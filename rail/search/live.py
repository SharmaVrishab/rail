"""Live train running status via NTES."""

import os
from datetime import datetime

from rail.models.indian_railways.base import LiveStatus
from rail.search.client import get_client

_NTES_LIVE_URL = "https://enquiry.indianrail.gov.in/mntes/q?opt=liveStatus&trainNo={train}"
_RAPIDAPI_LIVE_URL = "https://indianrailways.p.rapidapi.com/liveTrainStatus"
_RAPIDAPI_HOST = "indianrailways.p.rapidapi.com"


class GetLiveStatus:
    """Fetch the current running position of a train."""

    def get(self, train_number: str) -> LiveStatus | None:
        """Return live status for the given train.

        Args:
            train_number: Train number as a string (e.g. "12951").

        Returns:
            LiveStatus object or None if unavailable.
        """
        client = get_client()
        api_key = os.environ.get("RAIL_API_KEY")
        provider = os.environ.get("RAIL_API_PROVIDER", "ntes")

        if provider in ("rapidapi", "railwayapi") and api_key:
            return self._get_rapidapi(client, train_number, api_key)
        return self._get_ntes(client, train_number)

    def _get_ntes(self, client, train_number: str) -> LiveStatus | None:
        """Query NTES for live train position.

        Args:
            client: HTTP client.
            train_number: Train number string.

        Returns:
            Parsed LiveStatus or None.
        """
        url = _NTES_LIVE_URL.format(train=train_number)
        try:
            response = client.get(url)
            return self._parse(response.json(), train_number)
        except Exception:
            return None

    def _get_rapidapi(self, client, train_number: str, api_key: str) -> LiveStatus | None:
        """Query RapidAPI for live train status.

        Args:
            client: HTTP client.
            train_number: Train number string.
            api_key: RapidAPI key.

        Returns:
            Parsed LiveStatus or None.
        """
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": _RAPIDAPI_HOST,
        }
        try:
            response = client.get(
                _RAPIDAPI_LIVE_URL,
                params={"trainNo": train_number},
                headers=headers,
            )
            return self._parse(response.json(), train_number)
        except Exception:
            return None

    def _parse(self, raw: dict, train_number: str) -> LiveStatus | None:
        """Parse live status JSON into LiveStatus model.

        Args:
            raw: Raw JSON from the API.
            train_number: Original train number.

        Returns:
            LiveStatus or None on failure.
        """
        try:
            train_name = str(
                raw.get("trainName", raw.get("train_name", ""))
            ).strip().title()
            current_stn = str(
                raw.get("currentStation", raw.get("current_station", raw.get("stnCode", "")))
            ).strip().upper()
            current_stn_name = str(
                raw.get("currentStationName", raw.get("station_name", current_stn))
            ).strip().title()
            delay = int(raw.get("delayInMinutes", raw.get("delay", 0)))

            # last_updated — try to parse, fallback to now
            ts_raw = raw.get("lastUpdated", raw.get("last_updated", ""))
            try:
                last_updated = datetime.fromisoformat(str(ts_raw))
            except (ValueError, TypeError):
                last_updated = datetime.now()

            next_stn = str(
                raw.get("nextStation", raw.get("next_station", ""))
            ).strip().upper() or None
            next_stn_name = str(
                raw.get("nextStationName", raw.get("next_station_name", ""))
            ).strip().title() or None
            exp_arr_raw = raw.get("expectedArrivalNext", raw.get("expected_arrival", ""))
            try:
                expected_arrival_next = datetime.fromisoformat(str(exp_arr_raw))
            except (ValueError, TypeError):
                expected_arrival_next = None

            distance = raw.get("distanceFromSource", raw.get("distance", None))

            return LiveStatus(
                train_number=train_number,
                train_name=train_name,
                current_station=current_stn,
                current_station_name=current_stn_name,
                delay_minutes=delay,
                last_updated=last_updated,
                next_station=next_stn,
                next_station_name=next_stn_name,
                expected_arrival_next=expected_arrival_next,
                distance_from_source=int(distance) if distance is not None else None,
            )
        except Exception:
            return None
