"""Google Maps integration for road-level routing.

Calls Google Directions API for real road routes, decomposes polylines
into H3 hex grid cells, and caches results.

Fallback: if Google API is unavailable, delegates to geo_server.py
(state-level Dijkstra routing).

Architecture:
    ┌────────────────────────────┐
    │   google_maps_server.py    │
    │                            │
    │   get_road_route() ────────┼──► Google Directions API
    │   decompose_to_h3() ───────┼──► polyline → H3 cells
    │   snap_to_roads()  ────────┼──► Google Roads API (batch)
    │   cache_route()    ────────┼──► routes.db
    └────────────────────────────┘
"""
import hashlib
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from shared.db.connections import get_routes_db

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
ROADS_URL = "https://roads.googleapis.com/v1/snapToRoads"

CACHE_DURATION_HOURS = 24
MAX_RETRIES = 2
RETRY_DELAY_S = 1.0

# H3 resolution 8: ~460m edge length
H3_RESOLUTION = 8


class GoogleAPIError(Exception):
    """Base class for Google API errors."""
    pass


class GoogleAPITimeout(GoogleAPIError):
    pass


class GoogleQuotaExceeded(GoogleAPIError):
    pass


class GoogleAuthError(GoogleAPIError):
    pass


class NoRouteFound(GoogleAPIError):
    pass


class GeocodingFailed(GoogleAPIError):
    pass


def _compute_route_id(
    origin: str, destination: str, waypoints: list[str], alt_index: int
) -> str:
    """Deterministic route ID from origin+destination+waypoints+alt_index."""
    data = f"{origin}|{destination}|{'|'.join(waypoints)}|{alt_index}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def _call_directions_api(
    origin: str,
    destination: str,
    waypoints: Optional[list[str]] = None,
    alternatives: bool = True,
    avoid: Optional[list[str]] = None,
) -> dict:
    """Call Google Directions API with retry logic.

    Returns the raw API response as a dict.
    Raises GoogleAPIError subclasses on failure.
    """
    if not GOOGLE_MAPS_API_KEY:
        raise GoogleAuthError("GOOGLE_MAPS_API_KEY not set")

    params = {
        "origin": origin,
        "destination": destination,
        "alternatives": str(alternatives).lower(),
        "key": GOOGLE_MAPS_API_KEY,
    }

    if waypoints:
        params["waypoints"] = "|".join(waypoints)
    if avoid:
        params["avoid"] = "|".join(avoid)

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(DIRECTIONS_URL, params=params, timeout=10)
        except requests.Timeout:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S * (2 ** attempt))
                continue
            raise GoogleAPITimeout("Google Directions API timed out after retries")
        except requests.RequestException as e:
            raise GoogleAPIError(f"Network error: {e}")

        data = resp.json()
        status = data.get("status", "UNKNOWN")

        if status == "OK":
            return data
        elif status == "OVER_QUERY_LIMIT":
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S * (2 ** attempt))
                continue
            raise GoogleQuotaExceeded("Google API quota exceeded")
        elif status == "REQUEST_DENIED":
            raise GoogleAuthError(f"Google API request denied: {data.get('error_message', '')}")
        elif status == "ZERO_RESULTS":
            raise NoRouteFound(f"No route from {origin} to {destination}")
        elif status == "NOT_FOUND":
            raise GeocodingFailed(f"Could not geocode: {origin} or {destination}")
        else:
            raise GoogleAPIError(f"Unexpected API status: {status}")

    raise GoogleAPIError("Max retries exceeded")


def _decode_polyline(encoded: str) -> list[tuple[float, float]]:
    """Decode a Google encoded polyline into list of (lat, lng) tuples.

    Handles malformed/truncated input gracefully by returning decoded
    points up to the point of corruption.
    """
    points = []
    index = 0
    lat = 0
    lng = 0
    length = len(encoded)

    try:
        while index < length:
            # Decode latitude
            result = 0
            shift = 0
            while index < length:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            else:
                break  # truncated mid-character, return what we have
            lat += (~(result >> 1) if result & 1 else result >> 1)

            # Decode longitude
            result = 0
            shift = 0
            while index < length:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            else:
                break  # truncated mid-character, return what we have
            lng += (~(result >> 1) if result & 1 else result >> 1)

            points.append((lat / 1e5, lng / 1e5))
    except (IndexError, ValueError):
        pass  # return points decoded so far

    return points


