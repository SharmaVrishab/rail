"""CLI command: search trains between two stations."""

import json
from typing import Annotated

import typer

from rail.core.parsers import ParseError, parse_quota, parse_sort_by, parse_train_class, resolve_station
from rail.core.builders import build_train_search
from rail.models.indian_railways.base import Quota, SortBy, TrainClass
from rail.search.trains import SearchTrains


def _fmt_duration(minutes: int) -> str:
    """Format minutes as 'Xh Ym'."""
    return f"{minutes // 60}h {minutes % 60:02d}m"


def trains(
    origin: Annotated[str, typer.Argument(help="Origin station code (e.g. NDLS)")],
    destination: Annotated[str, typer.Argument(help="Destination station code (e.g. BCT)")],
    departure_date: Annotated[str, typer.Argument(help="Date of journey (YYYY-MM-DD)")],
    train_class: Annotated[
        str | None,
        typer.Option("--class", "-c", help="Class: SL, 3A, 2A, 1A, CC, EC, 2S (default: all)"),
    ] = None,
    quota: Annotated[
        str,
        typer.Option("--quota", "-q", help="Quota: GN, TQ, PT, LD, SS (default: GN)"),
    ] = "GN",
    sort_by: Annotated[
        str,
        typer.Option("--sort", "-o", help="Sort by: DEP, ARR, DUR (default: DEP)"),
    ] = "DEP",
    top_n: Annotated[
        int,
        typer.Option("--top", "-n", help="Number of results to show (default: 10)"),
    ] = 10,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output in JSON format"),
    ] = False,
) -> None:
    """Search for trains between two stations on a given date.

    Example:
        rail trains NDLS BCT 2025-06-01
        rail trains NDLS BCT 2025-06-01 --class SL --quota GN
        rail trains NDLS MAS 2025-06-15 --class 3A --sort DUR --top 5
    """
    try:
        origin_code = resolve_station(origin)
        dest_code = resolve_station(destination)
        cls = parse_train_class(train_class) if train_class else None
        q = parse_quota(quota)
        sort = parse_sort_by(sort_by)
    except ParseError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    filters = build_train_search(
        origin=origin_code,
        destination=dest_code,
        departure_date=departure_date,
        train_class=cls,
        quota=q,
        sort_by=sort,
    )

    try:
        results = SearchTrains().search(filters, top_n=top_n)
    except Exception as e:
        typer.echo(f"Search failed: {e}", err=True)
        raise typer.Exit(1) from e

    if not results:
        if output_json:
            typer.echo(json.dumps({"trains": [], "count": 0}))
        else:
            typer.echo(f"No trains found between {origin_code} and {dest_code} on {departure_date}.")
        raise typer.Exit(0)

    if output_json:
        typer.echo(json.dumps({"trains": [r.model_dump() for r in results], "count": len(results)}))
        return

    typer.echo(f"\nTrains: {origin_code} → {dest_code}  |  {departure_date}\n")
    typer.echo(f"{'#':<3}  {'Train':<8}  {'Name':<32}  {'Dep':>5}  {'Arr':>5}  {'Dur':>7}  Classes")
    typer.echo("-" * 85)
    for i, r in enumerate(results, 1):
        classes_str = ", ".join(c.value for c in r.classes) if r.classes else "—"
        typer.echo(
            f"{i:<3}  {r.train_number:<8}  {r.train_name[:32]:<32}  "
            f"{r.departure_time:>5}  {r.arrival_time:>5}  {_fmt_duration(r.duration):>7}  {classes_str}"
        )
    typer.echo("")
