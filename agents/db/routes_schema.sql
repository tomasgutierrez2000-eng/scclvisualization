-- Route Intelligence Database (routes.db)
-- H3 hex grid cells, GPS traversals, missions, events
-- See: agents/db/connections.py for connection helpers
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ============================================================
-- ROUTE CACHE (Google Directions API responses)
-- ============================================================

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,               -- SHA-256(origin+dest+waypoints+alt_index)
    origin_name TEXT NOT NULL,
    origin_lat REAL NOT NULL,
    origin_lng REAL NOT NULL,
    destination_name TEXT NOT NULL,
    destination_lat REAL NOT NULL,
    destination_lng REAL NOT NULL,
    waypoints_json TEXT,                      -- JSON array of {lat, lng, name}
    total_distance_m REAL NOT NULL,
    total_duration_s REAL NOT NULL,
    google_response_json TEXT,               -- full cached Directions API response
    alternative_index INTEGER DEFAULT 0,     -- 0=primary, 1=alt1, 2=alt2
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT                           -- cache expiry (24h default)
);

-- ============================================================
-- H3 CELLS ALONG ROUTES
-- ============================================================

CREATE TABLE IF NOT EXISTS route_cells (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id TEXT NOT NULL REFERENCES routes(route_id) ON DELETE CASCADE,
    h3_cell_id TEXT NOT NULL,                -- H3 index at resolution 8 (~460m edge)
    sequence_order INTEGER NOT NULL,
    distance_through_cell_m REAL,
    road_name TEXT,
    road_class TEXT CHECK(road_class IN ('highway','arterial','local','unpaved','unknown')),
    state_id TEXT,                            -- FK to intel.db states (cross-db, no constraint)
    UNIQUE(route_id, h3_cell_id, sequence_order)
);

CREATE INDEX IF NOT EXISTS idx_route_cells_route
    ON route_cells(route_id, sequence_order);

CREATE INDEX IF NOT EXISTS idx_route_cells_h3
    ON route_cells(h3_cell_id);

-- ============================================================
-- GPS BREADCRUMBS (raw ingest, high-frequency writes)
-- ============================================================

CREATE TABLE IF NOT EXISTS gps_breadcrumbs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    altitude_m REAL,
    speed_kmh REAL,
    heading REAL,
    accuracy_m REAL,
    device_timestamp TEXT NOT NULL,          -- ISO 8601 from device
    received_at TEXT DEFAULT (datetime('now')),
    processed INTEGER DEFAULT 0,            -- 0=pending, 1=matched, 2=discarded
    matched_h3_cell_id TEXT,
    discard_reason TEXT                       -- 'speed_check', 'teleportation', 'out_of_bounds', 'revoked'
);

CREATE INDEX IF NOT EXISTS idx_breadcrumbs_pending
    ON gps_breadcrumbs(processed, received_at)
    WHERE processed = 0;

CREATE INDEX IF NOT EXISTS idx_breadcrumbs_device
    ON gps_breadcrumbs(device_id, device_timestamp DESC);

-- ============================================================
-- TRAVERSALS (GPS data matched to H3 cells)
-- ============================================================

CREATE TABLE IF NOT EXISTS traversals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    h3_cell_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    team_member TEXT,
    device_id TEXT NOT NULL,
    traversal_start TEXT NOT NULL,           -- ISO 8601
    traversal_end TEXT,
    avg_speed_kmh REAL,
    conditions_noted TEXT,
    incidents_observed TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_traversals_cell
    ON traversals(h3_cell_id, traversal_start DESC);

CREATE INDEX IF NOT EXISTS idx_traversals_team
    ON traversals(team_id, traversal_start DESC);

-- ============================================================
-- SCOUTING STATUS (per H3 cell)
-- ============================================================

CREATE TABLE IF NOT EXISTS scouting_status (
    h3_cell_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'unscouted'
        CHECK(status IN ('unscouted','scheduled','scouted','stale')),
    last_scouted_at TEXT,
    scouted_by TEXT,
    next_scout_due TEXT,
    scout_priority INTEGER DEFAULT 10,       -- 1=highest, 10=lowest
    assigned_to TEXT,
    assigned_at TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- CELL RISK SCORES (computed, cached)
-- ============================================================

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
    inputs_hash TEXT                          -- for cache invalidation
);

-- ============================================================
-- EVENT BUS (SQLite-backed queue for decoupled processing)
-- ============================================================
--
-- Pipeline: GPS_ARRIVED → SEGMENT_MATCHED → SCORE_UPDATED
-- Consumers poll for unprocessed events of their type.

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,                -- 'gps_arrived', 'segment_matched', 'score_updated', 'incident_reported'
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    processed_at TEXT,                       -- NULL = unprocessed
    consumer TEXT                            -- which consumer processed it
);

CREATE INDEX IF NOT EXISTS idx_events_pending
    ON events(event_type, created_at)
    WHERE processed_at IS NULL;

-- ============================================================
-- MISSIONS (active operational movements)
-- ============================================================

CREATE TABLE IF NOT EXISTS missions (
    mission_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    route_id TEXT REFERENCES routes(route_id),
    status TEXT NOT NULL DEFAULT 'planning'
        CHECK(status IN ('planning','briefed','active','completed','aborted')),
    departure_time TEXT,
    eta TEXT,
    team_id TEXT,
    team_members_json TEXT,                  -- JSON array of member names
    vehicle_ids_json TEXT,                   -- JSON array of vehicle IDs
    briefing_json TEXT,                      -- full mission briefing
    aar_json TEXT,                           -- after-action report
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_missions_status
    ON missions(status, departure_time);

CREATE INDEX IF NOT EXISTS idx_missions_client
    ON missions(client_id, status);

-- ============================================================
-- RISK PATTERNS (predictive, time-bucketed)
-- ============================================================

CREATE TABLE IF NOT EXISTS risk_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    h3_cell_id TEXT NOT NULL,
    day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
    hour_bucket INTEGER NOT NULL CHECK(hour_bucket BETWEEN 0 AND 23),
    incident_count INTEGER DEFAULT 0,
    avg_risk_score REAL,
    pattern_confidence REAL DEFAULT 0,       -- 0.0 to 1.0
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(h3_cell_id, day_of_week, hour_bucket)
);

-- ============================================================
-- DEVICE TOKENS (GPS device authentication)
-- ============================================================

CREATE TABLE IF NOT EXISTS device_tokens (
    device_id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL,                -- SHA-256 hash of bearer token
    team_id TEXT NOT NULL,
    device_type TEXT,                         -- 'garmin_inreach', 'traccar', 'obd_gps'
    is_active INTEGER DEFAULT 1,
    revoked_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    last_seen_at TEXT
);
