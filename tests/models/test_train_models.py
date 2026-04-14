"""Tests for Indian Railways data models."""

import pytest

from rail.models.indian_railways.base import (
    DateAvailability,
    LiveStatus,
    PNRStatus,
    Quota,
    SeatAvailability,
    SortBy,
    TrainClass,
    TrainResult,
)
from rail.models.indian_railways.trains import TrainSearchFilters
from rail.models.indian_railways.availability import AvailabilityFilters


# ---------------------------------------------------------------------------
# TrainClass
# ---------------------------------------------------------------------------

class TestTrainClass:
    def test_all_classes_have_values(self):
        expected = {"SL", "3A", "2A", "1A", "CC", "EC", "2S", "FC"}
        actual = {tc.value for tc in TrainClass}
        assert expected == actual

    def test_sleeper_value(self):
        assert TrainClass.SL.value == "SL"

    def test_three_ac_value(self):
        assert TrainClass.THREE_AC.value == "3A"


# ---------------------------------------------------------------------------
# Quota
# ---------------------------------------------------------------------------

class TestQuota:
    def test_general_value(self):
        assert Quota.GENERAL.value == "GN"

    def test_tatkal_value(self):
        assert Quota.TATKAL.value == "TQ"

    def test_premium_tatkal_value(self):
        assert Quota.PREMIUM_TATKAL.value == "PT"


# ---------------------------------------------------------------------------
# TrainSearchFilters
# ---------------------------------------------------------------------------

class TestTrainSearchFilters:
    def test_basic_construction(self):
        f = TrainSearchFilters(
            origin="NDLS",
            destination="BCT",
            departure_date="2025-06-01",
        )
        assert f.origin == "NDLS"
        assert f.destination == "BCT"
        assert f.quota == Quota.GENERAL

    def test_station_codes_uppercased(self):
        f = TrainSearchFilters(
            origin="ndls",
            destination="bct",
            departure_date="2025-06-01",
        )
        assert f.origin == "NDLS"
        assert f.destination == "BCT"

    def test_with_class_filter(self):
        f = TrainSearchFilters(
            origin="NDLS",
            destination="MAS",
            departure_date="2025-06-01",
            train_class=TrainClass.SL,
        )
        assert f.train_class == TrainClass.SL

    def test_default_sort_is_departure(self):
        f = TrainSearchFilters(origin="NDLS", destination="BCT", departure_date="2025-06-01")
        assert f.sort_by == SortBy.DEPARTURE_TIME


# ---------------------------------------------------------------------------
# AvailabilityFilters
# ---------------------------------------------------------------------------

class TestAvailabilityFilters:
    def test_basic_construction(self):
        f = AvailabilityFilters(
            train_number="12951",
            origin="NDLS",
            destination="BCT",
            departure_date="2025-06-01",
            train_class=TrainClass.SL,
        )
        assert f.train_number == "12951"
        assert f.train_class == TrainClass.SL
        assert f.quota == Quota.GENERAL

    def test_station_uppercased(self):
        f = AvailabilityFilters(
            train_number="12951",
            origin="ndls",
            destination="bct",
            departure_date="2025-06-01",
            train_class=TrainClass.THREE_AC,
        )
        assert f.origin == "NDLS"
        assert f.destination == "BCT"


# ---------------------------------------------------------------------------
# SeatAvailability
# ---------------------------------------------------------------------------

class TestSeatAvailability:
    def test_construction(self):
        a = SeatAvailability(
            train_class=TrainClass.SL,
            quota=Quota.GENERAL,
            status="AVAILABLE-42",
            available_count=42,
            fare=350.0,
        )
        assert a.fare == 350.0
        assert a.currency == "INR"
        assert a.available_count == 42

    def test_optional_fields_default_none(self):
        a = SeatAvailability(
            train_class=TrainClass.SL,
            quota=Quota.GENERAL,
            status="REGRET",
        )
        assert a.fare is None
        assert a.available_count is None


# ---------------------------------------------------------------------------
# TrainResult
# ---------------------------------------------------------------------------

class TestTrainResult:
    def test_construction(self):
        r = TrainResult(
            train_number="12951",
            train_name="Mumbai Rajdhani Express",
            departure_station="NDLS",
            arrival_station="BCT",
            departure_time="16:25",
            arrival_time="08:15",
            duration=955,
            distance=1384,
            classes=[TrainClass.ONE_AC, TrainClass.TWO_AC, TrainClass.THREE_AC],
            days_of_run=["Daily"],
        )
        assert r.train_number == "12951"
        assert r.duration == 955
        assert TrainClass.THREE_AC in r.classes
