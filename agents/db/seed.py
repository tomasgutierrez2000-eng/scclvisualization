"""Seed the intelligence database with Venezuelan state data and initial threat levels."""
import hashlib
import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "intel.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DATA_DIR = Path(__file__).parent.parent / "data"


def get_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a database connection with WAL mode enabled."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables from schema.sql."""
    schema_sql = SCHEMA_PATH.read_text()
    conn.executescript(schema_sql)


def seed_states(conn: sqlite3.Connection) -> None:
    """Populate states and adjacency from venezuela_states.json."""
    data = json.loads((DATA_DIR / "venezuela_states.json").read_text())

    for state in data["states"]:
        conn.execute(
            "INSERT OR IGNORE INTO states (state_id, name, capital) VALUES (?, ?, ?)",
            (state["state_id"], state["name"], state["capital"]),
        )

    for from_state, neighbors in data["adjacency"].items():
        for to_state, distance in neighbors.items():
            conn.execute(
                "INSERT OR IGNORE INTO state_adjacency (from_state, to_state, distance_km) VALUES (?, ?, ?)",
                (from_state, to_state, distance),
            )

    conn.commit()


def seed_initial_threat_levels(conn: sqlite3.Connection) -> None:
    """Seed baseline threat levels from public source estimates.

    These are rough initial values based on publicly available travel advisories.
    Analysts should update these with current ground-truth intelligence.
    """
    # Initial threat levels based on general knowledge of Venezuelan security situation
    # Source: US State Dept Level 4 advisory (reconsider travel), general assessments
    initial_levels = {
        "DC": {"overall": "HIGH", "crime": "HIGH", "political": "HIGH", "infra": "MEDIUM", "natural": "LOW"},
        "MI": {"overall": "HIGH", "crime": "HIGH", "political": "MEDIUM", "infra": "MEDIUM", "natural": "LOW"},
        "VA": {"overall": "HIGH", "crime": "HIGH", "political": "MEDIUM", "infra": "MEDIUM", "natural": "LOW"},
        "AR": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "MEDIUM", "infra": "MEDIUM", "natural": "LOW"},
        "CA": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "MEDIUM", "infra": "MEDIUM", "natural": "LOW"},
        "YA": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "LOW", "infra": "MEDIUM", "natural": "LOW"},
        "LA": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "MEDIUM", "infra": "MEDIUM", "natural": "LOW"},
        "FA": {"overall": "HIGH", "crime": "HIGH", "political": "MEDIUM", "infra": "HIGH", "natural": "LOW"},
        "ZU": {"overall": "CRITICAL", "crime": "CRITICAL", "political": "HIGH", "infra": "HIGH", "natural": "LOW"},
        "TR": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "LOW", "infra": "MEDIUM", "natural": "LOW"},
        "ME": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "LOW", "infra": "MEDIUM", "natural": "MEDIUM"},
        "TA": {"overall": "HIGH", "crime": "HIGH", "political": "HIGH", "infra": "MEDIUM", "natural": "LOW"},
        "BA": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "LOW", "infra": "MEDIUM", "natural": "MEDIUM"},
        "PO": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "LOW", "infra": "MEDIUM", "natural": "LOW"},
        "CO": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "LOW", "infra": "MEDIUM", "natural": "LOW"},
        "GU": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "LOW", "infra": "HIGH", "natural": "LOW"},
        "AP": {"overall": "CRITICAL", "crime": "CRITICAL", "political": "HIGH", "infra": "CRITICAL", "natural": "MEDIUM"},
        "AN": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "MEDIUM", "infra": "MEDIUM", "natural": "LOW"},
        "MO": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "MEDIUM", "infra": "MEDIUM", "natural": "LOW"},
        "SU": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "MEDIUM", "infra": "MEDIUM", "natural": "LOW"},
        "DA": {"overall": "HIGH", "crime": "HIGH", "political": "LOW", "infra": "HIGH", "natural": "HIGH"},
        "BO": {"overall": "HIGH", "crime": "HIGH", "political": "MEDIUM", "infra": "HIGH", "natural": "LOW"},
        "AM": {"overall": "HIGH", "crime": "HIGH", "political": "LOW", "infra": "CRITICAL", "natural": "HIGH"},
        "NE": {"overall": "MEDIUM", "crime": "MEDIUM", "political": "LOW", "infra": "LOW", "natural": "MEDIUM"},
    }

    for state_id, levels in initial_levels.items():
        conn.execute(
            """INSERT INTO threat_levels
               (state_id, overall_level, crime, political, infrastructure, natural_hazards, source, updated_by)
               VALUES (?, ?, ?, ?, ?, ?, 'seed', 'system')""",
            (state_id, levels["overall"], levels["crime"], levels["political"], levels["infra"], levels["natural"]),
        )

    conn.commit()


