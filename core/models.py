from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional


@dataclass
class ApiConfig:
    """Stores API configuration."""
    client_id: str
    client_secret: str
    api_token: str
    refresh_token: str = ""


@dataclass
class Location:
    """Represents a location for reporting."""
    name: str
    region: str
    selected: bool = False


@dataclass
class ReportParams:
    """Parameters for generating a report."""
    date_from: date
    date_to: date
    counter_id: str
    grouping: str
    traffic_sources: Dict[str, bool]
    behavior: str
    locations: List[Location]


@dataclass
class ReportData:
    """Stores processed report data."""
    location: Location
    date: date
    visits: int
    users: int
    pageviews: int
    traffic_source: Optional[str] = None
    bounce_rate: Optional[float] = None
    page_depth: Optional[float] = None
    avg_visit_duration: Optional[float] = None