"""CLI command: check PNR booking status."""

import json
from typing import Annotated

import typer

from rail.search.pnr import CheckPNR


def pnr(
    pnr_number: Annotated[str, typer.Argument(help="10-digit PNR number")],
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output in JSON format"),
    ] = False,
) -> None:
    """Check PNR booking status.

    Example:
        rail pnr 1234567890
        rail pnr 1234567890 --json
    """
    pnr_number = pnr_number.strip()
    if len(pnr_number) != 10 or not pnr_number.isdigit():
        typer.echo("Error: PNR must be a 10-digit number.", err=True)
        raise typer.Exit(1)

    try:
        status = CheckPNR().check(pnr_number)
    except Exception as e:
        typer.echo(f"Error fetching PNR status: {e}", err=True)
        raise typer.Exit(1) from e

    if not status:
        if output_json:
            typer.echo(json.dumps({"error": "PNR not found or service unavailable"}))
        else:
            typer.echo("PNR not found or service is currently unavailable.")
        raise typer.Exit(1)

    if output_json:
        typer.echo(json.dumps(status.model_dump()))
        return

    typer.echo(f"\nPNR: {status.pnr_number}")
    typer.echo(f"Train: {status.train_number} — {status.train_name}")
    typer.echo(f"Date: {status.journey_date}")
    typer.echo(f"Route: {status.from_station} → {status.to_station}")
    typer.echo(f"Class: {status.train_class}  |  Quota: {status.quota}")
    typer.echo(f"Chart Prepared: {'Yes' if status.chart_prepared else 'No'}\n")

    if status.passengers:
        typer.echo(f"{'#':<3}  {'Seat':<8}  {'Booking Status':<20}  {'Current Status':<20}  Coach")
        typer.echo("-" * 70)
        for i, p in enumerate(status.passengers, 1):
            typer.echo(
                f"{i:<3}  {p.get('seat_number', '—'):<8}  "
                f"{p.get('booking_status', '—'):<20}  "
                f"{p.get('current_status', '—'):<20}  "
                f"{p.get('coach', '—')}"
            )
    typer.echo("")