def seed_no_go_zones(conn: sqlite3.Connection) -> None:
    """Seed known no-go zones."""
    zones = [
        ("AP", "Border region with Colombia", "Armed group activity, kidnapping risk"),
        ("ZU", "Sur del Lago region", "Organized crime, extortion"),
        ("BO", "Mining areas south of Ciudad Bolivar", "Illegal mining gangs, armed groups"),
        ("AM", "Southern border areas", "Armed group presence, no state authority"),
        ("TA", "Colombian border crossings (informal)", "Smuggling routes, unpredictable security"),
    ]
    for state_id, zone_name, reason in zones:
        conn.execute(
            "INSERT INTO no_go_zones (state_id, zone_name, reason, updated_by) VALUES (?, ?, ?, 'system')",
            (state_id, zone_name, reason),
        )
    conn.commit()


def seed_default_api_key(conn: sqlite3.Connection) -> None:
    """Create a default API key for initial setup. Print it once."""
    default_key = "transport-analyst-default-key-2026"
    key_hash = hashlib.sha256(default_key.encode()).hexdigest()

    existing = conn.execute("SELECT 1 FROM api_keys WHERE key_hash = ?", (key_hash,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO api_keys (key_hash, analyst_name) VALUES (?, ?)",
            (key_hash, "default_analyst"),
        )
        conn.commit()
        print(f"Default API key created: {default_key}")
        print("Change this in production!")
    else:
        print("Default API key already exists.")


def seed_default_client(conn: sqlite3.Connection) -> None:
    """Create a default client for testing."""
    conn.execute(
        """INSERT OR IGNORE INTO clients (client_id, name, risk_tolerance, preferred_vehicle_type, contact_email)
           VALUES ('default', 'Test Client', 'MEDIUM', 'armored_suv', 'test@example.com')""",
    )
    conn.commit()


def main(db_path: Path | None = None) -> None:
    """Run full seed: schema + states + threat levels + no-go zones + default key."""
    path = db_path or DB_PATH
    if path.exists():
        print(f"Database already exists at {path}. Skipping seed.")
        print("Delete the file and re-run to reseed.")
        return

    print(f"Creating database at {path}...")
    conn = get_db(path)
    try:
        init_schema(conn)
        print("Schema created.")

        seed_states(conn)
        print("24 states seeded with adjacency data.")

        seed_initial_threat_levels(conn)
        print("Initial threat levels seeded (24 states).")

        seed_no_go_zones(conn)
        print("No-go zones seeded.")

        seed_default_api_key(conn)
        seed_default_client(conn)

        # Verify
        count = conn.execute("SELECT COUNT(*) FROM states").fetchone()[0]
        print(f"\nVerification: {count} states in database.")
        threat_count = conn.execute("SELECT COUNT(*) FROM threat_levels").fetchone()[0]
        print(f"Verification: {threat_count} threat level records.")
        adj_count = conn.execute("SELECT COUNT(*) FROM state_adjacency").fetchone()[0]
        print(f"Verification: {adj_count} adjacency edges.")
        print("\nSeed complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
