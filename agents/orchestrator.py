"""Deterministic Python orchestrator for the trip planning pipeline.

This is plain Python, NOT an LLM agent. Only the initial intake parsing
uses an LLM call. The reroute loop and agent coordination are deterministic.

Pipeline:
    User input (natural language)
        │
        ▼
    parse_intake() ──► Sonnet LLM call ──► ClientRequest
        │
        ▼
    plan_route() ──► Geo MCP Server ──► RouteProposal
        │
        ▼
    assess_security() ──► Security MCP Server ──► SecurityBriefing
        │
        ├── if no_go_states: reroute loop (max 3)
        │
        ▼
    generate_outputs() ──► Heat Map HTML
        │
        ▼
    Return (RouteProposal, SecurityBriefing)
"""
import json
import sys
from datetime import datetime, timezone

from .schemas import ClientRequest, RouteProposal, SecurityBriefing, StateAssessment
from .schemas.security_briefing import ThreatBreakdown
from .servers.geo_server import calculate_route, geocode_location
from .servers.security_server import (
    assess_route_segment_risk,
    get_analyst_notes,
    get_no_go_zones,
    get_recent_incidents,
    get_state_threat_level,
)

MAX_REROUTE_ATTEMPTS = 3


def parse_intake_simple(user_input: str) -> ClientRequest:
    """Parse natural language trip request into structured ClientRequest.

    This is a simple rule-based parser for Phase 1. In production, this would
    be a single Sonnet LLM call with output_type=ClientRequest.
    """
    # Simple keyword extraction for MVP
    words = user_input.lower().strip()

    # Try to extract "X to Y" pattern
    origin = None
    destination = None
    num_days = None

    if " to " in words:
        parts = words.split(" to ", 1)
        # Origin is the last significant word(s) before "to"
        origin_part = parts[0].strip()
        # Remove common prefixes
        for prefix in ["plan a trip from", "plan trip from", "trip from", "from", "plan"]:
            if origin_part.startswith(prefix):
                origin_part = origin_part[len(prefix):].strip()
                break
        origin = origin_part.strip().rstrip(",").strip()

        dest_part = parts[1].strip()
        # Extract days if present
        for token in dest_part.split(","):
            token = token.strip()
            if "day" in token:
                for word in token.split():
                    if word.isdigit():
                        num_days = int(word)
                        break
            elif not destination:
                destination = token.strip()

    if not origin or not destination:
        # Fallback: try comma-separated
        parts = [p.strip() for p in user_input.split(",")]
        if len(parts) >= 2:
            origin = parts[0]
            destination = parts[1]
            if len(parts) >= 3 and "day" in parts[2].lower():
                for word in parts[2].split():
                    if word.isdigit():
                        num_days = int(word)

    if not origin or not destination:
        raise ValueError(f"Could not parse origin and destination from: {user_input}")

    # Capitalize city names
    origin = origin.title()
    destination = destination.title()

    return ClientRequest(
        origin=origin,
        destination=destination,
        num_days=num_days,
    )


def plan_route(request: ClientRequest) -> RouteProposal:
    """Invoke the Geo MCP Server to plan a route."""
    route_data = calculate_route(
        origin=request.origin,
        destination=request.destination,
        waypoints=request.waypoints or None,
        avoid_states=request.avoid_states or None,
    )

    if "error" in route_data:
        raise RuntimeError(f"Route planning failed: {route_data['error']}")

    from .schemas.route_proposal import RouteSegment, Route

    segments = [
        RouteSegment(
            from_location=s["from_location"],
            to_location=s["to_location"],
            distance_km=s["distance_km"],
            estimated_hours=s["estimated_hours"],
            states_traversed=s["states_traversed"],
            road_condition=s.get("road_condition", "unknown"),
            known_issues=s.get("known_issues", []),
        )
        for s in route_data["segments"]
    ]

    primary_route = Route(
        segments=segments,
        total_distance_km=route_data["total_distance_km"],
        total_estimated_hours=route_data["total_estimated_hours"],
        total_days=route_data["total_days"],
        states_traversed=route_data["states_traversed"],
    )

    return RouteProposal(
        primary_route=primary_route,
        route_rationale=f"Shortest path via state adjacency graph, {len(segments)} segments",
        avoid_states_applied=request.avoid_states,
    )


