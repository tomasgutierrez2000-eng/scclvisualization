"""API key authentication for the Analyst Portal."""
import hashlib
import sqlite3
from functools import wraps
from pathlib import Path

from flask import request, jsonify, g

DB_PATH = Path(__file__).parent.parent.parent / "shared" / "db" / "intel.db"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def require_api_key(f):
    """Decorator: require valid API key in X-API-Key header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"error": "Missing X-API-Key header"}), 401

        db = get_db()
        key_hash = hash_key(api_key)
        row = db.execute(
            "SELECT analyst_name FROM api_keys WHERE key_hash = ? AND is_active = 1",
            (key_hash,),
        ).fetchone()

        if not row:
            return jsonify({"error": "Invalid API key"}), 401

        # Update last_used_at
        db.execute(
            "UPDATE api_keys SET last_used_at = datetime('now') WHERE key_hash = ?",
            (key_hash,),
        )
        db.commit()

        g.analyst_name = row["analyst_name"]
        return f(*args, **kwargs)
    return decorated
