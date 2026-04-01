"""Tests for the deterministic Python orchestrator."""
import pytest

from tourism.orchestrator import parse_intake_simple, plan_route, assess_security, run_pipeline
from tourism.schemas import ClientRequest


class TestIntakeParsing:
    def test_basic_format(self):
        req = parse_intake_simple("Caracas to Maracaibo, 3 days")
        assert req.origin == "Caracas"
        assert req.destination == "Maracaibo"
        assert req.num_days == 3

    def test_plan_trip_prefix(self):
        req = parse_intake_simple("Plan a trip from Valencia to San Cristobal")
        assert req.origin == "Valencia"
        assert req.destination == "San Cristobal"

    def test_no_days(self):
        req = parse_intake_simple("Caracas to Valencia")
        assert req.origin == "Caracas"
        assert req.destination == "Valencia"
        assert req.num_days is None

    def test_invalid_input(self):
        with pytest.raises(ValueError):
            parse_intake_simple("hello world")


class TestPlanRoute:
    def test_basic_route(self):
        req = ClientRequest(origin="Caracas", destination="Maracaibo")
        proposal = plan_route(req)
        assert proposal.primary_route.total_distance_km > 0
        assert len(proposal.primary_route.states_traversed) > 2
        assert "DC" in proposal.primary_route.states_traversed
        assert "ZU" in proposal.primary_route.states_traversed

    def test_route_with_avoid(self):
        req = ClientRequest(origin="Caracas", destination="Maracaibo", avoid_states=["TR"])
        proposal = plan_route(req)
        assert "TR" not in proposal.primary_route.states_traversed
        assert "TR" in proposal.avoid_states_applied

    def test_impossible_route(self):
        req = ClientRequest(origin="Caracas", destination="Atlantis")
        with pytest.raises(RuntimeError, match="Route planning failed"):
            plan_route(req)


class TestAssessSecurity:
    def test_basic_assessment(self):
        briefing = assess_security(["DC", "MI", "AR"])
        assert briefing.overall_risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert len(briefing.state_assessments) == 3
        assert briefing.briefing_timestamp

    def test_high_risk_state(self):
        briefing = assess_security(["AP"])
        ap = briefing.state_assessments[0]
        assert ap.risk_level == "CRITICAL"

    def test_recommendations_generated(self):
        briefing = assess_security(["DC", "ZU"])
        assert len(briefing.recommendations) > 0


class TestFullPipeline:
    def test_end_to_end(self):
        result = run_pipeline("Caracas to Maracaibo, 3 days")
        assert result["route_proposal"] is not None
        assert result["security_briefing"] is not None
        assert result["route_proposal"].primary_route.total_distance_km > 0

    def test_short_trip(self):
        result = run_pipeline("Caracas to Valencia")
        assert result["route_proposal"].primary_route.total_days >= 1
