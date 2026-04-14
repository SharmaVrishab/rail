"""Tests for the Station enum."""

import pytest

from rail.models.station import Station


def test_station_enum_exists():
    """Station enum should have members."""
    assert len(Station) > 0


def test_known_stations_present():
    """Major Indian Railway station codes must exist in the enum."""
    codes = ["NDLS", "BCT", "HWH", "MAS", "SBC", "HYB", "PUNE", "ADI", "LKO"]
    for code in codes:
        assert hasattr(Station, code), f"Station {code} not found in enum"


def test_station_value_is_string():
    """Station enum values should be non-empty strings (human-readable names)."""
    assert isinstance(Station.NDLS.value, str)
    assert len(Station.NDLS.value) > 0


def test_station_str_enum():
    """Station should behave as a str enum."""
    assert Station.NDLS == Station.NDLS
