"""Seat availability search using IRCTC / RailConnect unofficial API.

Checks real-time seat availability for a specific train, class, and quota
on a given journey date.
"""

import os
import re
from datetime import datetime

from rail.models.indian_railways.availability import AvailabilityFilters
from rail.models.indian_railways.base import Quota, SeatAvailability, TrainClass
from rail.search.client import get_client

# IRCTC availability endpoint (unofficial, used by RailConnect app)
_IRCTC_AVAIL_URL = (
    "https://www.irctc.co.in/eticketing/protected/mapps1/avlFarenquiry"
    "/{train}/{from_stn}/{to_stn}/{date}/{class_}/{quota}"
)

# Fallback: RailwayAPI (requires RAIL_API_KEY)
_RAILWAYAPI_AVAIL_URL = "https://indianrailways.p.rapidapi.com/checkSeatAvailability"
_RAPIDAPI_HOST = "indianrailways.p.rapidapi.com"


class SearchAvailability:
    """Check seat availability for a train on a specific date."""

    def search(self, filters: AvailabilityFilters) -> list[SeatAvailability]:
        """Check availability for the given filters.

        Tries the IRCTC endpoint first; falls back to RapidAPI when RAIL_API_KEY
        is set and the IRCTC call fails.

        Args:
            filters: Journey parameters including train, class, quota, and date.

        Returns:
            List of SeatAvailability (may contain multiple quotas).
        """
        client = get_client()
        api_key = os.environ.get("RAIL_API_KEY")
        provider = os.environ.get("RAIL_API_PROVIDER", "ntes")

        if provider in ("rapidapi", "railwayapi") and api_key:
            return self._search_rapidapi(client, filters, api_key)
        return self._search_irctc(client, filters)

    # ------------------------------------------------------------------
    # IRCTC path
    # ------------------------------------------------------------------

    def _search_irctc(
        self, client, filters: AvailabilityFilters
    ) -> list[SeatAvailability]:
        """Query IRCTC availability endpoint.

        Args:
            client: HTTP client instance.
            filters: Availability query parameters.

        Returns:
            Parsed list of SeatAvailability.
        """
        date_str = datetime.strptime(filters.departure_date, "%Y-%m-%d").strftime("%Y%m%d")
        url = _IRCTC_AVAIL_URL.format(
            train=filters.train_number,
            from_stn=filters.origin,
            to_stn=filters.destination,
            date=date_str,
            class_=filters.train_class.value,
            quota=filters.quota.value,
        )
        headers = {
            "referer": "https://www.irctc.co.in/nget/train-search",
            "origin": "https://www.irctc.co.in",
        }
        try:
            response = client.get(url, headers=headers)
            return self._parse_irctc(response.json(), filters)
        except Exception:
            return []

    def _parse_irctc(self, raw: dict, filters: AvailabilityFilters) -> list[SeatAvailability]:
        """Parse IRCTC availability JSON.

        Args:
            raw: Raw JSON from IRCTC.
            filters: Original filters.

        Returns:
            List of SeatAvailability.
        """
        results: list[SeatAvailability] = []

        avl_list = raw.get("avlDayList", raw.get("availability", []))
        if not avl_list:
            # Single availability object
            status = raw.get("availablityStatus", raw.get("status", ""))
            fare = self._extract_fare(raw)
            if status:
                results.append(
                    SeatAvailability(
                        train_class=filters.train_class,
                        quota=filters.quota,
                        status=status,
                        available_count=self._count_from_status(status),
                        fare=fare,
                    )
                )
        else:
            for item in avl_list[:1]:  # First entry = requested date
                status = item.get("availablityStatus", item.get("status", ""))
                fare = self._extract_fare(item)
                results.append(
                    SeatAvailability(
                        train_class=filters.train_class,
                        quota=filters.quota,
                        status=status,
                        available_count=self._count_from_status(status),
                        fare=fare,
                    )
                )

        return results

    # ------------------------------------------------------------------
    # RapidAPI / third-party path
    # ------------------------------------------------------------------

    def _search_rapidapi(
        self, client, filters: AvailabilityFilters, api_key: str
    ) -> list[SeatAvailability]:
        """Query via RapidAPI Indian Railways endpoint.

        Args:
            client: HTTP client instance.
            filters: Availability query parameters.
            api_key: RapidAPI key from RAIL_API_KEY.

        Returns:
            Parsed list of SeatAvailability.
        """
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": _RAPIDAPI_HOST,
        }
        params = {
            "trainNo": filters.train_number,
            "fromStation": filters.origin,
            "toStation": filters.destination,
            "doj": filters.departure_date,
            "classCode": filters.train_class.value,
            "quota": filters.quota.value,
        }
        try:
            response = client.get(_RAILWAYAPI_AVAIL_URL, params=params, headers=headers)
            return self._parse_rapidapi(response.json(), filters)
        except Exception:
            return []

    def _parse_rapidapi(self, raw: dict, filters: AvailabilityFilters) -> list[SeatAvailability]:
        """Parse RapidAPI availability response.

        Args:
            raw: Raw JSON response.
            filters: Original filters.

        Returns:
            List of SeatAvailability.
        """
        status = (
            raw.get("availability", {}).get("status")
            or raw.get("status", "")
        )
        fare = self._extract_fare(raw.get("fare", raw))
        return [
            SeatAvailability(
                train_class=filters.train_class,
                quota=filters.quota,
                status=status or "UNKNOWN",
                available_count=self._count_from_status(status),
                fare=fare,
            )
        ]

    # ------------------------------------------------------------------
    # Shared utilities
    # ------------------------------------------------------------------

    def _extract_fare(self, data: dict) -> float | None:
        """Extract numeric fare from a response dict.

        Args:
            data: Dict that may contain fare fields.

        Returns:
            Fare as float, or None if not found.
        """
        for key in ("totalFare", "fare", "baseFare", "total_fare"):
            val = data.get(key)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    continue
        return None

    def _count_from_status(self, status: str) -> int | None:
        """Parse available seat count from status string.

        Args:
            status: Status string like "AVAILABLE-42", "RAC-1", "WL-5".

        Returns:
            Integer count if parseable, else None.
        """
        m = re.search(r"AVAILABLE[-\s](\d+)", status, re.IGNORECASE)
        if m:
            return int(m.group(1))
        return None
