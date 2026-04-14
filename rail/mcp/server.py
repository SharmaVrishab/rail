"""Indian Railways MCP Server.

Provides an MCP (Model Context Protocol) server for Indian Railways data,
enabling AI assistants to search trains, check seat availability, look up
PNR status, get live running status, and find cheapest travel dates.
"""

import os
from typing import Any

from fastmcp import FastMCP
from pydantic_settings import BaseSettings, SettingsConfigDict

from rail.core import (
    ParseError,
    build_availability_search,
    build_train_search,
    parse_quota,
    parse_sort_by,
    parse_train_class,
    resolve_station,
)
from rail.models.indian_railways.base import Quota, SortBy, TrainClass
from rail.search import CheckPNR, GetLiveStatus, SearchAvailability, SearchDates, SearchTrains


class RailConfig(BaseSettings):
    """Configuration for the Rail MCP server (loaded from environment variables)."""

    model_config = SettingsConfigDict(env_prefix="RAIL_")

    api_key: str | None = None
    api_provider: str = "ntes"
    rate_limit: int = 5


mcp = FastMCP(
    name="rail",
    instructions=(
        "Indian Railways search assistant. "
        "You can search for trains between stations, check seat availability, "
        "look up PNR booking status, get live train running status, and find "
        "the cheapest/most available dates on a route. "
        "Station codes are uppercase IATA-style codes (e.g. NDLS, BCT, HWH, MAS, SBC). "
        "Train classes: SL (Sleeper), 3A (3-Tier AC), 2A (2-Tier AC), 1A (1st AC), "
        "CC (Chair Car), EC (Executive Chair Car), 2S (2nd Sitting). "
        "Quota codes: GN (General), TQ (Tatkal), PT (Premium Tatkal), LD (Ladies), SS (Senior Citizen)."
    ),
)

_config = RailConfig()
_train_searcher = SearchTrains()
_avail_searcher = SearchAvailability()
_pnr_checker = CheckPNR()
_live_getter = GetLiveStatus()
_date_searcher = SearchDates()


# ---------------------------------------------------------------------------
# Tool 1: search_trains
# ---------------------------------------------------------------------------

