"""Train search filter model."""

from pydantic import BaseModel, field_validator

from rail.models.indian_railways.base import Quota, SortBy, TrainClass


class TrainSearchFilters(BaseModel):
    """Filters for searching trains between two stations on a given date."""

    origin: str  # Station code, e.g. "NDLS"
    destination: str  # Station code, e.g. "BCT"
    departure_date: str  # YYYY-MM-DD
    train_class: TrainClass | None = None  # None = all classes
    quota: Quota = Quota.GENERAL
    sort_by: SortBy = SortBy.DEPARTURE_TIME

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
