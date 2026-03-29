"""Composite risk scoring engine for H3 hex grid cells.

Scores each cell 0.0 (safest) to 10.0 (extreme danger) using 6 components:

    composite = (
        0.30 * state_risk           # from intel.db threat_levels
      + 0.10 * road_condition_risk  # road class + quality
      + 0.20 * recency_decay_risk   # days since last traversal/scout
      + 0.20 * incident_proximity   # nearby incidents (30d, 10km)
      + 0.10 * checkpoint_risk      # checkpoint proximity and type
      + 0.10 * time_of_day_risk     # night travel penalty
    )

Cold start: cells inherit state-level risk. Recency starts at 0 (neutral).
Cache invalidation: recompute on new incident, threat level change, or traversal.
"""
import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Optional

from agents.db.connections import get_intel_db, get_routes_db

# Component weights (must sum to 1.0)
WEIGHTS = {
    "state": 0.30,
    "road": 0.10,
    "recency": 0.20,
    "incident": 0.20,
    "checkpoint": 0.10,
    "tod": 0.10,
}

# Risk level to numeric mapping
RISK_LEVELS = {"LOW": 1, "MEDIUM": 3, "HIGH": 6, "CRITICAL": 10}

# Road class risk scores
ROAD_CLASS_RISK = {
    "highway": 1.0,
    "arterial": 3.0,
    "local": 5.0,
    "unpaved": 8.0,
    "unknown": 5.0,
}

# Checkpoint type risk (informal = unpredictable = higher risk)
CHECKPOINT_TYPE_RISK = {
    "military": 3.0,
    "police": 2.0,
    "national_guard": 4.0,
    "informal": 8.0,
}

# Incident proximity config
INCIDENT_RADIUS_KM = 10.0
INCIDENT_LOOKBACK_DAYS = 30
INCIDENT_SEVERITY = {"LOW": 1, "MEDIUM": 3, "HIGH": 6, "CRITICAL": 10}

# Recency config
RECENCY_CAP_DAYS = 30  # after 30 days, recency risk caps at 10


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def compute_state_risk(state_id: str) -> float:
    """State-level threat risk from intel.db. No data = CRITICAL."""
    conn = get_intel_db()
    try:
        row = conn.execute(
            "SELECT overall_level FROM threat_levels "
            "WHERE state_id = ? ORDER BY updated_at DESC LIMIT 1",
            (state_id,)
        ).fetchone()
        if row is None:
            return 10.0  # no data = CRITICAL (conservative)
        return float(RISK_LEVELS.get(row["overall_level"], 10))
    finally:
        conn.close()


def compute_road_risk(road_class: Optional[str]) -> float:
    """Road condition risk based on class."""
    return ROAD_CLASS_RISK.get(road_class or "unknown", 5.0)


def compute_recency_risk(h3_cell_id: str) -> float:
    """Risk based on how recently someone traversed or scouted this cell.

    Cold start: if never traversed, return 0.0 (neutral, not maximum).
    After first traversal: min(10, days_since / 3).
    """
    conn = get_routes_db()
    try:
        # Most recent traversal
        traversal = conn.execute(
            "SELECT MAX(traversal_start) as last_traversal FROM traversals "
            "WHERE h3_cell_id = ?",
            (h3_cell_id,)
        ).fetchone()

        # Most recent scout
        scout = conn.execute(
            "SELECT last_scouted_at FROM scouting_status WHERE h3_cell_id = ?",
            (h3_cell_id,)
        ).fetchone()

        last_traversal = traversal["last_traversal"] if traversal else None
        last_scout = scout["last_scouted_at"] if scout else None

        # Cold start: never traversed and never scouted
        if last_traversal is None and last_scout is None:
            return 0.0  # neutral, not maximum

        # Find most recent activity
        dates = [d for d in [last_traversal, last_scout] if d is not None]
        most_recent = max(dates)

        now = datetime.now(timezone.utc)
        try:
            last_dt = datetime.fromisoformat(most_recent.replace("Z", "+00:00"))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            return 5.0  # parse error, moderate default

        days_since = (now - last_dt).total_seconds() / 86400
        return min(10.0, days_since / 3.0)
    finally:
        conn.close()


