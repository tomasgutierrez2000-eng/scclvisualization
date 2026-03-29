"""Route Intelligence API (FastAPI).

Main entry point for the route intelligence service.
All DB-touching endpoints use sync `def` (not `async def`)
to avoid SQLite write-lock deadlocks. FastAPI runs them in
a threadpool automatically.

Run: uvicorn agents.servers.api:app --port 5060
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from agents.db.connections import get_routes_db, get_intel_db, init_routes_db
from agents.servers.risk_engine import score_cell, score_route, score_and_cache_cell

app = FastAPI(
    title="RUTA Route Intelligence API",
    version="0.1.0",
    description="Road-level routing, risk scoring, GPS tracking, and mission management for Venezuela.",
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    """Initialize routes.db on first run."""
    init_routes_db()


# ============================================================
# AUTH HELPERS
# ============================================================

def _verify_ops_token(authorization: str = Header(None)) -> str:
    """Verify JWT token for ops endpoints. Returns user_id."""
    if not authorization:
        raise HTTPException(401, "Authorization header required")
    # TODO: Implement JWT validation
    # For now, accept any bearer token for development
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    return "ops_user"


def _verify_device_token(authorization: str = Header(None)) -> str:
    """Verify device bearer token for GPS endpoints. Returns device_id."""
    if not authorization:
        raise HTTPException(401, "Authorization header required")
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")

    token = authorization.split(" ", 1)[1]
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    conn = get_routes_db()
    try:
        row = conn.execute(
            "SELECT device_id, is_active FROM device_tokens WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        if row is None:
            raise HTTPException(401, "Invalid device token")
        if not row["is_active"]:
            raise HTTPException(403, "Device token revoked")
        return row["device_id"]
    finally:
        conn.close()


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class RoutePlanRequest(BaseModel):
    origin: str
    destination: str
    waypoints: list[str] = Field(default_factory=list)
    departure_hour: Optional[int] = None
    alternatives: bool = True


class GPSBreadcrumb(BaseModel):
    lat: float
    lng: float
    altitude_m: Optional[float] = None
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None
    accuracy_m: Optional[float] = None
    device_timestamp: str  # ISO 8601


class MissionCreateRequest(BaseModel):
    client_id: str
    route_id: str
    departure_time: Optional[str] = None
    team_id: Optional[str] = None
    team_members: list[str] = Field(default_factory=list)
    vehicle_ids: list[str] = Field(default_factory=list)


# ============================================================
# ROUTE PLANNING ENDPOINTS
# ============================================================

@app.post("/route/plan")
def plan_route(req: RoutePlanRequest, user_id: str = Depends(_verify_ops_token)):
    """Plan a road-level route with alternatives and risk scores.

    Calls Google Directions API, decomposes into H3 cells, scores each cell.
    Falls back to Dijkstra state-level routing if Google API fails.
    """
    try:
        from agents.servers.google_maps_server import (
            get_road_route, cache_route,
            GoogleAPIError, GoogleAPITimeout, GoogleQuotaExceeded,
            GoogleAuthError, NoRouteFound, GeocodingFailed,
        )

        routes = get_road_route(
            req.origin, req.destination, req.waypoints, req.alternatives
        )

        results = []
        for route in routes:
            cache_route(route)
            risk = score_route(route["route_id"], hour=req.departure_hour)
            results.append({**route, "risk": risk})

        return {"routes": results, "source": "google_maps"}

    except GoogleAPIError as e:
        # Fallback to Dijkstra only for Google API failures, not programming errors
        from agents.servers.geo_server import calculate_route

        try:
            fallback = calculate_route(req.origin, req.destination)
            return {
                "routes": [fallback],
                "source": "dijkstra_fallback",
                "warning": f"Google Maps unavailable ({type(e).__name__}). Using state-level backup routing.",
            }
        except Exception as fallback_err:
            raise HTTPException(503, f"Routing unavailable: {e} (fallback also failed: {fallback_err})")


@app.get("/route/{route_id}")
def get_route(route_id: str, user_id: str = Depends(_verify_ops_token)):
    """Get route details with all H3 cells."""
    from agents.servers.google_maps_server import get_cached_route

    route = get_cached_route(route_id)
    if route is None:
        raise HTTPException(404, "Route not found or expired")

    risk = score_route(route_id)
    return {**route, "risk": risk}


@app.get("/cell/{h3_id}")
def get_cell(h3_id: str, hour: Optional[int] = None, user_id: str = Depends(_verify_ops_token)):
    """Get risk breakdown for a single H3 cell."""
    conn = get_routes_db()
    try:
        cell = conn.execute(
            "SELECT * FROM route_cells WHERE h3_cell_id = ? LIMIT 1",
            (h3_id,),
        ).fetchone()
    finally:
        conn.close()

    if cell is None:
        raise HTTPException(404, "Cell not found")

    result = score_cell(
        h3_id,
        cell_lat=0.0,  # TODO: h3.cell_to_latlng when h3 lib available
        cell_lng=0.0,
        state_id=cell["state_id"],
        road_class=cell["road_class"],
        hour=hour,
    )

    # Get traversal history
    conn = get_routes_db()
    try:
        traversals = conn.execute(
            "SELECT * FROM traversals WHERE h3_cell_id = ? "
            "ORDER BY traversal_start DESC LIMIT 10",
            (h3_id,),
        ).fetchall()
    finally:
        conn.close()

    return {
        "risk": result,
        "traversals": [dict(t) for t in traversals],
    }


# ============================================================
# GPS TRACKING ENDPOINTS
# ============================================================

# Spoofing defense constants
MAX_SPEED_KMH = 200.0
MAX_TELEPORT_SPEED_KMH = 300.0


@app.post("/track/ingest")
def ingest_breadcrumb(crumb: GPSBreadcrumb, device_id: str = Depends(_verify_device_token)):
    """Ingest a GPS breadcrumb from a field device.

    Validates, checks for spoofing, stores in breadcrumbs table.
    Batch processing (snap-to-road + H3 matching) runs separately.
    """
    # Speed check
    if crumb.speed_kmh is not None and crumb.speed_kmh > MAX_SPEED_KMH:
        _store_discarded_breadcrumb(device_id, crumb, "speed_check")
        return {"status": "discarded", "reason": "speed_check"}

    # Bounds check (Venezuela roughly: lat 1-12, lng -73 to -60)
    if not (1.0 <= crumb.lat <= 13.0 and -74.0 <= crumb.lng <= -59.0):
        _store_discarded_breadcrumb(device_id, crumb, "out_of_bounds")
        return {"status": "discarded", "reason": "out_of_bounds"}

    # Store breadcrumb
    conn = get_routes_db()
    try:
        conn.execute(
            """INSERT INTO gps_breadcrumbs
               (device_id, team_id, lat, lng, altitude_m, speed_kmh,
                heading, accuracy_m, device_timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                device_id,
                _get_team_for_device(device_id),
                crumb.lat, crumb.lng, crumb.altitude_m,
                crumb.speed_kmh, crumb.heading, crumb.accuracy_m,
                crumb.device_timestamp,
            ),
        )
        conn.commit()
    except Exception:
        # DB write failure: TODO implement file queue fallback
        raise HTTPException(500, "Failed to store breadcrumb")
    finally:
        conn.close()

    return {"status": "accepted"}


