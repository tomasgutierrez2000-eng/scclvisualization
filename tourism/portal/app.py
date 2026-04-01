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


# ---- Landing page ----

@app.route("/")
def index():
    """Landing page with API docs and interactive state dashboard."""
    db = get_db()
    rows = db.execute("""
        SELECT s.state_id, s.name, s.capital,
               t.overall_level, t.crime, t.political, t.infrastructure, t.natural_hazards,
               t.updated_at
        FROM states s
        LEFT JOIN threat_levels t ON s.state_id = t.state_id
            AND t.updated_at = (SELECT MAX(t2.updated_at) FROM threat_levels t2 WHERE t2.state_id = s.state_id)
        ORDER BY s.name
    """).fetchall()
    states = [dict(r) for r in rows]

    # Count incidents in last 30 days
    incident_count = db.execute(
        "SELECT COUNT(*) as cnt FROM incidents WHERE incident_date >= date('now', '-30 days')"
    ).fetchone()["cnt"]

    # Count active no-go zones
    nogo_count = db.execute(
        "SELECT COUNT(*) as cnt FROM no_go_zones WHERE is_active = 1"
    ).fetchone()["cnt"]

    import json
    states_json = json.dumps(states)

    # State center coordinates for the map
    state_coords = {
        "DC": [10.48, -66.87], "MI": [10.25, -66.42], "VA": [10.60, -66.93],
        "AR": [10.07, -67.53], "CA": [10.11, -67.96], "LA": [10.07, -69.32],
        "YA": [10.33, -68.73], "FA": [11.07, -69.85], "ZU": [10.00, -71.64],
        "TR": [9.37, -70.43], "ME": [8.60, -71.14], "TA": [7.77, -72.23],
        "BA": [8.62, -70.21], "PO": [9.06, -69.75], "CO": [9.68, -68.58],
        "GU": [8.75, -68.25], "AP": [7.63, -69.20], "BO": [7.63, -63.55],
        "AM": [3.42, -65.86], "DE": [9.93, -63.35], "AN": [8.59, -63.57],
        "MO": [9.75, -63.19], "SU": [10.45, -63.25], "NE": [11.00, -63.91],
    }
    coords_json = json.dumps(state_coords)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VZ Tourism - Analyst Portal</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f0f1a; color: #e5e7eb; }}

  .topbar {{ background: #1a1a2e; padding: 16px 24px; border-bottom: 1px solid #2d2d44; display: flex; align-items: center; justify-content: space-between; }}
  .topbar h1 {{ font-size: 20px; font-weight: 600; }}
  .topbar h1 span {{ color: #3b82f6; }}
  .topbar .stats {{ display: flex; gap: 24px; font-size: 13px; color: #9ca3af; }}
  .topbar .stats .val {{ color: #e5e7eb; font-weight: 600; font-size: 15px; }}

  .layout {{ display: flex; height: calc(100vh - 57px); }}

  .sidebar {{ width: 360px; background: #1a1a2e; border-right: 1px solid #2d2d44; overflow-y: auto; }}
  .sidebar-header {{ padding: 16px; border-bottom: 1px solid #2d2d44; }}
  .sidebar-header input {{ width: 100%; padding: 8px 12px; border-radius: 6px; border: 1px solid #2d2d44; background: #0f0f1a; color: #e5e7eb; font-size: 14px; outline: none; }}
  .sidebar-header input:focus {{ border-color: #3b82f6; }}

  .state-card {{ padding: 12px 16px; border-bottom: 1px solid #1f1f35; cursor: pointer; transition: background .15s; }}
  .state-card:hover {{ background: #1f1f35; }}
  .state-card.active {{ background: #1f2937; border-left: 3px solid #3b82f6; }}
  .state-card .name {{ font-weight: 600; font-size: 14px; }}
  .state-card .capital {{ font-size: 12px; color: #6b7280; margin-top: 2px; }}
  .state-card .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-top: 4px; }}
  .badge-LOW {{ background: #052e16; color: #22c55e; }}
  .badge-MEDIUM {{ background: #422006; color: #f59e0b; }}
  .badge-HIGH {{ background: #431407; color: #f97316; }}
  .badge-CRITICAL {{ background: #450a0a; color: #ef4444; }}

  .main {{ flex: 1; display: flex; flex-direction: column; }}
  #map {{ flex: 1; background: #0f0f1a; }}

  .detail-panel {{ width: 380px; background: #1a1a2e; border-left: 1px solid #2d2d44; overflow-y: auto; padding: 20px; display: none; }}
  .detail-panel.show {{ display: block; }}
  .detail-panel h2 {{ font-size: 18px; margin-bottom: 12px; }}
  .detail-panel .section {{ margin-bottom: 16px; }}
  .detail-panel .section h3 {{ font-size: 13px; color: #6b7280; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 8px; }}
  .threat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
  .threat-item {{ background: #0f0f1a; padding: 10px; border-radius: 6px; }}
  .threat-item .label {{ font-size: 11px; color: #6b7280; }}
  .threat-item .value {{ font-size: 14px; font-weight: 600; margin-top: 2px; }}
  .color-LOW {{ color: #22c55e; }}
  .color-MEDIUM {{ color: #f59e0b; }}
  .color-HIGH {{ color: #f97316; }}
  .color-CRITICAL {{ color: #ef4444; }}

  .incidents-list {{ max-height: 200px; overflow-y: auto; }}
  .incident {{ background: #0f0f1a; padding: 8px 10px; border-radius: 6px; margin-bottom: 6px; font-size: 13px; }}
  .incident .type {{ font-weight: 600; text-transform: capitalize; }}
  .incident .desc {{ color: #9ca3af; margin-top: 2px; }}

  .api-section {{ padding: 16px; border-top: 1px solid #2d2d44; background: #0f0f1a; font-size: 12px; color: #6b7280; }}
  .api-section code {{ background: #1a1a2e; padding: 2px 6px; border-radius: 3px; color: #3b82f6; }}
</style>
</head>
<body>
<div class="topbar">
  <h1><span>VZ</span> Tourism - Analyst Portal</h1>
  <div class="stats">
    <div><div class="val">{len(states)}</div>States</div>
    <div><div class="val">{incident_count}</div>Incidents (30d)</div>
    <div><div class="val">{nogo_count}</div>No-Go Zones</div>
  </div>
</div>
<div class="layout">
  <div class="sidebar">
    <div class="sidebar-header">
      <input type="text" id="search" placeholder="Search states..." />
    </div>
    <div id="state-list"></div>
    <div class="api-section">
      API: <code>GET /api/states</code> &middot; Header: <code>X-API-Key</code>
    </div>
  </div>
  <div class="main">
    <div id="map"></div>
  </div>
  <div class="detail-panel" id="detail">
    <h2 id="detail-name"></h2>
    <div class="section">
      <h3>Threat Assessment</h3>
      <div class="threat-grid" id="detail-threats"></div>
    </div>
    <div class="section">
      <h3>Recent Incidents</h3>
      <div class="incidents-list" id="detail-incidents"><em>Loading...</em></div>
    </div>
    <div class="section">
      <h3>No-Go Zones</h3>
      <div id="detail-nogo"><em>Loading...</em></div>
    </div>
  </div>
</div>
<script>
const API_KEY = "transport-analyst-default-key-2026";
const states = {states_json};
const coords = {coords_json};

const riskColors = {{ LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444' }};

// Build sidebar
const listEl = document.getElementById('state-list');
function renderList(filter = '') {{
  listEl.innerHTML = '';
  states.filter(s => !filter || s.name.toLowerCase().includes(filter) || s.state_id.toLowerCase().includes(filter))
    .forEach(s => {{
      const card = document.createElement('div');
      card.className = 'state-card';
      card.dataset.id = s.state_id;
      card.innerHTML = `<div class="name">${{s.name}} <span style="color:#6b7280;font-weight:400">${{s.state_id}}</span></div>
        <div class="capital">${{s.capital}}</div>
        <span class="badge badge-${{s.overall_level || 'MEDIUM'}}">${{s.overall_level || 'N/A'}}</span>`;
      card.onclick = () => selectState(s.state_id);
      listEl.appendChild(card);
    }});
}}
renderList();
document.getElementById('search').addEventListener('input', e => renderList(e.target.value.toLowerCase()));

// Map
const map = L.map('map', {{ zoomControl: true }}).setView([8.0, -66.0], 6);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; CartoDB', subdomains: 'abcd', maxZoom: 19
}}).addTo(map);

const markers = {{}};
states.forEach(s => {{
  const c = coords[s.state_id];
  if (!c) return;
  const color = riskColors[s.overall_level] || '#6b7280';
  const marker = L.circleMarker(c, {{
    radius: 10, fillColor: color, color: '#1a1a2e', weight: 2, fillOpacity: 0.85
  }}).addTo(map);
  marker.bindTooltip(`${{s.name}}: ${{s.overall_level || 'N/A'}}`, {{ direction: 'top' }});
  marker.on('click', () => selectState(s.state_id));
  markers[s.state_id] = marker;
}});

// Detail panel
async function selectState(id) {{
  document.querySelectorAll('.state-card').forEach(c => c.classList.remove('active'));
  const card = document.querySelector(`.state-card[data-id="${{id}}"]`);
  if (card) card.classList.add('active');

  const s = states.find(x => x.state_id === id);
  if (!s) return;

  const panel = document.getElementById('detail');
  panel.classList.add('show');
  document.getElementById('detail-name').textContent = `${{s.name}} (${{s.state_id}})`;

  const fields = ['crime', 'political', 'infrastructure', 'natural_hazards'];
  document.getElementById('detail-threats').innerHTML = fields.map(f => `
    <div class="threat-item">
      <div class="label">${{f.replace('_', ' ')}}</div>
      <div class="value color-${{s[f] || 'MEDIUM'}}">${{s[f] || 'N/A'}}</div>
    </div>`).join('');

  // Fetch incidents
  const headers = {{ 'X-API-Key': API_KEY }};
  try {{
    const incRes = await fetch(`/api/states/${{id}}/incidents?days=30`, {{ headers }});
    const incidents = await incRes.json();
    document.getElementById('detail-incidents').innerHTML = incidents.length
      ? incidents.map(i => `<div class="incident"><span class="type">${{i.incident_type}}</span> &middot; ${{i.severity}}<div class="desc">${{i.description || ''}}</div></div>`).join('')
      : '<em style="color:#6b7280">No incidents in last 30 days</em>';
  }} catch(e) {{ document.getElementById('detail-incidents').innerHTML = '<em>Error loading</em>'; }}

  try {{
    const ngRes = await fetch(`/api/states/${{id}}/no-go-zones`, {{ headers }});
    const zones = await ngRes.json();
    document.getElementById('detail-nogo').innerHTML = zones.length
      ? zones.map(z => `<div class="incident"><span class="type">${{z.zone_name}}</span><div class="desc">${{z.reason || ''}}</div></div>`).join('')
      : '<em style="color:#6b7280">No active no-go zones</em>';
  }} catch(e) {{ document.getElementById('detail-nogo').innerHTML = '<em>Error loading</em>'; }}

  if (coords[id]) map.flyTo(coords[id], 8);
}}
</script>
</body>
</html>"""


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
