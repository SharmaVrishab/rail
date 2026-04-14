"""CLI command functions."""

from rail.cli.commands.trains import trains
from rail.cli.commands.availability import availability
from rail.cli.commands.pnr import pnr
from rail.cli.commands.live import live
from rail.cli.commands.dates import dates

__all__ = ["trains", "availability", "pnr", "live", "dates"]