def decompose_to_h3_cells(
    encoded_polyline: str,
    state_id: Optional[str] = None,
    road_class: str = "unknown",
    road_name: str = "",
) -> list[dict]:
    """Decompose a Google encoded polyline into H3 hex grid cells.

    Returns list of dicts with h3_cell_id, lat, lng, road_class, state_id.
    Deduplicates consecutive identical cells.

    Requires h3 library. Falls back to simple lat/lng list if h3 not available.
    """
    points = _decode_polyline(encoded_polyline)
    if not points:
        return []

    try:
        import h3
    except ImportError:
        # h3 not installed: return points without H3 cell IDs
        # This allows the rest of the system to work without the h3 dependency
        return [
            {
                "h3_cell_id": f"noh3_{i}",
                "lat": p[0],
                "lng": p[1],
                "road_class": road_class,
                "road_name": road_name,
                "state_id": state_id,
            }
            for i, p in enumerate(points)
        ]

    cells = []
    prev_cell_id = None
    for lat, lng in points:
        cell_id = h3.latlng_to_cell(lat, lng, H3_RESOLUTION)
        if cell_id != prev_cell_id:
            cell_center = h3.cell_to_latlng(cell_id)
            cells.append({
                "h3_cell_id": cell_id,
                "lat": cell_center[0],
                "lng": cell_center[1],
                "road_class": road_class,
                "road_name": road_name,
                "state_id": state_id,
            })
            prev_cell_id = cell_id

    return cells


def get_road_route(
    origin: str,
    destination: str,
    waypoints: Optional[list[str]] = None,
    alternatives: bool = True,
) -> list[dict]:
    """Get road-level routes with H3 cell decomposition.

    Returns list of route dicts, each with:
        route_id, distance_m, duration_s, cells[], summary

    On Google API failure, raises exception (caller should fall back to Dijkstra).
    """
    data = _call_directions_api(origin, destination, waypoints, alternatives)
    routes = []

    for i, route in enumerate(data.get("routes", [])):
        route_id = _compute_route_id(origin, destination, waypoints or [], i)

        # Extract route-level info
        legs = route.get("legs", [])
        total_distance = sum(leg["distance"]["value"] for leg in legs)
        total_duration = sum(leg["duration"]["value"] for leg in legs)

        # Decompose each step's polyline into H3 cells
        all_cells = []
        for leg in legs:
            for step in leg.get("steps", []):
                polyline = step.get("polyline", {}).get("points", "")
                if polyline:
                    step_cells = decompose_to_h3_cells(
                        polyline,
                        road_name=step.get("html_instructions", ""),
                    )
                    all_cells.extend(step_cells)

        # Deduplicate consecutive cells at the route level
        deduped_cells = []
        prev_id = None
        for cell in all_cells:
            if cell["h3_cell_id"] != prev_id:
                cell["sequence_order"] = len(deduped_cells)
                deduped_cells.append(cell)
                prev_id = cell["h3_cell_id"]

        routes.append({
            "route_id": route_id,
            "alternative_index": i,
            "distance_m": total_distance,
            "duration_s": total_duration,
            "summary": route.get("summary", ""),
            "cells": deduped_cells,
            "origin": {
                "name": origin,
                "lat": legs[0]["start_location"]["lat"] if legs else 0,
                "lng": legs[0]["start_location"]["lng"] if legs else 0,
            },
            "destination": {
                "name": destination,
                "lat": legs[-1]["end_location"]["lat"] if legs else 0,
                "lng": legs[-1]["end_location"]["lng"] if legs else 0,
            },
            "google_response": json.dumps(route),
        })

    return routes


