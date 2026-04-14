"""CLI command: check seat availability on a specific train."""

import json
from typing import Annotated

import typer

from rail.core.builders import build_availability_search
from rail.core.parsers import ParseError, parse_quota, parse_train_class, resolve_station
from rail.search.availability import SearchAvailability


def availability(
    train_number: Annotated[str, typer.Argument(help="Train number (e.g. 12951)")],
    origin: Annotated[str, typer.Argument(help="Boarding station code (e.g. NDLS)")],
    destination: Annotated[str, typer.Argument(help="De-boarding station code (e.g. BCT)")],
    departure_date: Annotated[str, typer.Argument(help="Journey date (YYYY-MM-DD)")],
    train_class: Annotated[
        str,
        typer.Option("--class", "-c", help="Class: SL, 3A, 2A, 1A, CC, EC, 2S"),
    ] = "SL",
    quota: Annotated[
        str,
        typer.Option("--quota", "-q", help="Quota: GN, TQ, PT, LD, SS (default: GN)"),
    ] = "GN",
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output in JSON format"),
    ] = False,
) -> None:
    """Check seat availability for a train on a specific date.

    Example:
        rail availability 12951 NDLS BCT 2025-06-01 --class SL
        rail availability 12951 NDLS BCT 2025-06-01 --class 3A --quota TQ
    """
    try:
        origin_code = resolve_station(origin)
        dest_code = resolve_station(destination)
        cls = parse_train_class(train_class)
        q = parse_quota(quota)
    except ParseError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    filters = build_availability_search(
        train_number=train_number,
        origin=origin_code,
        destination=dest_code,
        departure_date=departure_date,
        train_class=cls,
        quota=q,
    )

    try:
        results = SearchAvailability().search(filters)
    except Exception as e:
        typer.echo(f"Search failed: {e}", err=True)
        raise typer.Exit(1) from e

    if not results:
        if output_json:
            typer.echo(json.dumps({"availability": [], "count": 0}))
        else:
            typer.echo("No availability information returned.")
        raise typer.Exit(0)

    if output_json:
        typer.echo(json.dumps({"availability": [r.model_dump() for r in results], "count": len(results)}))
        return

    typer.echo(f"\nAvailability: Train {train_number}  |  {origin_code} → {dest_code}  |  {departure_date}\n")
    typer.echo(f"{'Class':<6}  {'Quota':<4}  {'Status':<20}  {'Seats':>6}  {'Fare (INR)':>10}")
    typer.echo("-" * 56)
    for r in results:
        seats = str(r.available_count) if r.available_count is not None else "—"
        fare = f"₹{r.fare:,.0f}" if r.fare is not None else "—"
        typer.echo(
            f"{r.train_class.value:<6}  {r.quota.value:<4}  {r.status:<20}  {seats:>6}  {fare:>10}"
        )
    typer.echo("")
