"""ClientRequest: structured input extracted from natural language trip request."""
from pydantic import BaseModel, Field


class ClientRequest(BaseModel):
    """Structured trip request extracted from user's natural language input."""
    origin: str = Field(description="Origin city or location name")
    destination: str = Field(description="Destination city or location name")
    waypoints: list[str] = Field(default_factory=list, description="Intermediate stops")
    start_date: str | None = Field(default=None, description="Trip start date (YYYY-MM-DD)")
    end_date: str | None = Field(default=None, description="Trip end date (YYYY-MM-DD)")
    num_days: int | None = Field(default=None, description="Number of travel days")
    num_passengers: int = Field(default=1, description="Number of passengers")
    preferred_route: str | None = Field(default=None, description="User-specified route preference")
    vehicle_preference: str | None = Field(default=None, description="Vehicle type preference")
    client_id: str = Field(default="default", description="Client identifier for multi-tenancy")
    avoid_states: list[str] = Field(default_factory=list, description="States to avoid (populated during reroute)")