def cache_route(route: dict) -> None:
    """Store a route and its H3 cells in routes.db."""
    conn = get_routes_db()
    try:
        expires = (datetime.now(timezone.utc) + timedelta(hours=CACHE_DURATION_HOURS)).isoformat()

        conn.execute(
            """INSERT OR REPLACE INTO routes
               (route_id, origin_name, origin_lat, origin_lng,
                destination_name, destination_lat, destination_lng,
                waypoints_json, total_distance_m, total_duration_s,
                google_response_json, alternative_index, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                route["route_id"],
                route["origin"]["name"],
                route["origin"]["lat"],
                route["origin"]["lng"],
                route["destination"]["name"],
                route["destination"]["lat"],
                route["destination"]["lng"],
                json.dumps(route.get("waypoints", [])),
                route["distance_m"],
                route["duration_s"],
                route.get("google_response", ""),
                route["alternative_index"],
                expires,
            ),
        )

        # Insert H3 cells
        for cell in route.get("cells", []):
            conn.execute(
                """INSERT OR IGNORE INTO route_cells
                   (route_id, h3_cell_id, sequence_order,
                    road_name, road_class, state_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    route["route_id"],
                    cell["h3_cell_id"],
                    cell.get("sequence_order", 0),
                    cell.get("road_name", ""),
                    cell.get("road_class", "unknown"),
                    cell.get("state_id"),
                ),
            )

        conn.commit()
    finally:
        conn.close()


def get_cached_route(route_id: str) -> Optional[dict]:
    """Retrieve a cached route if it exists and hasn't expired."""
    conn = get_routes_db()
    try:
        row = conn.execute(
            "SELECT * FROM routes WHERE route_id = ? AND expires_at > datetime('now')",
            (route_id,),
        ).fetchone()

        if row is None:
            return None

        cells = conn.execute(
            "SELECT * FROM route_cells WHERE route_id = ? ORDER BY sequence_order",
            (route_id,),
        ).fetchall()

        return {
            "route_id": row["route_id"],
            "origin": {
                "name": row["origin_name"],
                "lat": row["origin_lat"],
                "lng": row["origin_lng"],
            },
            "destination": {
                "name": row["destination_name"],
                "lat": row["destination_lat"],
                "lng": row["destination_lng"],
            },
            "distance_m": row["total_distance_m"],
            "duration_s": row["total_duration_s"],
            "alternative_index": row["alternative_index"],
            "cells": [
                {
                    "h3_cell_id": c["h3_cell_id"],
                    "sequence_order": c["sequence_order"],
                    "road_name": c["road_name"],
                    "road_class": c["road_class"],
                    "state_id": c["state_id"],
                }
                for c in cells
            ],
        }
    finally:
        conn.close()


def snap_gps_to_roads(
    breadcrumbs: list[dict],
) -> list[dict]:
    """Snap GPS breadcrumbs to nearest roads using Google Roads API.

    Input: list of {"lat": float, "lng": float} dicts
    Output: list of {"lat": float, "lng": float, "placeId": str} snapped points

    Batches in groups of 100 (API limit).
    """
    if not GOOGLE_MAPS_API_KEY:
        raise GoogleAuthError("GOOGLE_MAPS_API_KEY not set")

    snapped = []
    batch_size = 100

    for i in range(0, len(breadcrumbs), batch_size):
        batch = breadcrumbs[i:i + batch_size]
        path = "|".join(f"{b['lat']},{b['lng']}" for b in batch)

        try:
            resp = requests.get(
                ROADS_URL,
                params={"path": path, "key": GOOGLE_MAPS_API_KEY, "interpolate": "false"},
                timeout=10,
            )
            data = resp.json()

            for point in data.get("snappedPoints", []):
                loc = point["location"]
                snapped.append({
                    "lat": loc["latitude"],
                    "lng": loc["longitude"],
                    "placeId": point.get("placeId", ""),
                    "originalIndex": point.get("originalIndex"),
                })

        except requests.Timeout:
            raise GoogleAPITimeout("Google Roads API timed out")
        except requests.RequestException as e:
            raise GoogleAPIError(f"Roads API error: {e}")

    return snapped
