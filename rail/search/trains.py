"""Train search implementation using NTES (National Train Enquiry System).

Targets the publicly-accessible NTES API to find trains running between
two stations on a specific date.
"""

import json
import re
from datetime import datetime

from rail.models.indian_railways.base import SortBy, TrainClass, TrainResult
from rail.models.indian_railways.trains import TrainSearchFilters
from rail.search.client import get_client

# NTES base URL for train enquiry
_NTES_BASE = "https://enquiry.indianrail.gov.in/mntes"

# Alternative: erail.in offers a stable JSON API used by many apps
_ERAIL_TRAINS_URL = "https://erail.in/rail/getTrains.aspx"


class SearchTrains:
    """Find trains running between two stations on a given date."""

    def search(self, filters: TrainSearchFilters, top_n: int = 10) -> list[TrainResult]:
        """Search for trains between origin and destination on departure_date.

        Makes a request to NTES / erail.in and parses the response into
        structured TrainResult objects.

        Args:
            filters: TrainSearchFilters specifying the journey parameters.
            top_n: Maximum number of results to return (0 = all).

        Returns:
            List of TrainResult objects sorted per filters.sort_by.
        """
        client = get_client()
        raw = self._fetch(client, filters)
        results = self._parse(raw, filters)

        if filters.train_class:
            results = [r for r in results if filters.train_class in r.classes]

        results = self._sort(results, filters.sort_by)

        if top_n > 0:
            results = results[:top_n]

        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch(self, client, filters: TrainSearchFilters) -> dict:
        """Fetch raw train data from erail.in.

        erail.in is widely used by Indian Railways apps and returns structured
        JSON without authentication.

        Args:
            client: HTTP client instance.
            filters: Search parameters.

        Returns:
            Parsed JSON response as a dict.
        """
        params = {
            "stationFrom": filters.origin,
            "stationTo": filters.destination,
            "datOfJourney": datetime.strptime(filters.departure_date, "%Y-%m-%d").strftime("%d-%b-%Y"),
            "inpQuota": filters.quota.value,
            "trainClass": filters.train_class.value if filters.train_class else "",
            "SORT": "D",  # Sort by departure by default
        }
        try:
            response = client.get(_ERAIL_TRAINS_URL, params=params)
            return response.json()
        except Exception:
            # Return empty structure on failure
            return {}

    def _parse(self, raw: dict, filters: TrainSearchFilters) -> list[TrainResult]:
        """Parse erail.in response into TrainResult list.

        Args:
            raw: Raw JSON dict from the API.
            filters: Original search filters (used for station codes).

        Returns:
            List of TrainResult objects.
        """
        results: list[TrainResult] = []

        # erail.in response format: {"Trains": [...]}
        trains_raw = raw.get("Trains", [])

        for item in trains_raw:
            try:
                train_number = str(item.get("trainNo", "")).strip()
                train_name = str(item.get("trainName", "")).strip().title()
                dep_time = str(item.get("departureTime", "00:00")).strip()
                arr_time = str(item.get("arrivalTime", "00:00")).strip()
                distance = int(item.get("distance", 0))
                duration_str = str(item.get("duration", "0:00"))
                duration = self._parse_duration(duration_str)
                days_of_run = self._parse_days(item.get("runningDays", ""))
                classes = self._parse_classes(item.get("availableClasses", ""))

                results.append(
                    TrainResult(
                        train_number=train_number,
                        train_name=train_name,
                        departure_station=filters.origin,
                        arrival_station=filters.destination,
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        duration=duration,
                        distance=distance,
                        classes=classes,
                        days_of_run=days_of_run,
                    )
                )
            except Exception:
                continue

        return results

    def _parse_duration(self, duration_str: str) -> int:
        """Convert a duration string like '16:45' or '16h 45m' to minutes.

        Args:
            duration_str: Duration as returned by the API.

        Returns:
            Duration in minutes.
        """
        m = re.match(r"(\d+)[h:](\d+)", duration_str)
        if m:
            return int(m.group(1)) * 60 + int(m.group(2))
        return 0

    def _parse_days(self, days_str: str) -> list[str]:
        """Parse running-days string into a list of day abbreviations.

        Args:
            days_str: A 7-char string like "1234567" or "Mon,Wed,Fri".

        Returns:
            List of day names like ["Mon", "Tue", ...].
        """
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        if not days_str:
            return ["Daily"]

        # Numeric format "1234567" — 1=Mon ... 7=Sun
        if re.match(r"^[1-7]+$", days_str.strip()):
            return [day_names[int(d) - 1] for d in days_str.strip() if d.isdigit()]

        # Already comma-separated names
        if "," in days_str:
            return [d.strip() for d in days_str.split(",") if d.strip()]

        return [days_str.strip()] if days_str.strip() else ["Daily"]

    def _parse_classes(self, classes_str: str) -> list[TrainClass]:
        """Parse available class codes into TrainClass enums.

        Args:
            classes_str: Comma- or space-separated class codes like "SL,3A,2A".

        Returns:
            List of TrainClass values present on this train.
        """
        code_to_class: dict[str, TrainClass] = {
            tc.value: tc for tc in TrainClass
        }
        classes: list[TrainClass] = []
        for token in re.split(r"[,\s]+", classes_str):
            token = token.strip().upper()
            if token in code_to_class:
                classes.append(code_to_class[token])
        return classes

    def _sort(self, results: list[TrainResult], sort_by: SortBy) -> list[TrainResult]:
        """Sort results according to the requested order.

        Args:
            results: Unsorted train results.
            sort_by: Sorting criterion.

        Returns:
            Sorted list of TrainResult.
        """
        if sort_by == SortBy.DEPARTURE_TIME:
            return sorted(results, key=lambda r: r.departure_time)
        if sort_by == SortBy.ARRIVAL_TIME:
            return sorted(results, key=lambda r: r.arrival_time)
        if sort_by == SortBy.DURATION:
            return sorted(results, key=lambda r: r.duration)
        return results
