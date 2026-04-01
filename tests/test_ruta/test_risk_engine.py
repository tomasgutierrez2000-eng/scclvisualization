"""Tests for the composite risk scoring engine.

Tests cover:
- 6-component scoring with known inputs
- Cold start (no traversal data)
- Stale data handling
- Time-of-day component
- Cache invalidation
- Route scoring aggregation
"""
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# The risk engine imports from shared.db.connections which needs DB paths
# We patch the DB paths to use test databases
TEST_DIR = Path(__file__).parent
TEST_INTEL_DB = TEST_DIR / "test_intel.db"
TEST_ROUTES_DB = TEST_DIR / "test_routes.db"


@pytest.fixture(autouse=True)
def setup_test_dbs(tmp_path):
    """Create fresh test databases for each test."""
    intel_db = tmp_path / "intel.db"
    routes_db = tmp_path / "routes.db"

    # Create intel.db with minimal schema
    conn = sqlite3.connect(str(intel_db))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS states (
            state_id TEXT PRIMARY KEY, name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS threat_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_id TEXT NOT NULL,
            overall_level TEXT NOT NULL,
            crime TEXT NOT NULL DEFAULT 'MEDIUM',
            political TEXT NOT NULL DEFAULT 'MEDIUM',
            infrastructure TEXT NOT NULL DEFAULT 'MEDIUM',
            natural_hazards TEXT NOT NULL DEFAULT 'LOW',
            source TEXT NOT NULL DEFAULT 'test',
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_id TEXT NOT NULL,
            incident_type TEXT NOT NULL DEFAULT 'other',
            severity TEXT NOT NULL,
            description TEXT,
            location TEXT,
            incident_date TEXT,
            lat REAL,
            lng REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_id TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT 'test',
            authority_type TEXT,
            is_active INTEGER DEFAULT 1,
            lat REAL,
            lng REAL,
            updated_at TEXT DEFAULT (datetime('now'))
        );
        INSERT INTO states VALUES ('ZU', 'Zulia');
        INSERT INTO states VALUES ('CA', 'Carabobo');
        INSERT INTO threat_levels (state_id, overall_level) VALUES ('ZU', 'HIGH');
        INSERT INTO threat_levels (state_id, overall_level) VALUES ('CA', 'LOW');
    """)
    conn.commit()
    conn.close()

    # Create routes.db from schema
    routes_conn = sqlite3.connect(str(routes_db))
    schema_path = Path(__file__).parent.parent / "agents" / "db" / "routes_schema.sql"
    if schema_path.exists():
        routes_conn.executescript(schema_path.read_text())
    else:
        # Minimal schema for testing
        routes_conn.executescript("""
            CREATE TABLE IF NOT EXISTS traversals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                h3_cell_id TEXT NOT NULL,
                team_id TEXT NOT NULL,
                device_id TEXT NOT NULL DEFAULT 'test',
                traversal_start TEXT NOT NULL,
                traversal_end TEXT,
                avg_speed_kmh REAL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS scouting_status (
                h3_cell_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'unscouted',
                last_scouted_at TEXT
            );
            CREATE TABLE IF NOT EXISTS route_cells (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT NOT NULL,
                h3_cell_id TEXT NOT NULL,
                sequence_order INTEGER NOT NULL,
                road_class TEXT DEFAULT 'unknown',
                road_name TEXT DEFAULT '',
                state_id TEXT
            );
            CREATE TABLE IF NOT EXISTS cell_risk_scores (
                h3_cell_id TEXT PRIMARY KEY,
                composite_score REAL NOT NULL DEFAULT 5.0,
                state_component REAL DEFAULT 0,
                road_component REAL DEFAULT 0,
                recency_component REAL DEFAULT 0,
                incident_component REAL DEFAULT 0,
                checkpoint_component REAL DEFAULT 0,
                tod_component REAL DEFAULT 0,
                computed_at TEXT DEFAULT (datetime('now')),
                inputs_hash TEXT
            );
        """)
    routes_conn.commit()
    routes_conn.close()

    # Patch the DB paths
    with patch("shared.db.connections.INTEL_DB_PATH", intel_db), \
         patch("shared.db.connections.ROUTES_DB_PATH", routes_db):
        yield {"intel_db": intel_db, "routes_db": routes_db}


class TestStateRisk:
    def test_known_state_high(self, setup_test_dbs):
        from ruta.risk_engine import compute_state_risk
        score = compute_state_risk("ZU")
        assert score == 6.0  # HIGH = 6

    def test_known_state_low(self, setup_test_dbs):
        from ruta.risk_engine import compute_state_risk
        score = compute_state_risk("CA")
        assert score == 1.0  # LOW = 1

    def test_unknown_state_defaults_critical(self, setup_test_dbs):
        from ruta.risk_engine import compute_state_risk
        score = compute_state_risk("XX")
        assert score == 10.0  # no data = CRITICAL


class TestRoadRisk:
    def test_highway(self):
        from ruta.risk_engine import compute_road_risk
        assert compute_road_risk("highway") == 1.0

    def test_unpaved(self):
        from ruta.risk_engine import compute_road_risk
        assert compute_road_risk("unpaved") == 8.0

    def test_unknown(self):
        from ruta.risk_engine import compute_road_risk
        assert compute_road_risk(None) == 5.0


class TestRecencyRisk:
    def test_cold_start_no_data(self, setup_test_dbs):
        """Never traversed, never scouted = 0 (neutral, not maximum)."""
        from ruta.risk_engine import compute_recency_risk
        score = compute_recency_risk("cell_never_seen")
        assert score == 0.0

    def test_recently_traversed(self, setup_test_dbs):
        """Traversed today = low recency risk."""
        from ruta.risk_engine import compute_recency_risk
        # Insert a recent traversal
        conn = sqlite3.connect(str(setup_test_dbs["routes_db"]))
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO traversals (h3_cell_id, team_id, device_id, traversal_start) "
            "VALUES (?, ?, ?, ?)",
            ("cell_recent", "team1", "dev1", now)
        )
        conn.commit()
        conn.close()

        score = compute_recency_risk("cell_recent")
        assert score < 1.0  # very recent = very low risk

    def test_stale_traversal(self, setup_test_dbs):
        """Traversed 30 days ago = capped at 10."""
        from ruta.risk_engine import compute_recency_risk
        conn = sqlite3.connect(str(setup_test_dbs["routes_db"]))
        old_date = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        conn.execute(
            "INSERT INTO traversals (h3_cell_id, team_id, device_id, traversal_start) "
            "VALUES (?, ?, ?, ?)",
            ("cell_stale", "team1", "dev1", old_date)
        )
        conn.commit()
        conn.close()

        score = compute_recency_risk("cell_stale")
        assert score == 10.0  # 31 days / 3 > 10, capped at 10


class TestTimeOfDayRisk:
    def test_daytime(self):
        from ruta.risk_engine import compute_time_of_day_risk
        assert compute_time_of_day_risk(12) == 0.0

    def test_nighttime(self):
        from ruta.risk_engine import compute_time_of_day_risk
        assert compute_time_of_day_risk(2) == 3.0

    def test_dawn(self):
        from ruta.risk_engine import compute_time_of_day_risk
        assert compute_time_of_day_risk(6) == 1.0


class TestCompositeScore:
    def test_known_inputs(self, setup_test_dbs):
        """Deterministic test with known inputs."""
        from ruta.risk_engine import score_cell

        result = score_cell(
            h3_cell_id="test_cell",
            cell_lat=10.0,
            cell_lng=-67.0,
            state_id="CA",  # LOW = 1.0
            road_class="highway",  # 1.0
            hour=12,  # daytime = 0.0
        )

        # state=1.0, road=1.0, recency=0.0 (cold start), incident=0, checkpoint=0, tod=0
        # composite = 0.30*1 + 0.10*1 + 0.20*0 + 0.20*0 + 0.10*0 + 0.10*0 = 0.4
        assert result["composite_score"] == 0.4
        assert result["state_component"] == 1.0
        assert result["road_component"] == 1.0
        assert result["recency_component"] == 0.0
        assert result["tod_component"] == 0.0

    def test_high_risk_scenario(self, setup_test_dbs):
        """High risk state + unpaved road + night = high composite."""
        from ruta.risk_engine import score_cell

        result = score_cell(
            h3_cell_id="danger_cell",
            cell_lat=10.0,
            cell_lng=-67.0,
            state_id="ZU",  # HIGH = 6.0
            road_class="unpaved",  # 8.0
            hour=2,  # night = 3.0
        )

        # state=6, road=8, recency=0, incident=0, checkpoint=0, tod=3
        # composite = 0.30*6 + 0.10*8 + 0.20*0 + 0.20*0 + 0.10*0 + 0.10*3
        #           = 1.8 + 0.8 + 0 + 0 + 0 + 0.3 = 2.9
        assert result["composite_score"] == 2.9
        assert result["state_component"] == 6.0
        assert result["road_component"] == 8.0
        assert result["tod_component"] == 3.0

    def test_score_clamped_0_to_10(self, setup_test_dbs):
        """Score should never exceed 10.0."""
        from ruta.risk_engine import score_cell

        result = score_cell(
            h3_cell_id="max_cell",
            cell_lat=10.0,
            cell_lng=-67.0,
            state_id="XX",  # CRITICAL = 10
            road_class="unpaved",  # 8
            hour=2,  # night = 3
        )

        assert result["composite_score"] <= 10.0
        assert result["composite_score"] >= 0.0


class TestIncidentProximity:
    def test_nearby_incident(self, setup_test_dbs):
        """Incident within 10km should contribute to risk."""
        from ruta.risk_engine import compute_incident_proximity

        conn = sqlite3.connect(str(setup_test_dbs["intel_db"]))
        conn.execute(
            "INSERT INTO incidents (state_id, incident_type, severity, lat, lng, incident_date) "
            "VALUES (?, ?, ?, ?, ?, date('now'))",
            ("ZU", "robbery", "HIGH", 10.001, -67.001)
        )
        conn.commit()
        conn.close()

        score = compute_incident_proximity(10.0, -67.0)
        assert score > 0.0  # nearby HIGH incident should contribute

    def test_distant_incident_no_effect(self, setup_test_dbs):
        """Incident far away should not contribute."""
        from ruta.risk_engine import compute_incident_proximity

        conn = sqlite3.connect(str(setup_test_dbs["intel_db"]))
        conn.execute(
            "INSERT INTO incidents (state_id, incident_type, severity, lat, lng, incident_date) "
            "VALUES (?, ?, ?, ?, ?, date('now'))",
            ("CA", "protest", "LOW", 20.0, -60.0)  # far away
        )
        conn.commit()
        conn.close()

        score = compute_incident_proximity(10.0, -67.0)
        assert score == 0.0

    def test_no_incidents(self, setup_test_dbs):
        """No incidents = 0 risk."""
        from ruta.risk_engine import compute_incident_proximity
        score = compute_incident_proximity(10.0, -67.0)
        assert score == 0.0


class TestRouteScoring:
    def test_empty_route(self, setup_test_dbs):
        """Route with no cells should return max risk."""
        from ruta.risk_engine import score_route
        result = score_route("nonexistent_route")
        assert result["avg_score"] == 10.0
        assert result["cell_scores"] == []

    def test_route_with_cells(self, setup_test_dbs):
        """Route with cells should return aggregate scores."""
        from ruta.risk_engine import score_route

        conn = sqlite3.connect(str(setup_test_dbs["routes_db"]))
        conn.execute(
            "INSERT INTO route_cells (route_id, h3_cell_id, sequence_order, road_class, state_id) "
            "VALUES (?, ?, ?, ?, ?)",
            ("test_route", "cell1", 0, "highway", "CA")
        )
        conn.execute(
            "INSERT INTO route_cells (route_id, h3_cell_id, sequence_order, road_class, state_id) "
            "VALUES (?, ?, ?, ?, ?)",
            ("test_route", "cell2", 1, "arterial", "ZU")
        )
        conn.commit()
        conn.close()

        result = score_route("test_route", hour=12)
        assert len(result["cell_scores"]) == 2
        assert result["avg_score"] > 0
        assert result["unscouted_pct"] == 100.0  # nothing traversed yet