def _store_discarded_breadcrumb(device_id: str, crumb: GPSBreadcrumb, reason: str):
    """Store a discarded breadcrumb for audit."""
    conn = get_routes_db()
    try:
        conn.execute(
            """INSERT INTO gps_breadcrumbs
               (device_id, team_id, lat, lng, speed_kmh, device_timestamp,
                processed, discard_reason)
               VALUES (?, ?, ?, ?, ?, ?, 2, ?)""",
            (device_id, _get_team_for_device(device_id),
             crumb.lat, crumb.lng, crumb.speed_kmh,
             crumb.device_timestamp, reason),
        )
        conn.commit()
    finally:
        conn.close()


def _get_team_for_device(device_id: str) -> str:
    """Look up team_id for a device."""
    conn = get_routes_db()
    try:
        row = conn.execute(
            "SELECT team_id FROM device_tokens WHERE device_id = ?",
            (device_id,),
        ).fetchone()
        return row["team_id"] if row else "unknown"
    finally:
        conn.close()


@app.get("/track/live/{team_id}")
def get_live_position(team_id: str, user_id: str = Depends(_verify_ops_token)):
    """Get latest position and trail for a team."""
    conn = get_routes_db()
    try:
        # Latest position per device in team
        breadcrumbs = conn.execute(
            """SELECT device_id, lat, lng, speed_kmh, heading, device_timestamp
               FROM gps_breadcrumbs
               WHERE team_id = ? AND processed != 2
               ORDER BY device_timestamp DESC
               LIMIT 50""",
            (team_id,),
        ).fetchall()
    finally:
        conn.close()

    if not breadcrumbs:
        raise HTTPException(404, f"No GPS data for team {team_id}")

    return {
        "team_id": team_id,
        "latest": dict(breadcrumbs[0]),
        "trail": [dict(b) for b in breadcrumbs[:20]],
    }