def compute_incident_proximity(
    cell_lat: float, cell_lng: float, state_id: Optional[str] = None
) -> float:
    """Risk from nearby incidents in the last 30 days.

    For each incident within INCIDENT_RADIUS_KM:
        severity_weight * max(0, 1 - distance_km / INCIDENT_RADIUS_KM)
    Sum and cap at 10.
    """
    conn = get_intel_db()
    try:
        # Bounding box for rough filter (~0.09 degrees per km at equator)
        lat_delta = INCIDENT_RADIUS_KM / 111.0
        lng_delta = INCIDENT_RADIUS_KM / (111.0 * max(0.1, math.cos(math.radians(cell_lat))))

        query = """
            SELECT lat, lng, severity FROM incidents
            WHERE lat IS NOT NULL AND lng IS NOT NULL
            AND lat BETWEEN ? AND ?
            AND lng BETWEEN ? AND ?
            AND incident_date >= date('now', ?)
        """
        params = (
            cell_lat - lat_delta, cell_lat + lat_delta,
            cell_lng - lng_delta, cell_lng + lng_delta,
            f"-{INCIDENT_LOOKBACK_DAYS} days",
        )

        risk = 0.0
        for row in conn.execute(query, params):
            dist = _haversine_km(cell_lat, cell_lng, row["lat"], row["lng"])
            if dist <= INCIDENT_RADIUS_KM:
                weight = INCIDENT_SEVERITY.get(row["severity"], 3)
                proximity_factor = max(0.0, 1.0 - dist / INCIDENT_RADIUS_KM)
                risk += weight * proximity_factor

        return min(10.0, risk)
    finally:
        conn.close()


def compute_checkpoint_risk(
    cell_lat: float, cell_lng: float
) -> float:
    """Risk from nearby checkpoints. Informal checkpoints score highest."""
    conn = get_intel_db()
    try:
        radius_km = 5.0
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * max(0.1, math.cos(math.radians(cell_lat))))

        query = """
            SELECT lat, lng, authority_type FROM checkpoints
            WHERE lat IS NOT NULL AND lng IS NOT NULL
            AND is_active = 1
            AND lat BETWEEN ? AND ?
            AND lng BETWEEN ? AND ?
        """
        params = (
            cell_lat - lat_delta, cell_lat + lat_delta,
            cell_lng - lng_delta, cell_lng + lng_delta,
        )

        risk = 0.0
        for row in conn.execute(query, params):
            dist = _haversine_km(cell_lat, cell_lng, row["lat"], row["lng"])
            if dist <= radius_km:
                type_risk = CHECKPOINT_TYPE_RISK.get(row["authority_type"], 3.0)
                proximity = max(0.0, 1.0 - dist / radius_km)
                risk += type_risk * proximity

        return min(10.0, risk)
    finally:
        conn.close()


def compute_time_of_day_risk(hour: int) -> float:
    """Night travel penalty. 18:00-06:00 = +3, dawn/dusk = +1."""
    if 0 <= hour < 6 or 18 <= hour <= 23:
        return 3.0  # night
    elif hour in (6, 17):
        return 1.0  # dawn/dusk
    return 0.0  # daytime


def score_cell(
    h3_cell_id: str,
    cell_lat: float,
    cell_lng: float,
    state_id: Optional[str] = None,
    road_class: Optional[str] = None,
    hour: Optional[int] = None,
) -> dict:
    """Compute composite risk score for an H3 cell.

    Returns dict with composite_score and all component values.
    """
    if hour is None:
        hour = datetime.now(timezone.utc).hour

    state = compute_state_risk(state_id) if state_id else 5.0
    road = compute_road_risk(road_class)
    recency = compute_recency_risk(h3_cell_id)
    incident = compute_incident_proximity(cell_lat, cell_lng, state_id)
    checkpoint = compute_checkpoint_risk(cell_lat, cell_lng)
    tod = compute_time_of_day_risk(hour)

    composite = (
        WEIGHTS["state"] * state
        + WEIGHTS["road"] * road
        + WEIGHTS["recency"] * recency
        + WEIGHTS["incident"] * incident
        + WEIGHTS["checkpoint"] * checkpoint
        + WEIGHTS["tod"] * tod
    )

    # Clamp to 0-10
    composite = max(0.0, min(10.0, composite))

    return {
        "h3_cell_id": h3_cell_id,
        "composite_score": round(composite, 2),
        "state_component": round(state, 2),
        "road_component": round(road, 2),
        "recency_component": round(recency, 2),
        "incident_component": round(incident, 2),
        "checkpoint_component": round(checkpoint, 2),
        "tod_component": round(tod, 2),
    }


