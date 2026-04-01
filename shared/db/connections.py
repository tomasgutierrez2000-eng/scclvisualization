"""Shared database connection helpers.

All modules that need DB access import from here. This ensures
consistent WAL mode, row_factory, and retry behavior.

Architecture:
    ┌──────────────────────┐
    │  agents/db/connections│
    │                      │
    │  get_intel_db()  ────┼──► intel.db (threats, incidents, etc)
    │  get_routes_db() ────┼──► routes.db (H3 cells, traversals, missions)
    └──────────────────────┘
"""
import sqlite3
import time
from pathlib import Path

DB_DIR = Path(__file__).parent
INTEL_DB_PATH = DB_DIR / "intel.db"
ROUTES_DB_PATH = DB_DIR / "routes.db"

MAX_RETRIES = 3
RETRY_DELAY_S = 0.1


def _connect(db_path: Path) -> sqlite3.Connection:
    """Create a connection with WAL mode and row_factory."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def get_intel_db() -> sqlite3.Connection:
    """Get a connection to intel.db (threats, incidents, checkpoints)."""
    return _connect(INTEL_DB_PATH)


def get_routes_db() -> sqlite3.Connection:
    """Get a connection to routes.db (H3 cells, traversals, missions)."""
    return _connect(ROUTES_DB_PATH)


def execute_with_retry(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute SQL with retry on SQLITE_BUSY.

    SQLite WAL mode reduces contention but writes can still conflict.
    Retry up to MAX_RETRIES times with exponential backoff.
    """
    for attempt in range(MAX_RETRIES):
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_S * (2 ** attempt))
                continue
            raise


def init_routes_db() -> None:
    """Initialize routes.db by running the schema SQL."""
    schema_path = DB_DIR.parent.parent / "ruta" / "db" / "routes_schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"routes_schema.sql not found at {schema_path}")
    conn = get_routes_db()
    try:
        conn.executescript(schema_path.read_text())
        conn.commit()
    finally:
        conn.close()
