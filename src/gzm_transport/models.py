from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class VehiclePosition:
    timestamp: str
    line_name: str
    vehicle_id: str
    direction: str
    lat: float
    lon: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Departure:
    timestamp: str
    stop_id: int
    line_name: str
    destination: str
    departure_time: str
    is_live: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StopInfo:
    stop_id: int
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)