"""Shared parsing utilities for converting user input into domain models.

Used by both the CLI and MCP server to normalise station codes, class names,
quota types, sort options, and time ranges.
"""

from rail.models.indian_railways.base import Quota, SortBy, TrainClass


class ParseError(ValueError):
    """Raised when a user-supplied value cannot be resolved to a domain model."""


# ---------------------------------------------------------------------------
# Station
# ---------------------------------------------------------------------------

def resolve_station(code: str) -> str:
    """Validate and normalise an Indian Railways station code.

    Args:
        code: Raw station code (case-insensitive), e.g. "ndls", "BCT".

    Returns:
        Uppercased station code string.

    Raises:
        ParseError: If the code is empty after stripping.
    """
    code = code.strip().upper()
    if not code:
        raise ParseError("Station code cannot be empty.")
    return code


# ---------------------------------------------------------------------------
# Train class
# ---------------------------------------------------------------------------

# Aliases let users type natural names in addition to official codes
_CLASS_ALIASES: dict[str, TrainClass] = {
    # Official codes
    "SL": TrainClass.SL,
    "3A": TrainClass.THREE_AC,
    "2A": TrainClass.TWO_AC,
    "1A": TrainClass.ONE_AC,
    "CC": TrainClass.CC,
    "EC": TrainClass.EC,
    "2S": TrainClass.SECOND_SITTING,
    "FC": TrainClass.FC,
    # Natural language aliases
    "SLEEPER": TrainClass.SL,
    "SLEEPERCLASS": TrainClass.SL,
    "THREEAC": TrainClass.THREE_AC,
    "3AC": TrainClass.THREE_AC,
    "THIRDAC": TrainClass.THREE_AC,
    "TWOAC": TrainClass.TWO_AC,
    "2AC": TrainClass.TWO_AC,
    "SECONDAC": TrainClass.TWO_AC,
    "ONEAC": TrainClass.ONE_AC,
    "1AC": TrainClass.ONE_AC,
    "FIRSTAC": TrainClass.ONE_AC,
    "CHAIRCAR": TrainClass.CC,
    "ACCHAIR": TrainClass.CC,
    "EXECUTIVECHAIR": TrainClass.EC,
    "EXECUTIVE": TrainClass.EC,
    "SECONDSITTING": TrainClass.SECOND_SITTING,
    "SECOND": TrainClass.SECOND_SITTING,
    "FIRSTCLASS": TrainClass.FC,
    "FIRST": TrainClass.FC,
}


def parse_train_class(cls: str) -> TrainClass:
    """Resolve a string to a TrainClass enum member.

    Accepts official codes ("SL", "3A") and natural names ("sleeper", "3ac").

    Args:
        cls: Raw class string from the user.

    Returns:
        Matching TrainClass enum value.

    Raises:
        ParseError: If the string cannot be resolved.
    """
    key = cls.strip().upper().replace(" ", "").replace("-", "").replace("_", "")
    result = _CLASS_ALIASES.get(key)
    if result is None:
        valid = ", ".join(sorted({tc.value for tc in TrainClass}))
        raise ParseError(
            f"Unknown train class '{cls}'. Valid codes: {valid}"
        )
    return result


# ---------------------------------------------------------------------------
# Quota
# ---------------------------------------------------------------------------

_QUOTA_ALIASES: dict[str, Quota] = {
    "GN": Quota.GENERAL,
    "GENERAL": Quota.GENERAL,
    "TQ": Quota.TATKAL,
    "TATKAL": Quota.TATKAL,
    "PT": Quota.PREMIUM_TATKAL,
    "PREMIUMTATKAL": Quota.PREMIUM_TATKAL,
    "PREMIUM": Quota.PREMIUM_TATKAL,
    "LD": Quota.LADIES,
    "LADIES": Quota.LADIES,
    "LADY": Quota.LADIES,
    "SS": Quota.SENIOR_CITIZEN,
    "SENIOR": Quota.SENIOR_CITIZEN,
    "SENIORCITIZEN": Quota.SENIOR_CITIZEN,
    "HP": Quota.DIVYAANG,
    "DIVYAANG": Quota.DIVYAANG,
    "HANDICAPPED": Quota.DIVYAANG,
    "YU": Quota.YOUTH,
    "YOUTH": Quota.YOUTH,
    "DF": Quota.DEFENCE,
    "DEFENCE": Quota.DEFENCE,
    "DEFENSE": Quota.DEFENCE,
}


def parse_quota(quota: str) -> Quota:
    """Resolve a string to a Quota enum member.

    Args:
        quota: Raw quota string, e.g. "GN", "tatkal", "Senior".

    Returns:
        Matching Quota enum value.

    Raises:
        ParseError: If the string cannot be resolved.
    """
    key = quota.strip().upper().replace(" ", "").replace("-", "").replace("_", "")
    result = _QUOTA_ALIASES.get(key)
    if result is None:
        valid = ", ".join(sorted({q.value for q in Quota}))
        raise ParseError(
            f"Unknown quota '{quota}'. Valid codes: {valid}"
        )
    return result


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------

_SORT_ALIASES: dict[str, SortBy] = {
    "DEP": SortBy.DEPARTURE_TIME,
    "DEPARTURE": SortBy.DEPARTURE_TIME,
    "DEPARTURETIME": SortBy.DEPARTURE_TIME,
    "ARR": SortBy.ARRIVAL_TIME,
    "ARRIVAL": SortBy.ARRIVAL_TIME,
    "ARRIVALTIME": SortBy.ARRIVAL_TIME,
    "DUR": SortBy.DURATION,
    "DURATION": SortBy.DURATION,
    "TIME": SortBy.DURATION,
    "AVAIL": SortBy.AVAILABILITY,
    "AVAILABILITY": SortBy.AVAILABILITY,
}


def parse_sort_by(sort: str) -> SortBy:
    """Resolve a string to a SortBy enum member.

    Args:
        sort: Sort preference string, e.g. "DEP", "duration", "arrival".

    Returns:
        Matching SortBy value.

    Raises:
        ParseError: If the string cannot be resolved.
    """
    key = sort.strip().upper().replace(" ", "").replace("-", "").replace("_", "")
    result = _SORT_ALIASES.get(key)
    if result is None:
        valid = "DEP, ARR, DUR, AVAIL"
        raise ParseError(f"Unknown sort option '{sort}'. Valid options: {valid}")
    return result


# ---------------------------------------------------------------------------
# Time range
# ---------------------------------------------------------------------------

def parse_time_range(time_range: str) -> tuple[int, int]:
    """Parse a departure/arrival time window in 'HH-HH' format.

    Args:
        time_range: A string like "06-22" representing a window from 06:00
            to 22:00 in 24-hour format.

    Returns:
        A (start_hour, end_hour) tuple, both in [0, 23].

    Raises:
        ParseError: If the format is invalid or hours are out of range.
    """
    parts = time_range.strip().split("-")
    if len(parts) != 2:
        raise ParseError(
            f"Invalid time range '{time_range}'. Expected format: 'HH-HH' (e.g. '06-22')."
        )
    try:
        start, end = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ParseError(
            f"Invalid time range '{time_range}'. Hours must be integers."
        ) from exc

    if not (0 <= start <= 23 and 0 <= end <= 23):
        raise ParseError(
            f"Time range hours must be between 0 and 23, got {start}-{end}."
        )
    return start, end
