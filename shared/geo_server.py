"""Geo MCP Server: routing, distances, and geographic data for Venezuelan states.

Uses a state adjacency graph with Dijkstra's algorithm for route finding.
Cities are geocoded to their state. Routes are state-level (not road-level).

Architecture:
                    ┌──────────────────┐
                    │   Route Planner   │
                    │     (Agent)       │
                    └────────┬─────────┘
                             │ tool calls
                    ┌────────▼─────────┐
                    │  Geo MCP Server   │
                    │                   │
                    │  calculate_route  │──► Dijkstra on adjacency graph
                    │  geocode_location │──► city_to_state lookup
                    │  get_road_conds   │──► DB query
                    │  estimate_time    │──► distance / avg_speed
                    │  get_border_cross │──► adjacency lookup
                    └──────────────────┘
"""
import heapq
import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = Path(__file__).parent / "db" / "intel.db"

# Load static data at module level
_state_data = json.loads((DATA_DIR / "venezuela_states.json").read_text())
_adjacency: dict[str, dict[str, float]] = _state_data["adjacency"]
_city_to_state: dict[str, str] = _state_data["city_to_state"]
_states: dict[str, dict] = {s["state_id"]: s for s in _state_data["states"]}

# Average speed assumptions (km/h) by road quality
AVG_SPEEDS = {"good": 70, "fair": 50, "poor": 30, "unknown": 40}


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def geocode_location(query: str) -> dict:
    """Resolve a city/location name to its Venezuelan state.

    Args:
        query: City or location name (case-insensitive)

    Returns:
        {"state_id": "ZU", "state_name": "Zulia", "capital": "Maracaibo", "matched_query": "maracaibo"}
    """
    normalized = query.strip().lower()
    state_id = _city_to_state.get(normalized)

    if not state_id:
        # Try partial match
        for city, sid in _city_to_state.items():
            if normalized in city or city in normalized:
                state_id = sid
                break

    if not state_id:
        return {"error": f"Unknown location: {query}. Known cities: {', '.join(sorted(_city_to_state.keys())[:10])}..."}

    state = _states[state_id]
    return {
        "state_id": state_id,
        "state_name": state["name"],
        "capital": state["capital"],
        "matched_query": normalized,
    }


def _dijkstra(start: str, end: str, avoid: set[str] | None = None) -> tuple[list[str], float]:
    """Find shortest path between states using Dijkstra's algorithm.

    Args:
        start: Starting state ID
        end: Destination state ID
        avoid: Set of state IDs to exclude from routing

    Returns:
        (path as list of state_ids, total_distance_km)
        Returns ([], 0) if no path exists.
    """
    avoid = avoid or set()

    if start in avoid or end in avoid:
        return [], 0

    # Priority queue: (distance, state_id)
    pq = [(0, start)]
    distances = {start: 0}
    previous = {}
    visited = set()

    while pq:
        current_dist, current = heapq.heappop(pq)

        if current in visited:
            continue
        visited.add(current)

        if current == end:
            # Reconstruct path
            path = []
            node = end
            while node in previous:
                path.append(node)
                node = previous[node]
            path.append(start)
            path.reverse()
            return path, current_dist

        for neighbor, edge_dist in _adjacency.get(current, {}).items():
            if neighbor in avoid or neighbor in visited:
                continue
            new_dist = current_dist + edge_dist
            if new_dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_dist
                previous[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))

    return [], 0  # No path found


