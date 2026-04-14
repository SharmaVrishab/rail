"""Tests for rail.core.parsers."""

import pytest

from rail.core.parsers import (
    ParseError,
    parse_quota,
    parse_sort_by,
    parse_time_range,
    parse_train_class,
    resolve_station,
)
from rail.models.indian_railways.base import Quota, SortBy, TrainClass


# ---------------------------------------------------------------------------
# resolve_station
# ---------------------------------------------------------------------------

class TestResolveStation:
    def test_uppercase_passthrough(self):
        assert resolve_station("NDLS") == "NDLS"

    def test_lowercase_uppercased(self):
        assert resolve_station("ndls") == "NDLS"

    def test_whitespace_stripped(self):
        assert resolve_station("  BCT  ") == "BCT"

    def test_empty_raises(self):
        with pytest.raises(ParseError):
            resolve_station("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ParseError):
            resolve_station("   ")


# ---------------------------------------------------------------------------
# parse_train_class
# ---------------------------------------------------------------------------

class TestParseTrainClass:
    @pytest.mark.parametrize("raw, expected", [
        ("SL", TrainClass.SL),
        ("sl", TrainClass.SL),
        ("sleeper", TrainClass.SL),
        ("3A", TrainClass.THREE_AC),
        ("3a", TrainClass.THREE_AC),
        ("3AC", TrainClass.THREE_AC),
        ("2A", TrainClass.TWO_AC),
        ("1A", TrainClass.ONE_AC),
        ("CC", TrainClass.CC),
        ("EC", TrainClass.EC),
        ("2S", TrainClass.SECOND_SITTING),
        ("FC", TrainClass.FC),
        ("FIRST", TrainClass.FC),
        ("executive", TrainClass.EC),
    ])
    def test_valid_aliases(self, raw, expected):
        assert parse_train_class(raw) == expected

    def test_invalid_raises(self):
        with pytest.raises(ParseError):
            parse_train_class("XYZ")

    def test_empty_raises(self):
        with pytest.raises(ParseError):
            parse_train_class("")


# ---------------------------------------------------------------------------
# parse_quota
# ---------------------------------------------------------------------------

class TestParseQuota:
    @pytest.mark.parametrize("raw, expected", [
        ("GN", Quota.GENERAL),
        ("gn", Quota.GENERAL),
        ("general", Quota.GENERAL),
        ("TQ", Quota.TATKAL),
        ("tatkal", Quota.TATKAL),
        ("PT", Quota.PREMIUM_TATKAL),
        ("premium", Quota.PREMIUM_TATKAL),
        ("LD", Quota.LADIES),
        ("ladies", Quota.LADIES),
        ("SS", Quota.SENIOR_CITIZEN),
        ("senior", Quota.SENIOR_CITIZEN),
        ("HP", Quota.DIVYAANG),
        ("divyaang", Quota.DIVYAANG),
    ])
    def test_valid_aliases(self, raw, expected):
        assert parse_quota(raw) == expected

    def test_invalid_raises(self):
        with pytest.raises(ParseError):
            parse_quota("UNKNOWN")


# ---------------------------------------------------------------------------
# parse_sort_by
# ---------------------------------------------------------------------------

class TestParseSortBy:
    @pytest.mark.parametrize("raw, expected", [
        ("DEP", SortBy.DEPARTURE_TIME),
        ("dep", SortBy.DEPARTURE_TIME),
        ("departure", SortBy.DEPARTURE_TIME),
        ("ARR", SortBy.ARRIVAL_TIME),
        ("arrival", SortBy.ARRIVAL_TIME),
        ("DUR", SortBy.DURATION),
        ("duration", SortBy.DURATION),
        ("AVAIL", SortBy.AVAILABILITY),
        ("availability", SortBy.AVAILABILITY),
    ])
    def test_valid_aliases(self, raw, expected):
        assert parse_sort_by(raw) == expected

    def test_invalid_raises(self):
        with pytest.raises(ParseError):
            parse_sort_by("PRICE")


# ---------------------------------------------------------------------------
# parse_time_range
# ---------------------------------------------------------------------------

class TestParseTimeRange:
    def test_basic(self):
        assert parse_time_range("06-22") == (6, 22)

    def test_zero_padded(self):
        assert parse_time_range("00-23") == (0, 23)

    def test_invalid_format_raises(self):
        with pytest.raises(ParseError):
            parse_time_range("06:22")

    def test_non_integer_raises(self):
        with pytest.raises(ParseError):
            parse_time_range("aa-bb")

    def test_out_of_range_raises(self):
        with pytest.raises(ParseError):
            parse_time_range("0-25")
