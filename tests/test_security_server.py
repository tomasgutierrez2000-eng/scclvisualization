"""Tests for the Security MCP Server: data fusion and threat assessment."""
import pytest

from agents.servers.security_server import (
    fuse_intel,
    get_state_threat_level,
    get_no_go_zones,
    get_recent_incidents,
    assess_route_segment_risk,
    get_analyst_notes,
    _highest_risk,
)


def test_highest_risk():
    assert _highest_risk("LOW", "MEDIUM") == "MEDIUM"
    assert _highest_risk("LOW", "CRITICAL") == "CRITICAL"
    assert _highest_risk("HIGH", "MEDIUM") == "HIGH"
    assert _highest_risk() == "CRITICAL"  # No data = CRITICAL


def test_fuse_intel_threat_level():
    result = fuse_intel("DC", "threat_level")
    assert result.sources_consulted  # At least one source returned data
    assert "internal" in result.data
    assert not result.is_gap


def test_fuse_intel_no_go_zones():
    result = fuse_intel("ZU", "no_go_zones")
    assert not result.is_gap
    zones = result.data.get("internal", [])
    assert len(zones) > 0  # Zulia has seeded no-go zones


def test_fuse_intel_analyst_notes_delimiter():
    """Analyst notes should be wrapped in delimiters for injection defense."""
    result = fuse_intel("ZU", "analyst_notes")
    notes = result.data.get("internal", [])
    # If there are notes (from earlier portal test), they should be wrapped
    for note in notes:
        assert "[ANALYST NOTE" in note["text"]
        assert "[END ANALYST NOTE]" in note["text"]


def test_get_state_threat_level_batch():
    """Batch query multiple states."""
    result = get_state_threat_level(["DC", "ZU", "AR"])
    assert "DC" in result
    assert "ZU" in result
    assert "AR" in result
    assert result["DC"]["overall_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_get_state_threat_level_unknown_state():
    """Unknown state should return CRITICAL (conservative)."""
    result = get_state_threat_level(["XX"])
    assert result["XX"]["overall_level"] == "CRITICAL"
    # External stub always returns data, so is_gap won't be True.
    # The key assertion: unknown states default to CRITICAL.


def test_get_no_go_zones_batch():
    result = get_no_go_zones(["ZU", "AP", "DC"])
    assert result["ZU"]["has_no_go_zones"]
    assert result["AP"]["has_no_go_zones"]


def test_assess_route_segment_risk():
    states = ["DC", "MI", "AR", "CA"]
    result = assess_route_segment_risk(states)
    assert result["overall_risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert result["route_risk_score"] > 0
    assert result["states_assessed"] == 4
    assert len(result["per_state"]) == 4


def test_assess_route_with_critical_state():
    """Route through Apure (CRITICAL) should flag it."""
    states = ["DC", "GU", "AP"]
    result = assess_route_segment_risk(states)
    assert result["overall_risk_level"] in ("HIGH", "CRITICAL")
    # AP has no-go zones, so it may be flagged
    ap_assessment = next(s for s in result["per_state"] if s["state_id"] == "AP")
    assert ap_assessment["risk_level"] == "CRITICAL"
