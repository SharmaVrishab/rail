"""Shared builder utilities for constructing search filter objects.

Used by both the CLI and MCP server to assemble TrainSearchFilters and
AvailabilityFilters from parsed user input.
"""

from datetime import datetime

from rail.models.indian_railways.availability import AvailabilityFilters
from rail.models.indian_railways.base import Quota, SortBy, TrainClass
from rail.models.indian_railways.trains import TrainSearchFilters


def normalize_date(date_str: str) -> str:
    """Normalise a date string to YYYY-MM-DD format.

    Accepts common formats: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, YYYYMMDD.

    Args:
        date_str: Raw date string from user input.

    Returns:
        Date string in 'YYYY-MM-DD' format.

    Raises:
        ValueError: If the date cannot be parsed.
    """
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y%m%d",
        "%d-%b-%Y",  # e.g. 15-Jun-2025
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(
        f"Cannot parse date '{date_str}'. Use YYYY-MM-DD format."
    )


def build_train_search(
    origin: str,
    destination: str,
    departure_date: str,
    train_class: TrainClass | None = None,
    quota: Quota = Quota.GENERAL,
    sort_by: SortBy = SortBy.DEPARTURE_TIME,
) -> TrainSearchFilters:
    """Construct a TrainSearchFilters object from individual parameters.

    Args:
        origin: Origin station code (e.g. "NDLS").
        destination: Destination station code (e.g. "BCT").
        departure_date: Journey date in any supported format.
        train_class: Optional class filter (None = all classes).
        quota: Booking quota (default: GENERAL).
        sort_by: Sort order for results (default: DEPARTURE_TIME).

    Returns:
        Constructed TrainSearchFilters instance.
    """
    return TrainSearchFilters(
        origin=origin,
        destination=destination,
        departure_date=normalize_date(departure_date),
        train_class=train_class,
        quota=quota,
        sort_by=sort_by,
    )


def build_availability_search(
    train_number: str,
    origin: str,
    destination: str,
    departure_date: str,
    train_class: TrainClass,
    quota: Quota = Quota.GENERAL,
) -> AvailabilityFilters:
    """Construct an AvailabilityFilters object from individual parameters.

    Args:
        train_number: Train number (e.g. "12951").
        origin: Boarding station code.
        destination: De-boarding station code.
        departure_date: Journey date in any supported format.
        train_class: Coach class to check.
        quota: Booking quota (default: GENERAL).

    Returns:
        Constructed AvailabilityFilters instance.
    """
    return AvailabilityFilters(
        train_number=train_number,
        origin=origin,
        destination=destination,
        departure_date=normalize_date(departure_date),
        train_class=train_class,
        quota=quota,
    )
