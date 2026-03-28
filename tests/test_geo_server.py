"""Tests for the Geo MCP Server: routing and geocoding."""
import pytest

from agents.servers.geo_server import calculate_route, geocode_location, estimate_travel_time, _dijkstra


def test_geocode_known_city():
    result = geocode_location("Caracas")
    assert result["state_id"] == "DC"
    assert result["state_name"] == "Distrito Capital"


def test_geocode_case_insensitive():
    result = geocode_location("MARACAIBO")
    assert result["state_id"] == "ZU"


def test_geocode_unknown_city():
    result = geocode_location("Atlantis")
    assert "error" in result


def test_geocode_partial_match():
    result = geocode_location("puerto la cruz")
    assert result["state_id"] == "AN"


def test_dijkstra_basic():
    path, dist = _dijkstra("DC", "ZU")
    assert len(path) > 2
    assert path[0] == "DC"
    assert path[-1] == "ZU"
    assert dist > 0


def test_dijkstra_same_state():
    path, dist = _dijkstra("DC", "DC")
    assert path == ["DC"]
    assert dist == 0


def test_dijkstra_with_avoid():
    path_normal, _ = _dijkstra("DC", "ZU")
    path_avoid, _ = _dijkstra("DC", "ZU", avoid={"TR"})
    # Avoiding TR should produce a different path
    assert "TR" not in path_avoid


def test_dijkstra_no_path():
    # NE (Nueva Esparta) is an island with no adjacency
    path, dist = _dijkstra("DC", "NE")
    assert path == []
    assert dist == 0


def test_calculate_route_basic():
    route = calculate_route("Caracas", "Maracaibo")
    assert "error" not in route
    assert route["total_distance_km"] > 0
    assert route["total_days"] >= 1
    assert "DC" in route["states_traversed"]
    assert "ZU" in route["states_traversed"]


def test_calculate_route_with_waypoint():
    route = calculate_route("Caracas", "Maracaibo", waypoints=["Valencia"])
    assert "error" not in route
    assert "CA" in route["states_traversed"]


def test_calculate_route_with_avoid():
    route = calculate_route("Caracas", "Maracaibo", avoid_states=["TR"])
    assert "error" not in route
    assert "TR" not in route["states_traversed"]


def test_calculate_route_unknown_city():
    route = calculate_route("Atlantis", "Maracaibo")
    assert "error" in route


def test_calculate_route_same_city():
    route = calculate_route("Caracas", "Caracas")
    assert "error" not in route
    assert route["total_days"] == 1


def test_estimate_travel_time_basic():
    result = estimate_travel_time("Caracas", "Valencia")
    assert "error" not in result
    assert result["adjusted_hours"] > 0


def test_estimate_travel_time_armored():
    standard = estimate_travel_time("Caracas", "Valencia", "standard_suv")
    armored = estimate_travel_time("Caracas", "Valencia", "armored_suv")
    # Armored should be slower
    assert armored["adjusted_hours"] > standard["adjusted_hours"]
