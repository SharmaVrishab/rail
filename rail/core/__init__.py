"""Core utilities for rail search operations.

Provides shared parsing and building utilities used by both the CLI
and MCP interfaces.
"""

from rail.core.builders import (
    build_availability_search,
    build_train_search,
    normalize_date,
)
from rail.core.parsers import (
    ParseError,
    parse_quota,
    parse_sort_by,
    parse_time_range,
    parse_train_class,
    resolve_station,
)

__all__ = [
    # Parsers
    "resolve_station",
    "parse_train_class",
    "parse_quota",
    "parse_sort_by",
    "parse_time_range",
    "ParseError",
    # Builders
    "normalize_date",
    "build_train_search",
    "build_availability_search",
]
