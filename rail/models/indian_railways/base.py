"""Base enums and result models for Indian Railways."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TrainClass(str, Enum):
    """Train coach/class types on Indian Railways."""

    SL = "SL"  # Sleeper Class
    THREE_AC = "3A"  # 3-Tier AC
    TWO_AC = "2A"  # 2-Tier AC
    ONE_AC = "1A"  # 1st Class AC
    CC = "CC"  # AC Chair Car
    EC = "EC"  # Executive Chair Car
    SECOND_SITTING = "2S"  # 2nd Sitting (non-AC)
    FC = "FC"  # First Class (non-AC)


class Quota(str, Enum):
    """Booking quota types on Indian Railways."""

    GENERAL = "GN"
    TATKAL = "TQ"
    PREMIUM_TATKAL = "PT"
    LADIES = "LD"
    SENIOR_CITIZEN = "SS"
    DIVYAANG = "HP"  # Physically Handicapped
    YOUTH = "YU"
    DEFENCE = "DF"


class SortBy(str, Enum):
    """Sort options for train search results."""

    DEPARTURE_TIME = "DEP"
    ARRIVAL_TIME = "ARR"
    DURATION = "DUR"
    AVAILABILITY = "AVAIL"


class TrainResult(BaseModel):
    """A single train found between two stations."""

    train_number: str
    train_name: str
    departure_station: str  # Station code, e.g. "NDLS"
    arrival_station: str
    departure_time: str  # "HH:MM" 24-hour
    arrival_time: str
    duration: int  # Total journey duration in minutes
    distance: int  # Distance in km
    classes: list[TrainClass]  # Classes available on this train
    days_of_run: list[str]  # e.g. ["Mon", "Wed", "Fri"] or ["Daily"]


class SeatAvailability(BaseModel):
    """Seat availability for a specific class and quota on a train."""

    train_class: TrainClass
    quota: Quota
    status: str  # e.g. "AVAILABLE-42", "RAC-1", "WL-5", "REGRET", "NOT AVAILABLE"
    available_count: int | None = None  # Numeric seats available when known
    fare: float | None = None
    currency: str = "INR"


class PNRStatus(BaseModel):
    """PNR booking status details."""

    pnr_number: str
    train_number: str
    train_name: str
    journey_date: str  # YYYY-MM-DD
    from_station: str  # Station code
    to_station: str
    train_class: str
    quota: str
    passengers: list[dict]  # [{seat_number, booking_status, current_status, coach}]
    chart_prepared: bool
    boarding_station: str | None = None


class LiveStatus(BaseModel):
    """Real-time running status of a train."""

    train_number: str
    train_name: str
    current_station: str  # Station code
    current_station_name: str
    delay_minutes: int  # Positive = late, 0 = on time, negative = early
    last_updated: datetime
    next_station: str | None = None
    next_station_name: str | None = None
    expected_arrival_next: datetime | None = None
    distance_from_source: int | None = None  # km from origin


class DateAvailability(BaseModel):
    """Seat availability summary for a specific date."""

    date: str  # YYYY-MM-DD
    train_number: str
    train_name: str
    train_class: TrainClass
    quota: Quota
    status: str  # "AVAILABLE", "RAC", "WL", "REGRET", "NOT AVAILABLE"
    available_count: int | None = None
    fare: float | None = None
    currency: str = "INR"
