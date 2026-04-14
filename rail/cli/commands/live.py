"""CLI command: get live running status of a train."""

import json
from typing import Annotated

import typer

from rail.search.live import GetLiveStatus


def live(
    train_number: Annotated[str, typer.Argument(help="Train number (e.g. 12951)")],
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output in JSON format"),
    ] = False,
) -> None:
    """Get real-time running status of a train.

    Example:
        rail live 12951
        rail live 12951 --json
    """
    train_number = train_number.strip()

    try:
        status = GetLiveStatus().get(train_number)
    except Exception as e:
        typer.echo(f"Error fetching live status: {e}", err=True)
        raise typer.Exit(1) from e

    if not status:
        if output_json:
            typer.echo(json.dumps({"error": "Live status unavailable"}))
        else:
            typer.echo("Live status is currently unavailable for this train.")
        raise typer.Exit(1)

    if output_json:
        typer.echo(json.dumps(status.model_dump(mode="json")))
        return

    delay_str = (
        "On time"
        if status.delay_minutes == 0
        else (
            f"{status.delay_minutes} min late"
            if status.delay_minutes > 0
            else f"{abs(status.delay_minutes)} min early"
        )
    )

    typer.echo(f"\nTrain: {status.train_number} — {status.train_name}")
    typer.echo(f"Current station: {status.current_station_name} ({status.current_station})")
    typer.echo(f"Delay: {delay_str}")
    typer.echo(f"Last updated: {status.last_updated.strftime('%Y-%m-%d %H:%M')}")

    if status.next_station:
        typer.echo(f"Next station: {status.next_station_name or status.next_station} ({status.next_station})")
    if status.expected_arrival_next:
        typer.echo(f"Expected arrival at next: {status.expected_arrival_next.strftime('%H:%M')}")
    if status.distance_from_source is not None:
        typer.echo(f"Distance from origin: {status.distance_from_source} km")
    typer.echo("")