@mcp.tool()
def search_trains(
    origin: str,
    destination: str,
    date: str,
    train_class: str | None = None,
    quota: str = "GN",
    sort_by: str = "DEP",
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Find trains running between two Indian Railway stations on a specific date.

    Args:
        origin: Origin station code (e.g. "NDLS" for New Delhi).
        destination: Destination station code (e.g. "BCT" for Mumbai Central).
        date: Date of journey in YYYY-MM-DD format.
        train_class: Optional class filter — SL, 3A, 2A, 1A, CC, EC, 2S.
            Pass null to see all classes.
        quota: Booking quota — GN (General), TQ (Tatkal), PT (Premium Tatkal),
            LD (Ladies), SS (Senior Citizen). Defaults to GN.
        sort_by: Sort order — DEP (departure time), ARR (arrival), DUR (duration).
            Defaults to DEP.
        top_n: Maximum results to return (default 10).

    Returns:
        List of train dicts with keys: train_number, train_name,
        departure_time, arrival_time, duration (minutes), distance (km),
        classes, days_of_run.
    """
    try:
        origin_code = resolve_station(origin)
        dest_code = resolve_station(destination)
        cls = parse_train_class(train_class) if train_class else None
        q = parse_quota(quota)
        sort = parse_sort_by(sort_by)
    except ParseError as e:
        return [{"error": str(e)}]

    filters = build_train_search(
        origin=origin_code,
        destination=dest_code,
        departure_date=date,
        train_class=cls,
        quota=q,
        sort_by=sort,
    )

    try:
        results = _train_searcher.search(filters, top_n=top_n)
        return [r.model_dump() for r in results]
    except Exception as e:
        return [{"error": f"Search failed: {e}"}]


# ---------------------------------------------------------------------------
# Tool 2: check_availability
# ---------------------------------------------------------------------------

@mcp.tool()
def check_availability(
    train_number: str,
    origin: str,
    destination: str,
    date: str,
    train_class: str,
    quota: str = "GN",
) -> list[dict[str, Any]]:
    """Check seat availability for a specific train on a given date.

    Args:
        train_number: Train number (e.g. "12951" for Mumbai Rajdhani).
        origin: Boarding station code (e.g. "NDLS").
        destination: De-boarding station code (e.g. "BCT").
        date: Journey date in YYYY-MM-DD format.
        train_class: Coach class — SL, 3A, 2A, 1A, CC, EC, 2S.
        quota: Booking quota — GN, TQ, PT, LD, SS. Defaults to GN.

    Returns:
        List of availability dicts with keys: train_class, quota, status
        (e.g. "AVAILABLE-42", "RAC-1", "WL-5", "REGRET"),
        available_count, fare (INR), currency.
    """
    try:
        origin_code = resolve_station(origin)
        dest_code = resolve_station(destination)
        cls = parse_train_class(train_class)
        q = parse_quota(quota)
    except ParseError as e:
        return [{"error": str(e)}]

    filters = build_availability_search(
        train_number=train_number,
        origin=origin_code,
        destination=dest_code,
        departure_date=date,
        train_class=cls,
        quota=q,
    )

    try:
        results = _avail_searcher.search(filters)
        return [r.model_dump() for r in results]
    except Exception as e:
        return [{"error": f"Search failed: {e}"}]


# ---------------------------------------------------------------------------
# Tool 3: check_pnr
# ---------------------------------------------------------------------------

@mcp.tool()
def check_pnr(pnr_number: str) -> dict[str, Any]:
    """Look up PNR booking status for an Indian Railways ticket.

    Args:
        pnr_number: 10-digit PNR number as a string (e.g. "1234567890").

    Returns:
        Dict with keys: pnr_number, train_number, train_name, journey_date,
        from_station, to_station, train_class, quota, chart_prepared,
        boarding_station, passengers (list of {seat_number, booking_status,
        current_status, coach}).
    """
    pnr_number = pnr_number.strip()
    if not pnr_number:
        return {"error": "PNR number is required."}

    try:
        status = _pnr_checker.check(pnr_number)
        if not status:
            return {"error": "PNR not found or service is currently unavailable."}
        return status.model_dump()
    except Exception as e:
        return {"error": f"PNR lookup failed: {e}"}


# ---------------------------------------------------------------------------
# Tool 4: get_live_status
# ---------------------------------------------------------------------------

@mcp.tool()
def get_live_status(train_number: str) -> dict[str, Any]:
    """Get real-time running status of a train.

    Args:
        train_number: Train number (e.g. "12951").

    Returns:
        Dict with keys: train_number, train_name, current_station,
        current_station_name, delay_minutes (positive = late),
        last_updated, next_station, next_station_name,
        expected_arrival_next, distance_from_source (km).
    """
    train_number = train_number.strip()
    if not train_number:
        return {"error": "Train number is required."}

    try:
        status = _live_getter.get(train_number)
        if not status:
            return {"error": "Live status is currently unavailable for this train."}
        return status.model_dump(mode="json")
    except Exception as e:
        return {"error": f"Live status lookup failed: {e}"}


# ---------------------------------------------------------------------------
# Tool 5: search_dates
# ---------------------------------------------------------------------------

@mcp.tool()
def search_dates(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    train_class: str,
    quota: str = "GN",
    train_number: str | None = None,
    sort_by_price: bool = True,
) -> list[dict[str, Any]]:
    """Find seat availability and fares across a date range for a train route.

    Useful for finding the cheapest or most available days to travel.

    Args:
        origin: Origin station code (e.g. "NDLS").
        destination: Destination station code (e.g. "BCT").
        start_date: Start of the date range (YYYY-MM-DD).
        end_date: End of the date range (YYYY-MM-DD).
        train_class: Class to check — SL, 3A, 2A, 1A, CC, EC, 2S.
        quota: Booking quota — GN, TQ, PT, LD, SS. Defaults to GN.
        train_number: Optional specific train number. If omitted, the first
            available train on the route is used for the entire range.
        sort_by_price: Sort by fare (True, default) or by availability status.

    Returns:
        List of availability dicts per date, each with keys: date, train_number,
        train_class, quota, status, available_count, fare (INR), currency.
        Sorted by price (cheapest first) when sort_by_price is True.
    """
    try:
        origin_code = resolve_station(origin)
        dest_code = resolve_station(destination)
        cls = parse_train_class(train_class)
        q = parse_quota(quota)
    except ParseError as e:
        return [{"error": str(e)}]

    try:
        results = _date_searcher.search(
            origin=origin_code,
            destination=dest_code,
            start_date=start_date,
            end_date=end_date,
            train_class=cls,
            quota=q,
            train_number=train_number,
            sort_by_price=sort_by_price,
        )
        return [r.model_dump() for r in results]
    except Exception as e:
        return [{"error": f"Date search failed: {e}"}]


# ---------------------------------------------------------------------------
# Run helpers (used by _entry.py)
# ---------------------------------------------------------------------------

def run() -> None:
    """Run the MCP server over STDIO (for Claude Desktop / MCP clients)."""
    mcp.run()


def run_http(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the MCP server over HTTP with SSE streaming.

    Args:
        host: Bind address (default: 0.0.0.0).
        port: Port number (default: 8000).
    """
    mcp.run(transport="streamable-http", host=host, port=port)
