"""Tests for database schema, seed, and WAL mode."""
import sqlite3
import tempfile
from pathlib import Path

import pytest

from agents.db.seed import main as seed_main, get_db, init_schema, seed_states, seed_initial_threat_levels


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    # Remove so seed can create fresh
    db_path.unlink()
    seed_main(db_path)
    yield db_path
    db_path.unlink(missing_ok=True)


def test_wal_mode(temp_db):
    conn = sqlite3.connect(str(temp_db))
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
    conn.close()


def test_states_count(temp_db):
    conn = get_db(temp_db)
    count = conn.execute("SELECT COUNT(*) FROM states").fetchone()[0]
    assert count == 24
    conn.close()


def test_threat_levels_seeded(temp_db):
    conn = get_db(temp_db)
    count = conn.execute("SELECT COUNT(*) FROM threat_levels").fetchone()[0]
    assert count == 24
    conn.close()


def test_adjacency_edges(temp_db):
    conn = get_db(temp_db)
    count = conn.execute("SELECT COUNT(*) FROM state_adjacency").fetchone()[0]
    assert count > 50  # Should have ~97 edges
    conn.close()


def test_no_go_zones_seeded(temp_db):
    conn = get_db(temp_db)
    count = conn.execute("SELECT COUNT(*) FROM no_go_zones").fetchone()[0]
    assert count >= 5
    conn.close()


def test_multi_tenant_schema(temp_db):
    """Verify client_id exists on per-client tables."""
    conn = get_db(temp_db)
    # active_trips should have client_id
    conn.execute("SELECT client_id FROM active_trips LIMIT 0")
    # client_preferences should have client_id
    conn.execute("SELECT client_id FROM client_preferences LIMIT 0")
    conn.close()


def test_api_key_created(temp_db):
    conn = get_db(temp_db)
    count = conn.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]
    assert count >= 1
    conn.close()


def test_foreign_keys_enforced(temp_db):
    conn = get_db(temp_db)
    conn.execute("PRAGMA foreign_keys=ON")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO threat_levels (state_id, overall_level, crime, political, infrastructure, natural_hazards, source) VALUES ('FAKE', 'LOW', 'LOW', 'LOW', 'LOW', 'LOW', 'test')"
        )
    conn.close()
