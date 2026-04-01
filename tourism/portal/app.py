"""Analyst Portal: Flask app for security analysts to update per-state intelligence."""
import re
import sqlite3
import time
from pathlib import Path

from flask import Flask, request, jsonify, g, render_template

from .auth import require_api_key, get_db, close_db

app = Flask(__name__)

# SQLite write retry on SQLITE_BUSY (WAL mode handles most cases, this is the safety net)
MAX_WRITE_RETRIES = 3
RETRY_DELAY_MS = 100

VALID_THREAT_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_INCIDENT_TYPES = {"robbery", "kidnapping", "protest", "checkpoint", "infrastructure", "other"}

# Patterns to strip from free-text notes (prompt injection defense at write boundary)
# Read-boundary defense is also applied in the Security MCP Server
INJECTION_PATTERNS = re.compile(
    r"(?i)(ignore\s+(previous|all|above|prior)\s+(instructions?|prompts?|rules?))"
    r"|(system\s*prompt)"
    r"|(you\s+are\s+(now|a)\s+)"
    r"|(pretend\s+to\s+be)"
    r"|(act\s+as\s+(if|a)\s+)"
    r"|(forget\s+(everything|all|your))"
    r"|(override\s+(safety|rules|instructions?))"
    r"|(do\s+not\s+follow)"
)


def sanitize_text(text: str) -> str:
    """Strip potential prompt injection patterns from free-text input."""
    return INJECTION_PATTERNS.sub("[REDACTED]", text)


def execute_with_retry(db: sqlite3.Connection, sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute SQL with retry on SQLITE_BUSY."""
    for attempt in range(MAX_WRITE_RETRIES):
        try:
            cursor = db.execute(sql, params)
            db.commit()
            return cursor
        except sqlite3.OperationalError as e:
            if "locked" in str(e) or "busy" in str(e):
                if attempt < MAX_WRITE_RETRIES - 1:
                    time.sleep(RETRY_DELAY_MS / 1000 * (attempt + 1))
                    continue
            raise
    raise sqlite3.OperationalError("Database busy after retries")


app.teardown_appcontext(close_db)


# ---- State listing ----

@app.route("/api/states", methods=["GET"])
@require_api_key
def list_states():
    """List all states with their current threat level."""
    db = get_db()
    rows = db.execute("""
        SELECT s.state_id, s.name, s.capital,
               t.overall_level, t.crime, t.political, t.infrastructure, t.natural_hazards,
               t.updated_at, t.updated_by
        FROM states s
        LEFT JOIN threat_levels t ON s.state_id = t.state_id
            AND t.updated_at = (SELECT MAX(t2.updated_at) FROM threat_levels t2 WHERE t2.state_id = s.state_id)
        ORDER BY s.name
    """).fetchall()

    return jsonify([dict(r) for r in rows])


# ---- Threat level updates ----

@app.route("/api/states/<state_id>/threat", methods=["GET"])
@require_api_key
def get_threat_level(state_id: str):
    """Get current threat level and history for a state."""
    db = get_db()

    # Current level
    current = db.execute("""
        SELECT * FROM threat_levels
        WHERE state_id = ?
        ORDER BY updated_at DESC LIMIT 1
    """, (state_id,)).fetchone()

    if not current:
        return jsonify({"error": f"No threat data for state {state_id}"}), 404

    # Recent history
    history = db.execute("""
        SELECT overall_level, crime, political, infrastructure, natural_hazards,
               source, updated_by, updated_at
        FROM threat_levels
        WHERE state_id = ?
        ORDER BY updated_at DESC LIMIT 5
    """, (state_id,)).fetchall()

    return jsonify({
        "current": dict(current),
        "history": [dict(r) for r in history],
    })


@app.route("/api/states/<state_id>/threat", methods=["POST"])
@require_api_key
def update_threat_level(state_id: str):
    """Update threat level for a state. All fields required."""
    db = get_db()

    # Verify state exists
    state = db.execute("SELECT 1 FROM states WHERE state_id = ?", (state_id,)).fetchone()
    if not state:
        return jsonify({"error": f"Unknown state: {state_id}"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    required = ["overall_level", "crime", "political", "infrastructure", "natural_hazards"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Validate threat levels
    for field in required:
        if data[field] not in VALID_THREAT_LEVELS:
            return jsonify({"error": f"Invalid {field}: {data[field]}. Must be one of {VALID_THREAT_LEVELS}"}), 400

    execute_with_retry(
        db,
        """INSERT INTO threat_levels
           (state_id, overall_level, crime, political, infrastructure, natural_hazards, source, updated_by)
           VALUES (?, ?, ?, ?, ?, ?, 'analyst', ?)""",
        (state_id, data["overall_level"], data["crime"], data["political"],
         data["infrastructure"], data["natural_hazards"], g.analyst_name),
    )

    return jsonify({"status": "updated", "state_id": state_id, "updated_by": g.analyst_name}), 200


# ---- Incidents ----

@app.route("/api/states/<state_id>/incidents", methods=["GET"])
@require_api_key
def list_incidents(state_id: str):
    """List recent incidents for a state."""
    db = get_db()
    days = request.args.get("days", 30, type=int)
    rows = db.execute("""
        SELECT * FROM incidents
        WHERE state_id = ? AND incident_date >= date('now', ?)
        ORDER BY incident_date DESC
    """, (state_id, f"-{days} days")).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/states/<state_id>/incidents", methods=["POST"])
@require_api_key
def add_incident(state_id: str):
    """Report a new incident."""
    db = get_db()
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    if "incident_type" not in data or data["incident_type"] not in VALID_INCIDENT_TYPES:
        return jsonify({"error": f"incident_type required, one of: {VALID_INCIDENT_TYPES}"}), 400
    if "severity" not in data or data["severity"] not in VALID_THREAT_LEVELS:
        return jsonify({"error": f"severity required, one of: {VALID_THREAT_LEVELS}"}), 400

    description = sanitize_text(data.get("description", "")) if data.get("description") else None

    execute_with_retry(
        db,
        """INSERT INTO incidents (state_id, incident_type, severity, description, location, incident_date, reported_by)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (state_id, data["incident_type"], data["severity"], description,
         data.get("location"), data.get("incident_date"), g.analyst_name),
    )

    return jsonify({"status": "recorded", "state_id": state_id}), 201


