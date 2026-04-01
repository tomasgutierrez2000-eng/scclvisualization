"""Risk Heat Map generator using Leaflet.js.

Generates an interactive HTML map of Venezuela with:
- States color-coded by risk level (green/amber/orange/red/gray)
- Text labels on each state (colorblind-safe)
- Route overlay as a blue line
- Hover to preview risk card, click to pin
- Sidebar with route summary
- Legend with intel freshness indicator

Design spec from plan-design-review:
  Background: #1a1a2e (dark navy)
  Map boundaries: #2d2d44
  Text: #e5e7eb
  Risk colors: LOW #22c55e, MEDIUM #f59e0b, HIGH #f97316, CRITICAL #ef4444, NO DATA #6b7280
  Route line: #3b82f6, 3px
"""
import json
import webbrowser
from datetime import datetime
from pathlib import Path

from tourism.schemas.route_proposal import RouteProposal
from tourism.schemas.security_briefing import SecurityBriefing

OUTPUT_DIR = Path(__file__).parent

# Venezuelan state approximate center coordinates (lat, lng)
STATE_COORDS = {
    "DC": [10.48, -66.87], "MI": [10.25, -66.42], "VA": [10.60, -66.93],
    "AR": [10.23, -67.59], "CA": [10.18, -68.00], "YA": [10.35, -68.75],
    "LA": [10.07, -69.36], "FA": [11.41, -69.67], "ZU": [10.00, -71.64],
    "TR": [9.37, -70.43], "ME": [8.60, -71.14], "TA": [7.77, -72.23],
    "BA": [8.62, -70.21], "PO": [9.04, -69.75], "CO": [9.65, -68.58],
    "GU": [8.75, -67.36], "AP": [7.88, -69.27], "AN": [10.12, -64.69],
    "MO": [9.74, -63.18], "SU": [10.46, -63.25], "DA": [9.07, -62.05],
    "BO": [7.63, -63.55], "AM": [3.42, -65.85], "NE": [11.00, -63.91],
}

RISK_COLORS = {
    "LOW": "#22c55e",
    "MEDIUM": "#f59e0b",
    "HIGH": "#f97316",
    "CRITICAL": "#ef4444",
}
NO_DATA_COLOR = "#6b7280"
ROUTE_COLOR = "#3b82f6"


def generate_heat_map(
    route_proposal: RouteProposal,
    security_briefing: SecurityBriefing,
    output_path: Path | None = None,
    open_browser: bool = True,
) -> str:
    """Generate an interactive risk heat map HTML file.

    Args:
        route_proposal: The planned route
        security_briefing: Security assessment for route states
        output_path: Where to save the HTML. Defaults to output/{timestamp}_map.html
        open_browser: Whether to open the map in the default browser

    Returns:
        Path to the generated HTML file.
    """
    if output_path is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"{timestamp}_map.html"

    # Build state risk data
    state_risks = {}
    for assessment in security_briefing.state_assessments:
        state_risks[assessment.state_id] = {
            "level": assessment.risk_level,
            "color": RISK_COLORS.get(assessment.risk_level, NO_DATA_COLOR),
            "crime": assessment.threat_breakdown.crime,
            "political": assessment.threat_breakdown.political,
            "infrastructure": assessment.threat_breakdown.infrastructure,
            "natural": assessment.threat_breakdown.natural_hazards,
            "no_go_zones": assessment.no_go_zones,
            "posture": assessment.recommended_security_posture,
            "is_no_go": assessment.is_no_go,
            "freshness": assessment.intelligence_freshness or "unknown",
        }

    # Route coordinates for the polyline
    route_states = route_proposal.primary_route.states_traversed
    route_coords = [STATE_COORDS.get(s, [8, -66]) for s in route_states]

    # Build route summary for sidebar
    segments_info = []
    for seg in route_proposal.primary_route.segments:
        segments_info.append({
            "from": seg.from_location,
            "to": seg.to_location,
            "km": seg.distance_km,
            "hours": seg.estimated_hours,
            "states": seg.states_traversed,
        })

    html = _build_html(
        state_risks=state_risks,
        route_coords=route_coords,
        route_states=route_states,
        segments_info=segments_info,
        overall_risk=security_briefing.overall_risk_level,
        risk_score=security_briefing.route_risk_score,
        total_km=route_proposal.primary_route.total_distance_km,
        total_days=route_proposal.primary_route.total_days,
        recommendations=security_briefing.recommendations,
        origin=route_proposal.primary_route.segments[0].from_location if route_proposal.primary_route.segments else "?",
        destination=route_proposal.primary_route.segments[-1].to_location if route_proposal.primary_route.segments else "?",
    )

    output_path.write_text(html)

    if open_browser:
        webbrowser.open(f"file://{output_path.resolve()}")

    return str(output_path)