def assess_security(states: list[str]) -> SecurityBriefing:
    """Invoke the Security MCP Server to assess all states on the route."""
    risk = assess_route_segment_risk(states)
    threats = get_state_threat_level(states)
    no_go = get_no_go_zones(states)
    incidents = get_recent_incidents(states)
    notes = get_analyst_notes(states)

    state_assessments = []
    no_go_states = []

    for state_id in states:
        threat = threats.get(state_id, {})
        zones = no_go.get(state_id, {})
        state_incidents = incidents.get(state_id, {})
        state_notes = notes.get(state_id, {})

        is_no_go = any(s["is_no_go"] for s in risk.get("per_state", []) if s["state_id"] == state_id)
        if is_no_go:
            no_go_states.append(state_id)

        # Map security posture from risk level
        posture_map = {"LOW": "standard", "MEDIUM": "elevated", "HIGH": "high", "CRITICAL": "maximum"}

        level = threat.get("overall_level", "CRITICAL")

        state_assessments.append(StateAssessment(
            state_id=state_id,
            state_name=state_id,  # Could resolve to full name
            risk_level=level,
            threat_breakdown=ThreatBreakdown(
                crime=threat.get("crime", "CRITICAL"),
                political=threat.get("political", "CRITICAL"),
                infrastructure=threat.get("infrastructure", "CRITICAL"),
                natural_hazards=threat.get("natural_hazards", "CRITICAL"),
            ),
            no_go_zones=[z["zone_name"] for z in zones.get("zones", [])],
            recent_incidents=[
                f"{i['incident_type']}: {i.get('description', 'No details')}"
                for i in state_incidents.get("incidents", [])[:3]
            ],
            recommended_security_posture=posture_map.get(level, "maximum"),
            intelligence_freshness=threat.get("freshness"),
            intelligence_gaps=["No analyst notes" if not state_notes.get("notes") else ""],
            is_no_go=is_no_go,
        ))

    return SecurityBriefing(
        overall_risk_level=risk["overall_risk_level"],
        route_risk_score=risk["route_risk_score"],
        state_assessments=state_assessments,
        no_go_states=no_go_states,
        recommendations=_generate_recommendations(state_assessments),
        briefing_timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _generate_recommendations(assessments: list[StateAssessment]) -> list[str]:
    """Generate actionable recommendations based on state assessments."""
    recs = []
    for a in assessments:
        if a.risk_level == "CRITICAL":
            recs.append(f"AVOID {a.state_id} if possible. Risk level: CRITICAL.")
        elif a.risk_level == "HIGH":
            recs.append(f"Exercise extreme caution in {a.state_id}. Avoid night travel.")
        if a.no_go_zones:
            recs.append(f"No-go zones in {a.state_id}: {', '.join(a.no_go_zones)}")
        if a.intelligence_gaps and a.intelligence_gaps[0]:
            recs.append(f"Intelligence gap for {a.state_id}: recommend fresh analyst assessment.")
    return recs


def run_pipeline(user_input: str, client_id: str = "default") -> dict:
    """Run the full planning pipeline: intake -> route -> security -> reroute loop.

    Args:
        user_input: Natural language trip request
        client_id: Client identifier

    Returns:
        Dict with route_proposal, security_briefing, and metadata.
    """
    print(f"[1/4] Parsing trip request...")
    request = parse_intake_simple(user_input)
    request.client_id = client_id
    print(f"       Origin: {request.origin} -> Destination: {request.destination}")
    if request.num_days:
        print(f"       Days: {request.num_days}")

    print(f"\n[2/4] Planning route...")
    route_proposal = plan_route(request)
    states = route_proposal.primary_route.states_traversed
    print(f"       Route: {' -> '.join(states)}")
    print(f"       Distance: {route_proposal.primary_route.total_distance_km}km")
    print(f"       Days: {route_proposal.primary_route.total_days}")

    print(f"\n[3/4] Assessing security for {len(states)} states...")
    security_briefing = assess_security(states)

    # Reroute loop (deterministic)
    avoid_states = list(request.avoid_states)
    for attempt in range(MAX_REROUTE_ATTEMPTS):
        if security_briefing.no_go_states:
            new_no_go = [s for s in security_briefing.no_go_states if s not in avoid_states]
            if not new_no_go:
                break
            avoid_states = list(set(avoid_states + security_briefing.no_go_states))
            print(f"\n[!] Reroute attempt {attempt + 1}: avoiding {avoid_states}")

            request.avoid_states = avoid_states
            route_proposal = plan_route(request)
            states = route_proposal.primary_route.states_traversed
            print(f"    New route: {' -> '.join(states)}")

            security_briefing = assess_security(states)
        else:
            break
    else:
        if security_briefing.no_go_states:
            print("\n[!!] WARNING: No safe route found after 3 reroute attempts.")
            print("     Consider air transport or postponing the trip.")

    # Print summary
    print(f"\n[4/4] Results:")
    print(f"       Overall risk: {security_briefing.overall_risk_level}")
    print(f"       Risk score: {security_briefing.route_risk_score}/10")
    print(f"       No-go states: {security_briefing.no_go_states or 'None'}")
    print(f"\n       Per-state assessment:")
    for a in security_briefing.state_assessments:
        flag = " [NO-GO]" if a.is_no_go else ""
        stale = " [STALE]" if a.intelligence_freshness and "gap" in str(a.intelligence_gaps) else ""
        print(f"         {a.state_id}: {a.risk_level} -> {a.recommended_security_posture}{flag}{stale}")

    if security_briefing.recommendations:
        print(f"\n       Recommendations:")
        for rec in security_briefing.recommendations:
            print(f"         - {rec}")

    return {
        "route_proposal": route_proposal,
        "security_briefing": security_briefing,
        "client_id": client_id,
        "reroutes": len(avoid_states) > len(request.avoid_states or []),
    }