# ============================================================
# MISSION ENDPOINTS
# ============================================================

@app.post("/mission/create")
def create_mission(req: MissionCreateRequest, user_id: str = Depends(_verify_ops_token)):
    """Create a new mission from a planned route."""
    import uuid

    mission_id = str(uuid.uuid4())[:12]

    conn = get_routes_db()
    try:
        conn.execute(
            """INSERT INTO missions
               (mission_id, client_id, route_id, status, departure_time,
                team_id, team_members_json, vehicle_ids_json)
               VALUES (?, ?, ?, 'planning', ?, ?, ?, ?)""",
            (
                mission_id, req.client_id, req.route_id,
                req.departure_time, req.team_id,
                json.dumps(req.team_members),
                json.dumps(req.vehicle_ids),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {"mission_id": mission_id, "status": "planning"}


@app.get("/mission/{mission_id}/status")
def get_mission_status(mission_id: str, user_id: str = Depends(_verify_ops_token)):
    """Get current mission status with live tracking data."""
    conn = get_routes_db()
    try:
        mission = conn.execute(
            "SELECT * FROM missions WHERE mission_id = ?",
            (mission_id,),
        ).fetchone()
    finally:
        conn.close()

    if mission is None:
        raise HTTPException(404, "Mission not found")

    result = dict(mission)

    # If active, include live position
    if mission["status"] == "active" and mission["team_id"]:
        try:
            live = get_live_position(mission["team_id"])
            result["live_position"] = live
        except HTTPException:
            result["live_position"] = None

    return result


# ============================================================
# SCOUTING ENDPOINTS
# ============================================================

@app.get("/scout/queue")
def get_scouting_queue(user_id: str = Depends(_verify_ops_token)):
    """Get prioritized scouting queue."""
    conn = get_routes_db()
    try:
        queue = conn.execute(
            """SELECT h3_cell_id, status, last_scouted_at, scout_priority,
                      assigned_to, assigned_at
               FROM scouting_status
               WHERE status IN ('unscouted', 'stale')
               ORDER BY scout_priority ASC, last_scouted_at ASC
               LIMIT 50""",
        ).fetchall()
    finally:
        conn.close()

    return {"queue": [dict(q) for q in queue]}


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@app.get("/admin/health")
def health_check():
    """System health dashboard data."""
    conn = get_routes_db()
    try:
        stats = {
            "active_missions": conn.execute(
                "SELECT COUNT(*) as c FROM missions WHERE status = 'active'"
            ).fetchone()["c"],
            "total_breadcrumbs": conn.execute(
                "SELECT COUNT(*) as c FROM gps_breadcrumbs"
            ).fetchone()["c"],
            "pending_breadcrumbs": conn.execute(
                "SELECT COUNT(*) as c FROM gps_breadcrumbs WHERE processed = 0"
            ).fetchone()["c"],
            "pending_events": conn.execute(
                "SELECT COUNT(*) as c FROM events WHERE processed_at IS NULL"
            ).fetchone()["c"],
            "scored_cells": conn.execute(
                "SELECT COUNT(*) as c FROM cell_risk_scores"
            ).fetchone()["c"],
        }
    finally:
        conn.close()

    return {"status": "healthy", "stats": stats, "timestamp": datetime.now(timezone.utc).isoformat()}