# ---- No-go zones ----

@app.route("/api/states/<state_id>/no-go-zones", methods=["GET"])
@require_api_key
def list_no_go_zones(state_id: str):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM no_go_zones WHERE state_id = ? AND is_active = 1", (state_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/states/<state_id>/no-go-zones", methods=["POST"])
@require_api_key
def add_no_go_zone(state_id: str):
    db = get_db()
    data = request.get_json()
    if not data or "zone_name" not in data:
        return jsonify({"error": "zone_name required"}), 400

    reason = sanitize_text(data.get("reason", "")) if data.get("reason") else None

    execute_with_retry(
        db,
        "INSERT INTO no_go_zones (state_id, zone_name, reason, updated_by) VALUES (?, ?, ?, ?)",
        (state_id, data["zone_name"], reason, g.analyst_name),
    )

    return jsonify({"status": "added", "state_id": state_id}), 201


# ---- Analyst notes ----

@app.route("/api/states/<state_id>/notes", methods=["GET"])
@require_api_key
def list_notes(state_id: str):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM analyst_notes WHERE state_id = ? ORDER BY created_at DESC LIMIT 10",
        (state_id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/states/<state_id>/notes", methods=["POST"])
@require_api_key
def add_note(state_id: str):
    db = get_db()
    data = request.get_json()
    if not data or "note_text" not in data:
        return jsonify({"error": "note_text required"}), 400

    note_text = data["note_text"]
    if len(note_text) > 500:
        return jsonify({"error": "note_text must be 500 characters or fewer"}), 400

    sanitized = sanitize_text(note_text)

    execute_with_retry(
        db,
        "INSERT INTO analyst_notes (state_id, note_text, analyst_id) VALUES (?, ?, ?)",
        (state_id, sanitized, g.analyst_name),
    )

    return jsonify({"status": "added", "state_id": state_id}), 201


# ---- Checkpoints ----

@app.route("/api/states/<state_id>/checkpoints", methods=["GET"])
@require_api_key
def list_checkpoints(state_id: str):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM checkpoints WHERE state_id = ? AND is_active = 1", (state_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


def create_app(db_path: str | None = None) -> Flask:
    """Factory function for testing with custom DB path."""
    if db_path:
        import tourism.portal.auth as auth_module
        auth_module.DB_PATH = Path(db_path)
    return app


if __name__ == "__main__":
    app.run(debug=True, port=5050)
