"""MCP module for the rail package.

The MCP server depends on optional extras (``rail[mcp]``). When those
packages are not installed the public names are simply unavailable and
importing this package will not raise an error.
"""

try:
    from rail.mcp.server import (
        mcp,
        run,
        run_http,
        search_trains,
        check_availability,
        check_pnr,
        get_live_status,
        search_dates,
    )

    __all__ = [
        "mcp",
        "run",
        "run_http",
        "search_trains",
        "check_availability",
        "check_pnr",
        "get_live_status",
        "search_dates",
    ]
except ModuleNotFoundError:
    __all__: list[str] = []
