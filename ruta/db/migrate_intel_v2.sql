-- Migration: Add lat/lng to incidents and checkpoints for spatial queries
-- Add boundary GeoJSON to no_go_zones for geo-fencing
-- Add spatial index for incident proximity queries in risk engine

-- Incidents: add coordinates for proximity-based risk scoring
ALTER TABLE incidents ADD COLUMN lat REAL;
ALTER TABLE incidents ADD COLUMN lng REAL;

-- Checkpoints: add coordinates for proximity-based risk scoring
ALTER TABLE checkpoints ADD COLUMN lat REAL;
ALTER TABLE checkpoints ADD COLUMN lng REAL;

-- No-go zones: add GeoJSON boundary for geo-fencing
ALTER TABLE no_go_zones ADD COLUMN boundary_geojson TEXT;

-- Spatial index for incident proximity queries (risk_engine.py)
CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents(lat, lng);

-- Spatial index for checkpoint proximity queries (risk_engine.py)
CREATE INDEX IF NOT EXISTS idx_checkpoints_location ON checkpoints(lat, lng);
