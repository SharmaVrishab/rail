#!/usr/bin/env python3
"""CLI entry point for the rail Indian Railways search tool."""

import sys

import typer

from rail.cli.commands.trains import trains
from rail.cli.commands.availability import availability
from rail.cli.commands.pnr import pnr
from rail.cli.commands.live import live
from rail.cli.commands.dates import dates

app = typer.Typer(
    help="Search Indian Railways trains, availability, PNR status, and live running status.",
    add_completion=True,
)

app.command(name="trains")(trains)
app.command(name="availability")(availability)
app.command(name="pnr")(pnr)
app.command(name="live")(live)
app.command(name="dates")(dates)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Show help when no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        ctx.get_help()
        raise typer.Exit()


def cli() -> None:
    """Entry point for the rail CLI."""
    args = sys.argv[1:]
    if not args:
        sys.argv.append("--help")

    known_commands = {"trains", "availability", "pnr", "live", "dates", "--help", "-h"}
    if args and args[0] not in known_commands:
        # Treat bare arguments as a trains search (e.g. `rail NDLS BCT 2025-06-01`)
        sys.argv.insert(1, "trains")

    app()


if __name__ == "__main__":
    cli()