def calculate_route(
    origin: str,
    destination: str,
    waypoints: list[str] | None = None,
    avoid_states: list[str] | None = None,
) -> dict:
    """Calculate a route between two locations through Venezuelan states.

    Uses Dijkstra on the state adjacency graph. Cities are resolved to states.

    Args:
        origin: Origin city name
        destination: Destination city name
        waypoints: Optional intermediate stop cities
        avoid_states: State IDs to exclude from routing

    Returns:
        Route with segments, distances, and states traversed.
    """
    avoid = set(avoid_states or [])
    waypoints = waypoints or []

    # Geocode all locations
    points = [origin] + waypoints + [destination]
    resolved = []
    for point in points:
        geo = geocode_location(point)
        if "error" in geo:
            return {"error": geo["error"]}
        resolved.append(geo)

    # Build route through all points
    segments = []
    all_states = []
    total_distance = 0

    for i in range(len(resolved) - 1):
        from_state = resolved[i]["state_id"]
        to_state = resolved[i + 1]["state_id"]

        if from_state == to_state:
            # Same state, no inter-state routing needed
            segments.append({
                "from_location": resolved[i]["capital"],
                "to_location": resolved[i + 1]["capital"],
                "distance_km": 20,  # Intra-state estimate
                "estimated_hours": 0.5,
                "states_traversed": [from_state],
                "road_condition": "unknown",
                "known_issues": [],
            })
            if from_state not in all_states:
                all_states.append(from_state)
            total_distance += 20
            continue

        path, distance = _dijkstra(from_state, to_state, avoid)

        if not path:
            return {
                "error": f"No route from {resolved[i]['state_name']} to {resolved[i+1]['state_name']}"
                + (f" avoiding {avoid}" if avoid else ""),
            }

        # Build segment for this leg
        segments.append({
            "from_location": resolved[i]["capital"],
            "to_location": resolved[i + 1]["capital"],
            "distance_km": distance,
            "estimated_hours": round(distance / AVG_SPEEDS["unknown"], 1),
            "states_traversed": path,
            "road_condition": "unknown",
            "known_issues": [],
        })

        for state in path:
            if state not in all_states:
                all_states.append(state)
        total_distance += distance

    total_hours = sum(s["estimated_hours"] for s in segments)
    # Recommend days: ~8 hours driving per day, minimum 1 day
    total_days = max(1, round(total_hours / 8 + 0.5))

    return {
        "segments": segments,
        "total_distance_km": round(total_distance, 1),
        "total_estimated_hours": round(total_hours, 1),
        "total_days": total_days,
        "states_traversed": all_states,
    }


def get_road_conditions(states: list[str]) -> dict:
    """Get road conditions for a list of states.

    Args:
        states: List of state IDs

    Returns:
        Dict keyed by state_id with road condition info.
    """
    db = _get_db()
    result = {}
    try:
        for state_id in states:
            # Check for active checkpoints
            checkpoints = db.execute(
                "SELECT location, authority_type, estimated_delay_minutes FROM checkpoints WHERE state_id = ? AND is_active = 1",
                (state_id,),
            ).fetchall()

            result[state_id] = {
                "state_id": state_id,
                "road_quality": "unknown",  # Would come from a road DB in production
                "active_checkpoints": [dict(c) for c in checkpoints],
                "checkpoint_count": len(checkpoints),
            }
    finally:
        db.close()

    return result


def estimate_travel_time(origin: str, destination: str, vehicle_type: str = "armored_suv") -> dict:
    """Estimate travel time accounting for vehicle type and road quality.

    Args:
        origin: Origin city
        destination: Destination city
        vehicle_type: Vehicle type (affects speed estimates)

    Returns:
        Time estimate with breakdown.
    """
    route = calculate_route(origin, destination)
    if "error" in route:
        return route

    # Vehicle speed multipliers (armored vehicles are slower)
    speed_multiplier = {
        "standard_suv": 1.0,
        "reinforced_suv": 0.9,
        "armored_suv": 0.8,
        "armored_convoy": 0.6,
    }.get(vehicle_type, 0.8)

    base_hours = route["total_estimated_hours"]
    adjusted_hours = round(base_hours / speed_multiplier, 1)

    return {
        "origin": origin,
        "destination": destination,
        "vehicle_type": vehicle_type,
        "base_hours": base_hours,
        "adjusted_hours": adjusted_hours,
        "speed_multiplier": speed_multiplier,
        "distance_km": route["total_distance_km"],
        "states_traversed": route["states_traversed"],
    }


def get_state_border_crossings(state_a: str, state_b: str) -> dict:
    """Get information about crossing between two adjacent states.

    Args:
        state_a: First state ID
        state_b: Second state ID

    Returns:
        Border crossing info including distance and any known issues.
    """
    distance = _adjacency.get(state_a, {}).get(state_b)
    if distance is None:
        return {"error": f"{state_a} and {state_b} are not adjacent"}

    return {
        "from_state": state_a,
        "to_state": state_b,
        "distance_km": distance,
        "from_name": _states.get(state_a, {}).get("name", state_a),
        "to_name": _states.get(state_b, {}).get("name", state_b),
    }
