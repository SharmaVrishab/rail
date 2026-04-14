"""Seat availability filter model."""

from pydantic import BaseModel, field_validator

from rail.models.indian_railways.base import Quota, TrainClass


class AvailabilityFilters(BaseModel):
    """Filters for checking seat availability on a specific train."""

    train_number: str  # e.g. "12951"
    origin: str  # Boarding station code
    destination: str  # De-boarding station code
    departure_date: str  # YYYY-MM-DD
    train_class: TrainClass
    quota: Quota = Quota.GENERAL

    @field_validator("origin", "destination", mode="before")
    @classmethod
    def uppercase_station(cls, v: str) -> str:
        """Normalize station code to uppercase.

        Args:
            v: Raw station code string.

        Returns:
            Uppercased station code.
        """
        return v.strip().upper()

    @field_validator("train_number", mode="before")
    @classmethod
    def strip_train_number(cls, v: str) -> str:
        """Strip whitespace from train number.

        Args:
            v: Raw train number string.

        Returns:
            Stripped train number.
        """
        return str(v).strip()