def _build_html(**kwargs) -> str:
    state_risks_json = json.dumps(kwargs["state_risks"])
    route_coords_json = json.dumps(kwargs["route_coords"])
    route_states_json = json.dumps(kwargs["route_states"])
    segments_json = json.dumps(kwargs["segments_info"])
    recommendations_json = json.dumps(kwargs["recommendations"])
    state_coords_json = json.dumps(STATE_COORDS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Route Security Heat Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'SF Mono', 'Fira Code', monospace; background: #1a1a2e; color: #e5e7eb; }}
  #container {{ display: flex; height: 100vh; }}
  #sidebar {{ width: 280px; padding: 16px; overflow-y: auto; background: #16213e; border-right: 1px solid #2d2d44; }}
  #map {{ flex: 1; }}
  #risk-panel {{ width: 300px; padding: 16px; overflow-y: auto; background: #16213e; border-left: 1px solid #2d2d44; }}
  h1 {{ font-size: 14px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }}
  h2 {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin: 16px 0 8px; }}
  .risk-badge {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; }}
  .risk-LOW {{ background: #22c55e22; color: #22c55e; border: 1px solid #22c55e44; }}
  .risk-MEDIUM {{ background: #f59e0b22; color: #f59e0b; border: 1px solid #f59e0b44; }}
  .risk-HIGH {{ background: #f9731622; color: #f97316; border: 1px solid #f9731644; }}
  .risk-CRITICAL {{ background: #ef444422; color: #ef4444; border: 1px solid #ef444444; }}
  .stat {{ margin: 4px 0; font-size: 13px; }}
  .stat-label {{ color: #64748b; }}
  .stat-value {{ color: #e5e7eb; font-weight: bold; }}
  .segment {{ padding: 8px; margin: 4px 0; background: #1a1a2e; border-radius: 4px; font-size: 12px; }}
  .rec {{ padding: 6px 8px; margin: 4px 0; background: #1a1a2e; border-radius: 4px; font-size: 11px; border-left: 2px solid #f59e0b; }}
  #risk-panel .state-card {{ padding: 12px; margin: 8px 0; background: #1a1a2e; border-radius: 6px; }}
  .threat-row {{ display: flex; justify-content: space-between; padding: 3px 0; font-size: 12px; }}
  .legend {{ position: absolute; bottom: 20px; left: 300px; z-index: 1000; background: #16213eee; padding: 10px 14px; border-radius: 6px; border: 1px solid #2d2d44; font-size: 11px; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; margin: 3px 0; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 2px; }}
  .no-state {{ color: #64748b; font-style: italic; text-align: center; margin-top: 40px; }}
</style>
</head>
<body>
<div id="container">
  <div id="sidebar">
    <h1>Route Summary</h1>
    <div class="stat">
      <span class="stat-label">Route:</span>
      <span class="stat-value">{kwargs['origin']} → {kwargs['destination']}</span>
    </div>
    <div class="stat">
      <span class="stat-label">Distance:</span>
      <span class="stat-value">{kwargs['total_km']} km</span>
    </div>
    <div class="stat">
      <span class="stat-label">Days:</span>
      <span class="stat-value">{kwargs['total_days']}</span>
    </div>
    <div class="stat">
      <span class="stat-label">Overall Risk:</span>
      <span class="risk-badge risk-{kwargs['overall_risk']}">{kwargs['overall_risk']}</span>
    </div>
    <div class="stat">
      <span class="stat-label">Risk Score:</span>
      <span class="stat-value">{kwargs['risk_score']}/10</span>
    </div>

    <h2>Route Segments</h2>
    <div id="segments"></div>

    <h2>Recommendations</h2>
    <div id="recs"></div>
  </div>

  <div id="map"></div>

  <div id="risk-panel">
    <h1>State Intelligence</h1>
    <p class="no-state" id="no-state-msg">Hover over a state on the map to see its risk profile. Click to pin.</p>
    <div id="state-detail" style="display:none;"></div>
  </div>
</div>

<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div> LOW</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div> MEDIUM</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f97316"></div> HIGH</div>
  <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div> CRITICAL</div>
  <div class="legend-item"><div class="legend-dot" style="background:#6b7280"></div> NO DATA</div>
  <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div> ROUTE</div>
</div>

<script>
const stateRisks = {state_risks_json};
const routeCoords = {route_coords_json};
const routeStates = {route_states_json};
const segments = {segments_json};
const recommendations = {recommendations_json};
const stateCoords = {state_coords_json};

// Init map
const map = L.map('map', {{
  center: [8, -66],
  zoom: 6,
  zoomControl: true,
}});

// Dark tile layer
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 19,
}}).addTo(map);

// State markers with risk colors and labels
let pinnedState = null;

Object.entries(stateCoords).forEach(([stateId, [lat, lng]]) => {{
  const risk = stateRisks[stateId];
  const color = risk ? risk.color : '#6b7280';
  const level = risk ? risk.level : 'N/A';
  const isOnRoute = routeStates.includes(stateId);

  // Circle marker for state
  const marker = L.circleMarker([lat, lng], {{
    radius: isOnRoute ? 18 : 12,
    fillColor: color,
    fillOpacity: isOnRoute ? 0.8 : 0.4,
    color: isOnRoute ? '#e5e7eb' : '#2d2d44',
    weight: isOnRoute ? 2 : 1,
  }}).addTo(map);

  // Text label (colorblind-safe)
  const label = L.divIcon({{
    className: '',
    html: `<div style="color:#fff;font-size:${{isOnRoute ? 11 : 9}}px;font-weight:bold;text-align:center;text-shadow:0 0 4px #000;white-space:nowrap;">${{stateId}}<br><span style="font-size:${{isOnRoute ? 9 : 7}}px">${{level}}</span></div>`,
    iconSize: [40, 20],
    iconAnchor: [20, 10],
  }});
  L.marker([lat, lng], {{ icon: label, interactive: false }}).addTo(map);

  // Hover: show risk panel
  marker.on('mouseover', () => {{
    if (!pinnedState) showStateDetail(stateId);
  }});
  marker.on('mouseout', () => {{
    if (!pinnedState) hideStateDetail();
  }});
  // Click: pin
  marker.on('click', () => {{
    if (pinnedState === stateId) {{
      pinnedState = null;
      hideStateDetail();
    }} else {{
      pinnedState = stateId;
      showStateDetail(stateId);
    }}
  }});
}});

// Route polyline
L.polyline(routeCoords, {{
  color: '#3b82f6',
  weight: 3,
  opacity: 0.9,
  dashArray: null,
}}).addTo(map);

// Populate segments
const segEl = document.getElementById('segments');
segments.forEach(s => {{
  segEl.innerHTML += `<div class="segment">${{s.from}} → ${{s.to}}<br><span class="stat-label">${{s.km}}km | ${{s.hours}}h | ${{s.states.join(' → ')}}</span></div>`;
}});

// Populate recommendations
const recEl = document.getElementById('recs');
recommendations.forEach(r => {{
  recEl.innerHTML += `<div class="rec">${{r}}</div>`;
}});

function showStateDetail(stateId) {{
  const risk = stateRisks[stateId];
  const el = document.getElementById('state-detail');
  const msg = document.getElementById('no-state-msg');
  msg.style.display = 'none';
  el.style.display = 'block';

  if (!risk) {{
    el.innerHTML = `<div class="state-card"><h2>${{stateId}}</h2><p>No intelligence data available.</p><p class="stat-label">Treating as CRITICAL (conservative).</p></div>`;
    return;
  }}

  const pinIcon = pinnedState === stateId ? ' [PINNED]' : '';
  el.innerHTML = `
    <div class="state-card">
      <h2>${{stateId}}${{pinIcon}}</h2>
      <div class="stat"><span class="stat-label">Overall:</span> <span class="risk-badge risk-${{risk.level}}">${{risk.level}}</span></div>
      <div class="stat"><span class="stat-label">Posture:</span> <span class="stat-value">${{risk.posture}}</span></div>
      <h2>Threat Breakdown</h2>
      <div class="threat-row"><span>Crime</span><span class="risk-badge risk-${{risk.crime}}">${{risk.crime}}</span></div>
      <div class="threat-row"><span>Political</span><span class="risk-badge risk-${{risk.political}}">${{risk.political}}</span></div>
      <div class="threat-row"><span>Infrastructure</span><span class="risk-badge risk-${{risk.infrastructure}}">${{risk.infrastructure}}</span></div>
      <div class="threat-row"><span>Natural Hazards</span><span class="risk-badge risk-${{risk.natural}}">${{risk.natural}}</span></div>
      ${{risk.no_go_zones.length ? `<h2>No-Go Zones</h2>${{risk.no_go_zones.map(z => `<div class="rec">${{z}}</div>`).join('')}}` : ''}}
      <div class="stat" style="margin-top:12px"><span class="stat-label">Intel freshness:</span> <span class="stat-value">${{risk.freshness}}</span></div>
      ${{risk.is_no_go ? '<div class="rec" style="border-color:#ef4444;color:#ef4444;font-weight:bold">STATE FLAGGED AS NO-GO</div>' : ''}}
    </div>
  `;
}}

function hideStateDetail() {{
  document.getElementById('state-detail').style.display = 'none';
  document.getElementById('no-state-msg').style.display = 'block';
}}
</script>
</body>
</html>"""
