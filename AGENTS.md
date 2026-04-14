# AGENTS.md

## Overview

Rail is a Python library and MCP server for Indian Railways. It provides programmatic access to train search, seat availability, PNR status, and live running status via NTES and IRCTC APIs.

No external databases or caches are required.

## Development commands

All standard commands are in the `Makefile`. Key ones:

- **Install deps**: `uv sync --all-extras`
- **Lint**: `make lint` (ruff)
- **Format**: `make format`
- **Tests**: `make test`
- **CLI**: `uv run rail trains NDLS BCT 2025-06-01 --class SL`
- **MCP STDIO**: `uv run rail-mcp`
- **MCP HTTP**: `uv run rail-mcp-http` (serves at `http://127.0.0.1:8000/mcp/`)

## Testing caveats

- Tests under `tests/search/` hit live APIs (NTES, IRCTC) and may fail in CI/cloud environments due to rate limiting or service availability. All other tests (models, core, MCP) are self-contained and pass reliably.
- Run `uv run pytest -vv --ignore=tests/search/` to skip API-dependent tests.

## MCP server notes

- Five tools: `search_trains`, `check_availability`, `check_pnr`, `get_live_status`, `search_dates`.
- The MCP HTTP endpoint requires `Accept: application/json, text/event-stream` header.
- Configure data source via `RAIL_API_PROVIDER` (`ntes` | `rapidapi` | `railwayapi`) and `RAIL_API_KEY`.

## Package structure

```
rail/
├── cli/          # Typer CLI — commands: trains, availability, pnr, live, dates
├── core/         # Shared parsers and builders
├── mcp/          # FastMCP server
├── models/       # Pydantic models + Station enum
└── search/       # Search implementations (trains, availability, pnr, live, dates)
```
