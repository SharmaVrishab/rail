"""Tests for rail.core.builders."""

import pytest

from rail.core.builders import (
    build_availability_search,
    build_train_search,
    normalize_date,
)
from rail.models.indian_railways.base import Quota, SortBy, TrainClass


# ---------------------------------------------------------------------------
# normalize_date
# ---------------------------------------------------------------------------

class TestNormalizeDate:
    def test_iso_format_passthrough(self):
        assert normalize_date("2025-06-01") == "2025-06-01"

    def test_dd_mm_yyyy(self):
        assert normalize_date("01-06-2025") == "2025-06-01"

    def test_slash_format(self):
        assert normalize_date("01/06/2025") == "2025-06-01"

    def test_compact_format(self):
        assert normalize_date("20250601") == "2025-06-01"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            normalize_date("not-a-date")


# ---------------------------------------------------------------------------
# build_train_search
# ---------------------------------------------------------------------------

class TestBuildTrainSearch:
    def test_basic(self):
        f = build_train_search(
            origin="NDLS",
            destination="BCT",
            departure_date="2025-06-01",
        )
        assert f.origin == "NDLS"
        assert f.destination == "BCT"
        assert f.departure_date == "2025-06-01"
        assert f.train_class is None
        assert f.quota == Quota.GENERAL

    def test_with_class_and_quota(self):
        f = build_train_search(
            origin="NDLS",
            destination="BCT",
            departure_date="2025-06-01",
            train_class=TrainClass.SL,
            quota=Quota.TATKAL,
            sort_by=SortBy.DURATION,
        )
        assert f.train_class == TrainClass.SL
        assert f.quota == Quota.TATKAL
        assert f.sort_by == SortBy.DURATION

    def test_date_normalised(self):
        f = build_train_search(origin="NDLS", destination="BCT", departure_date="01-06-2025")
        assert f.departure_date == "2025-06-01"


# ---------------------------------------------------------------------------
# build_availability_search
# ---------------------------------------------------------------------------

class TestBuildAvailabilitySearch:
    def test_basic(self):
        f = build_availability_search(
            train_number="12951",
            origin="NDLS",
            destination="BCT",
            departure_date="2025-06-01",
            train_class=TrainClass.THREE_AC,
        )
        assert f.train_number == "12951"
        assert f.train_class == TrainClass.THREE_AC
        assert f.quota == Quota.GENERAL

    def test_date_normalised(self):
        f = build_availability_search(
            train_number="12951",
            origin="NDLS",
            destination="BCT",
            departure_date="01/06/2025",
            train_class=TrainClass.SL,
        )
        assert f.departure_date == "2025-06-01"
