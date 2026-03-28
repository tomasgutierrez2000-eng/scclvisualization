-- Venezuela Transport Logistics Intelligence Database
-- Multi-tenant: shared intel tables + per-client trip/preference tables
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ============================================================
-- SHARED TABLES (geographic intel, same for all clients)
-- ============================================================

CREATE TABLE IF NOT EXISTS states (
    state_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    capital TEXT,
    geojson_path TEXT,
    -- adjacency stored in state_adjacency table
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS state_adjacency (
    from_state TEXT NOT NULL REFERENCES states(state_id),
    to_state TEXT NOT NULL REFERENCES states(state_id),
    distance_km REAL NOT NULL,
    road_quality TEXT DEFAULT 'unknown', -- good, fair, poor, unknown
    PRIMARY KEY (from_state, to_state)
);

CREATE TABLE IF NOT EXISTS threat_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id TEXT NOT NULL REFERENCES states(state_id),
    overall_level TEXT NOT NULL CHECK(overall_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    crime TEXT NOT NULL CHECK(crime IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    political TEXT NOT NULL CHECK(political IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    infrastructure TEXT NOT NULL CHECK(infrastructure IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    natural_hazards TEXT NOT NULL CHECK(natural_hazards IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    source TEXT NOT NULL, -- 'analyst', 'external_api', 'seed'
    updated_by TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Index for fast lookups: most recent threat level per state
CREATE INDEX IF NOT EXISTS idx_threat_levels_state_date
    ON threat_levels(state_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id TEXT NOT NULL REFERENCES states(state_id),
    incident_type TEXT NOT NULL, -- 'robbery', 'kidnapping', 'protest', 'checkpoint', 'infrastructure', 'other'
    severity TEXT NOT NULL CHECK(severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    description TEXT,
    location TEXT,
    incident_date TEXT,
    reported_by TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_incidents_state_date
    ON incidents(state_id, incident_date DESC);

CREATE TABLE IF NOT EXISTS no_go_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id TEXT NOT NULL REFERENCES states(state_id),
    zone_name TEXT NOT NULL,
    reason TEXT,
    is_active INTEGER DEFAULT 1,
    updated_by TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id TEXT NOT NULL REFERENCES states(state_id),
    location TEXT NOT NULL,
    authority_type TEXT, -- 'military', 'police', 'national_guard', 'informal'
    behavior_notes TEXT,
    estimated_delay_minutes INTEGER,
    is_active INTEGER DEFAULT 1,
    updated_by TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS analyst_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id TEXT NOT NULL REFERENCES states(state_id),
    note_text TEXT NOT NULL,
    -- Sanitized at read time: free-text wrapped in delimiters before agent consumption
    analyst_id TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_analyst_notes_state_date
    ON analyst_notes(state_id, created_at DESC);

-- API keys for analyst portal authentication
CREATE TABLE IF NOT EXISTS api_keys (
    key_hash TEXT PRIMARY KEY, -- SHA-256 hash of the API key
    analyst_name TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    last_used_at TEXT
);

-- ============================================================
-- PER-CLIENT TABLES (trip plans, preferences)
-- ============================================================

CREATE TABLE IF NOT EXISTS clients (
    client_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    risk_tolerance TEXT DEFAULT 'MEDIUM' CHECK(risk_tolerance IN ('LOW','MEDIUM','HIGH')),
    -- LOW = avoid anything above LOW risk
    -- MEDIUM = accept MEDIUM, avoid HIGH+
    -- HIGH = accept HIGH, avoid only CRITICAL
    preferred_vehicle_type TEXT DEFAULT 'armored_suv',
    contact_email TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS active_trips (
    trip_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL REFERENCES clients(client_id),
    route_states TEXT NOT NULL, -- JSON array of state_ids
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    baseline_risk TEXT NOT NULL, -- JSON: per-state risk at plan time
    status TEXT DEFAULT 'active' CHECK(status IN ('active','completed','cancelled')),
    route_proposal TEXT, -- JSON: full RouteProposal
    security_briefing TEXT, -- JSON: full SecurityBriefing
    trip_plan TEXT, -- JSON: full CompleteTripPlan (Phase 2)
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_active_trips_status
    ON active_trips(status, start_date);

CREATE TABLE IF NOT EXISTS client_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL REFERENCES clients(client_id),
    preference_key TEXT NOT NULL, -- e.g. 'preferred_hotels', 'no_go_override', 'comms_preference'
    preference_value TEXT NOT NULL, -- JSON
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(client_id, preference_key)
);
