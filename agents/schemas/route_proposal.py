"""RouteProposal: output from the Route Planner agent."""
from pydantic import BaseModel, Field


class RouteSegment(BaseModel):
    """A single segment of a route between two points."""
    from_location: str = Field(description="Origin of this segment")
    to_location: str = Field(description="Destination of this segment")
    distance_km: float = Field(description="Distance in kilometers")
    estimated_hours: float = Field(description="Estimated travel time in hours")
    states_traversed: list[str] = Field(description="State IDs this segment passes through")
    road_condition: str = Field(default="unknown", description="Road condition: good, fair, poor, unknown")
    known_issues: list[str] = Field(default_factory=list, description="Known issues on this segment")


class Route(BaseModel):
    """A complete route from origin to destination."""
    segments: list[RouteSegment] = Field(description="Ordered list of route segments")
    total_distance_km: float = Field(description="Total distance in kilometers")
    total_estimated_hours: float = Field(description="Total estimated travel time")
    total_days: int = Field(description="Recommended number of travel days")
    states_traversed: list[str] = Field(description="All unique state IDs on this route, in order")


class RouteProposal(BaseModel):
    """Complete route proposal from the Route Planner agent."""
    primary_route: Route = Field(description="Recommended primary route")
    alternatives: list[Route] = Field(default_factory=list, description="Alternative routes (up to 2)")
    route_rationale: str = Field(description="Explanation of why this route was chosen")
    user_route_respected: bool = Field(default=True, description="Whether user's preferred route was used")
    avoid_states_applied: list[str] = Field(default_factory=list, description="States excluded from routing")
