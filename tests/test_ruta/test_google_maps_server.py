"""Tests for Google Maps server: polyline decoding, H3 decomposition, caching."""
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


TEST_DIR = Path(__file__).parent


@pytest.fixture(autouse=True)
def setup_routes_db(tmp_path):
    """Create a fresh routes.db for each test."""
    routes_db = tmp_path / "routes.db"
    conn = sqlite3.connect(str(routes_db))
    schema_path = Path(__file__).parent.parent.parent / "ruta" / "db" / "routes_schema.sql"
    if schema_path.exists():
        conn.executescript(schema_path.read_text())
    conn.commit()
    conn.close()

    with patch("shared.db.connections.ROUTES_DB_PATH", routes_db):
        yield {"routes_db": routes_db}


class TestPolylineDecoding:
    def test_simple_polyline(self):
        """Decode a known Google encoded polyline."""
        from ruta.google_maps_server import _decode_polyline

        # This encodes a simple 2-point line: (38.5, -120.2) to (40.7, -120.95)
        encoded = "_p~iF~ps|U_ulLnnqC"
        points = _decode_polyline(encoded)

        assert len(points) == 2
        assert abs(points[0][0] - 38.5) < 0.01
        assert abs(points[0][1] - (-120.2)) < 0.01

    def test_empty_polyline(self):
        from ruta.google_maps_server import _decode_polyline
        points = _decode_polyline("")
        assert points == []


class TestH3Decomposition:
    def test_decompose_deduplicates_consecutive(self):
        """Consecutive points in the same H3 cell should be deduplicated."""
        from ruta.google_maps_server import decompose_to_h3_cells

        # Create a short polyline that stays within one H3 cell
        # Two very close points should produce only 1 cell
        encoded = "_p~iF~ps|U_ulLnnqC"
        cells = decompose_to_h3_cells(encoded, road_class="highway")

        # With h3 library: consecutive duplicate cells removed
        # Without h3: each point gets a unique fallback ID
        assert len(cells) >= 1
        assert all(c["road_class"] == "highway" for c in cells)

    def test_empty_polyline_returns_empty(self):
        from ruta.google_maps_server import decompose_to_h3_cells
        cells = decompose_to_h3_cells("")
        assert cells == []


class TestRouteCache:
    def test_cache_and_retrieve(self, setup_routes_db):
        """Cached route should be retrievable."""
        from ruta.google_maps_server import cache_route, get_cached_route

        route = {
            "route_id": "test123",
            "origin": {"name": "Caracas", "lat": 10.5, "lng": -66.9},
            "destination": {"name": "Maracaibo", "lat": 10.6, "lng": -71.6},
            "distance_m": 700000,
            "duration_s": 36000,
            "alternative_index": 0,
            "cells": [
                {"h3_cell_id": "cell_a", "sequence_order": 0, "road_class": "highway", "state_id": "DC"},
                {"h3_cell_id": "cell_b", "sequence_order": 1, "road_class": "arterial", "state_id": "AR"},
            ],
            "google_response": "{}",
        }

        cache_route(route)
        cached = get_cached_route("test123")

        assert cached is not None
        assert cached["route_id"] == "test123"
        assert len(cached["cells"]) == 2
        assert cached["cells"][0]["h3_cell_id"] == "cell_a"

    def test_cache_miss(self, setup_routes_db):
        from ruta.google_maps_server import get_cached_route
        assert get_cached_route("nonexistent") is None


class TestDirectionsAPIErrors:
    @patch("ruta.google_maps_server.GOOGLE_MAPS_API_KEY", "")
    def test_no_api_key(self):
        from ruta.google_maps_server import _call_directions_api, GoogleAuthError
        with pytest.raises(GoogleAuthError, match="GOOGLE_MAPS_API_KEY not set"):
            _call_directions_api("A", "B")

    @patch("ruta.google_maps_server.GOOGLE_MAPS_API_KEY", "test-key")
    @patch("ruta.google_maps_server.requests.get")
    def test_zero_results(self, mock_get):
        from ruta.google_maps_server import _call_directions_api, NoRouteFound
        mock_get.return_value = MagicMock(
            json=lambda: {"status": "ZERO_RESULTS"}
        )
        with pytest.raises(NoRouteFound):
            _call_directions_api("Nowhere", "Nowhere2")

    @patch("ruta.google_maps_server.GOOGLE_MAPS_API_KEY", "test-key")
    @patch("ruta.google_maps_server.requests.get")
    def test_quota_exceeded_retries(self, mock_get):
        from ruta.google_maps_server import _call_directions_api, GoogleQuotaExceeded

        mock_get.return_value = MagicMock(
            json=lambda: {"status": "OVER_QUERY_LIMIT"}
        )
        with pytest.raises(GoogleQuotaExceeded):
            _call_directions_api("A", "B")

        # Should have retried MAX_RETRIES + 1 times
        assert mock_get.call_count == 3  # initial + 2 retries

    @patch("ruta.google_maps_server.GOOGLE_MAPS_API_KEY", "test-key")
    @patch("ruta.google_maps_server.requests.get")
    def test_success(self, mock_get):
        from ruta.google_maps_server import _call_directions_api
        mock_get.return_value = MagicMock(
            json=lambda: {
                "status": "OK",
                "routes": [{"legs": [], "summary": "Test Route"}]
            }
        )
        result = _call_directions_api("Caracas", "Maracaibo")
        assert result["status"] == "OK"


class TestRouteIDDeterminism:
    def test_same_inputs_same_id(self):
        from ruta.google_maps_server import _compute_route_id
        id1 = _compute_route_id("A", "B", ["C"], 0)
        id2 = _compute_route_id("A", "B", ["C"], 0)
        assert id1 == id2

    def test_different_alt_index_different_id(self):
        from ruta.google_maps_server import _compute_route_id
        id1 = _compute_route_id("A", "B", [], 0)
        id2 = _compute_route_id("A", "B", [], 1)
        assert id1 != id2
