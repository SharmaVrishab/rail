"""PNR status lookup using NTES / IRCTC API."""

import os

from rail.models.indian_railways.base import PNRStatus
from rail.search.client import get_client

# NTES PNR status endpoint
_NTES_PNR_URL = "https://enquiry.indianrail.gov.in/mntes/q?opt=pnr&pnrNo={pnr}"

# RapidAPI fallback
_RAPIDAPI_PNR_URL = "https://indianrailways.p.rapidapi.com/pnr-status"
_RAPIDAPI_HOST = "indianrailways.p.rapidapi.com"


class CheckPNR:
    """Look up a PNR booking status."""

    def check(self, pnr_number: str) -> PNRStatus | None:
        """Fetch and return PNR status.

        Tries the primary NTES endpoint, falls back to RapidAPI when
        RAIL_API_KEY is set.

        Args:
            pnr_number: 10-digit PNR number as a string.

        Returns:
            PNRStatus object, or None if the PNR could not be fetched.
        """
        client = get_client()
        api_key = os.environ.get("RAIL_API_KEY")
        provider = os.environ.get("RAIL_API_PROVIDER", "ntes")

        if provider in ("rapidapi", "railwayapi") and api_key:
            return self._check_rapidapi(client, pnr_number, api_key)
        return self._check_ntes(client, pnr_number)

    def _check_ntes(self, client, pnr_number: str) -> PNRStatus | None:
        """Query NTES for PNR status.

        Args:
            client: HTTP client instance.
            pnr_number: 10-digit PNR string.

        Returns:
            Parsed PNRStatus or None.
        """
        url = _NTES_PNR_URL.format(pnr=pnr_number)
        try:
            response = client.get(url)
            return self._parse(response.json(), pnr_number)
        except Exception:
            return None

    def _check_rapidapi(self, client, pnr_number: str, api_key: str) -> PNRStatus | None:
        """Query RapidAPI for PNR status.

        Args:
            client: HTTP client instance.
            pnr_number: 10-digit PNR string.
            api_key: RapidAPI key.

        Returns:
            Parsed PNRStatus or None.
        """
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": _RAPIDAPI_HOST,
        }
        try:
            response = client.get(
                _RAPIDAPI_PNR_URL,
                params={"pnrNumber": pnr_number},
                headers=headers,
            )
            return self._parse(response.json(), pnr_number)
        except Exception:
            return None

    def _parse(self, raw: dict, pnr_number: str) -> PNRStatus | None:
        """Parse PNR JSON into a PNRStatus model.

        Handles both NTES and RapidAPI response shapes.

        Args:
            raw: Raw JSON dict from the API.
            pnr_number: Original PNR number (used as fallback).

        Returns:
            PNRStatus or None if parsing fails.
        """
        try:
            # Normalise varying key names across providers
            train_number = str(
                raw.get("trainNumber", raw.get("train_number", raw.get("trainNo", "")))
            ).strip()
            train_name = str(
                raw.get("trainName", raw.get("train_name", ""))
            ).strip().title()
            journey_date = str(
                raw.get("dateOfJourney", raw.get("date", raw.get("doj", "")))
            ).strip()
            from_station = str(
                raw.get("boardingStation", raw.get("from", raw.get("boardingStationCode", "")))
            ).strip().upper()
            to_station = str(
                raw.get("destinationStation", raw.get("to", raw.get("destStnCode", "")))
            ).strip().upper()
            train_class = str(raw.get("journeyClass", raw.get("class", ""))).strip().upper()
            quota = str(raw.get("quota", "GN")).strip().upper()
            chart_prepared = bool(raw.get("chartPrepared", raw.get("chart", False)))
            boarding_station = str(
                raw.get("boardingStationCode", raw.get("boarding_station", from_station))
            ).strip().upper()

            # Passengers list
            passengers_raw = raw.get(
                "passengerList", raw.get("passengers", raw.get("psgList", []))
            )
            passengers: list[dict] = []
            for p in passengers_raw:
                passengers.append(
                    {
                        "seat_number": str(p.get("seatNumber", p.get("seat", ""))),
                        "booking_status": str(
                            p.get("bookingStatus", p.get("booking_status", ""))
                        ),
                        "current_status": str(
                            p.get("currentStatus", p.get("current_status", ""))
                        ),
                        "coach": str(p.get("coach", p.get("coachId", ""))),
                    }
                )

            return PNRStatus(
                pnr_number=pnr_number,
                train_number=train_number,
                train_name=train_name,
                journey_date=journey_date,
                from_station=from_station,
                to_station=to_station,
                train_class=train_class,
                quota=quota,
                passengers=passengers,
                chart_prepared=chart_prepared,
                boarding_station=boarding_station,
            )
        except Exception:
            return None