def _compute_inputs_hash(
    h3_cell_id: str, state_id: str, road_class: str, hour: int
) -> str:
    """Hash of inputs for cache invalidation."""
    data = f"{h3_cell_id}:{state_id}:{road_class}:{hour}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def score_and_cache_cell(
    h3_cell_id: str,
    cell_lat: float,
    cell_lng: float,
    state_id: Optional[str] = None,
    road_class: Optional[str] = None,
    hour: Optional[int] = None,
) -> dict:
    """Score a cell and write to cell_risk_scores cache."""
    result = score_cell(h3_cell_id, cell_lat, cell_lng, state_id, road_class, hour)

    conn = get_routes_db()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO cell_risk_scores
               (h3_cell_id, composite_score, state_component, road_component,
                recency_component, incident_component, checkpoint_component,
                tod_component, computed_at, inputs_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)""",
            (
                h3_cell_id,
                result["composite_score"],
                result["state_component"],
                result["road_component"],
                result["recency_component"],
                result["incident_component"],
                result["checkpoint_component"],
                result["tod_component"],
                _compute_inputs_hash(
                    h3_cell_id, state_id or "", road_class or "", hour or 12
                ),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return result


def score_route(route_id: str, hour: Optional[int] = None) -> dict:
    """Score all H3 cells along a route and return aggregate risk.

    Returns:
        {
            "route_id": str,
            "avg_score": float,
            "max_score": float,
            "cell_scores": [{"h3_cell_id": str, "composite_score": float, ...}],
            "critical_cells": int,   # cells with score >= 7.5
            "unscouted_pct": float,  # percentage never traversed/scouted
        }
    """
    conn = get_routes_db()
    try:
        cells = conn.execute(
            "SELECT h3_cell_id, road_class, state_id FROM route_cells "
            "WHERE route_id = ? ORDER BY sequence_order",
            (route_id,)
        ).fetchall()
    finally:
        conn.close()

    if not cells:
        return {
            "route_id": route_id,
            "avg_score": 10.0,
            "max_score": 10.0,
            "cell_scores": [],
            "critical_cells": 0,
            "unscouted_pct": 100.0,
        }

    # We need lat/lng for each cell. For now, use a placeholder.
    # In production, H3 cell center coordinates come from h3.cell_to_latlng().
    # This will be integrated when the h3 library is added.
    cell_scores = []
    for cell in cells:
        # TODO: get lat/lng from h3.cell_to_latlng(cell["h3_cell_id"])
        # For now, we skip proximity-based components for cells without coords
        result = score_cell(
            cell["h3_cell_id"],
            cell_lat=0.0,  # placeholder
            cell_lng=0.0,  # placeholder
            state_id=cell["state_id"],
            road_class=cell["road_class"],
            hour=hour,
        )
        cell_scores.append(result)

    scores = [c["composite_score"] for c in cell_scores]
    critical = sum(1 for s in scores if s >= 7.5)

    # Count unscouted cells
    conn = get_routes_db()
    try:
        h3_ids = [c["h3_cell_id"] for c in cells]
        placeholders = ",".join("?" * len(h3_ids))
        scouted = conn.execute(
            f"SELECT COUNT(*) as cnt FROM scouting_status "
            f"WHERE h3_cell_id IN ({placeholders}) AND status != 'unscouted'",
            h3_ids,
        ).fetchone()

        traversed = conn.execute(
            f"SELECT COUNT(DISTINCT h3_cell_id) as cnt FROM traversals "
            f"WHERE h3_cell_id IN ({placeholders})",
            h3_ids,
        ).fetchone()
    finally:
        conn.close()

    covered = max(scouted["cnt"], traversed["cnt"]) if scouted and traversed else 0
    unscouted_pct = ((len(cells) - covered) / len(cells)) * 100 if cells else 100.0

    return {
        "route_id": route_id,
        "avg_score": round(sum(scores) / len(scores), 2),
        "max_score": round(max(scores), 2),
        "cell_scores": cell_scores,
        "critical_cells": critical,
        "unscouted_pct": round(unscouted_pct, 1),
    }
