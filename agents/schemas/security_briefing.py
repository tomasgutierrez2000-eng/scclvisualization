"""SecurityBriefing: output from the Security Briefing agent."""
from pydantic import BaseModel, Field


class ThreatBreakdown(BaseModel):
    crime: str = Field(description="Crime threat level: LOW, MEDIUM, HIGH, CRITICAL")
    political: str = Field(description="Political instability level")
    infrastructure: str = Field(description="Infrastructure risk level")
    natural_hazards: str = Field(description="Natural hazard risk level")


class StateAssessment(BaseModel):
    """Security assessment for a single Venezuelan state."""
    state_id: str = Field(description="State identifier (e.g., 'ZU' for Zulia)")
    state_name: str = Field(description="Full state name")
    risk_level: str = Field(description="Overall risk: LOW, MEDIUM, HIGH, CRITICAL")
    threat_breakdown: ThreatBreakdown = Field(description="Per-category threat breakdown")
    no_go_zones: list[str] = Field(default_factory=list, description="Areas to avoid within this state")
    recent_incidents: list[str] = Field(default_factory=list, description="Summary of recent incidents")
    recommended_security_posture: str = Field(description="Recommended posture: standard, elevated, high, maximum")
    intelligence_freshness: str | None = Field(default=None, description="Date of most recent intel (ISO format)")
    intelligence_gaps: list[str] = Field(default_factory=list, description="Known gaps in intelligence coverage")
    is_no_go: bool = Field(default=False, description="True if this state should be avoided entirely")


class SecurityBriefing(BaseModel):
    """Complete security briefing for a planned route."""
    overall_risk_level: str = Field(description="Overall route risk: LOW, MEDIUM, HIGH, CRITICAL")
    route_risk_score: float = Field(description="Numeric risk score 1-10 (1=lowest, 10=highest)")
    state_assessments: list[StateAssessment] = Field(description="Per-state security assessments")
    no_go_states: list[str] = Field(default_factory=list, description="State IDs that should be avoided entirely")
    recommendations: list[str] = Field(default_factory=list, description="Actionable security recommendations")
    briefing_timestamp: str = Field(description="When this briefing was generated (ISO datetime)")
