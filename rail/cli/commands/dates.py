"""CLI command: find availability and fares across a date range."""

import json
from typing import Annotated

import typer

from rail.core.parsers import ParseError, parse_quota, parse_train_class, resolve_station
from rail.models.indian_railways.base import Quota, TrainClass
from rail.search.dates import SearchDates


def dates(
    origin: Annotated[str, typer.Argument(help="Origin station code (e.g. NDLS)")],
    destination: Annotated[str, typer.Argument(help="Destination station code (e.g. BCT)")],
    start_date: Annotated[str, typer.Argument(help="Range start date (YYYY-MM-DD)")],
    end_date: Annotated[str, typer.Argument(help="Range end date (YYYY-MM-DD)")],
    train_class: Annotated[
        str,
        typer.Option("--class", "-c", help="Class: SL, 3A, 2A, 1A, CC, EC, 2S (default: SL)"),
    ] = "SL",
    quota: Annotated[
        str,
        typer.Option("--quota", "-q", help="Quota: GN, TQ, PT, LD, SS (default: GN)"),
    ] = "GN",
    train_number: Annotated[
        str | None,
        typer.Option("--train", "-t", help="Specific train number (auto-detected if omitted)"),
    ] = None,
    sort_by_price: Annotated[
        bool,
        typer.Option("--price/--status", help="Sort by price (default) or availability status"),
    ] = True,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output in JSON format"),
    ] = False,
) -> None:
    """Find seat availability and fares across a date range.

    Example:
        rail dates NDLS BCT 2025-06-01 2025-06-30 --class SL
        rail dates NDLS BCT 2025-06-01 2025-06-30 --class 3A --quota TQ --status
        rail dates NDLS MAS 2025-06-01 2025-07-31 --train 12163 --price
    """
    try:
        origin_code = resolve_station(origin)
        dest_code = resolve_station(destination)
        cls = parse_train_class(train_class)
        q = parse_quota(quota)
    except ParseError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    try:
        results = SearchDates().search(
            origin=origin_code,
            destination=dest_code,
            start_date=start_date,
            end_date=end_date,
            train_class=cls,
            quota=q,
            train_number=train_number,
            sort_by_price=sort_by_price,
        )
    except Exception as e:
        typer.echo(f"Search failed: {e}", err=True)
        raise typer.Exit(1) from e

    if not results:
        if output_json:
            typer.echo(json.dumps({"dates": [], "count": 0}))
        else:
            typer.echo("No results found for the given date range.")
        raise typer.Exit(0)

    if output_json:
        typer.echo(json.dumps({"dates": [r.model_dump() for r in results], "count": len(results)}))
        return

    typer.echo(f"\nAvailability: {origin_code} → {dest_code}  |  Train {results[0].train_number}  |  {cls.value}\n")
    typer.echo(f"{'Date':<12}  {'Status':<20}  {'Seats':>6}  {'Fare (INR)':>12}")
    typer.echo("-" * 56)
    for r in results:
        seats = str(r.available_count) if r.available_count is not None else "—"
        fare = f"₹{r.fare:,.0f}" if r.fare is not None else "—"
        typer.echo(f"{r.date:<12}  {r.status:<20}  {seats:>6}  {fare:>12}")
    typer.echo("")
