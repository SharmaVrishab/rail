# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Rail is a Python library for Indian Railways data with a CLI and MCP server. It provides:

- **CLI interface** (`rail/cli/`) — Typer-based tool with `trains`, `availability`, `pnr`, `live`, and `dates` commands
- **MCP server** (`rail/mcp/`) — FastMCP server with 5 tools for AI assistant integration
- **Core utilities** (`rail/core/`) — Shared parsing and building utilities
- **Search engine** (`rail/search/`) — Train search, availability, PNR, live status, and date search
- **Data models** (`rail/models/`) — Pydantic models for stations, train classes, quotas, and results

## Development Commands

```bash
# Install dependencies
uv sync --all-extras

# Run tests
make test                    # Standard test suite
uv run pytest -vv           # Direct pytest

# Code quality
make lint                   # Check with ruff
make lint-fix               # Auto-fix linting
make format                 # Format with ruff

# MCP server
rail-mcp                    # Run MCP server on STDIO
rail-mcp-http               # Run MCP server over HTTP

# Regenerate station enum from CSV
uv run python scripts/generate_station_enum.py
```

## Architecture Overview

### Core Components

1. **Core Layer** (`rail/core/`)
   - `parsers.py`: Resolve station codes, train classes, quotas, sort options, time ranges
   - `builders.py`: Build `TrainSearchFilters` and `AvailabilityFilters` from user input

2. **Client Layer** (`rail/search/client.py`)
   - Rate-limited HTTP client (5 req/sec default) using curl-cffi
   - Automatic retries with exponential backoff
   - Optional API key injection for third-party providers

3. **Search Engine** (`rail/search/`)
   - `trains.py` — `SearchTrains`: find trains between stations (erail.in / NTES)
   - `availability.py` — `SearchAvailability`: seat availability (IRCTC / RapidAPI)
   - `pnr.py` — `CheckPNR`: PNR booking status
   - `live.py` — `GetLiveStatus`: real-time train running position
   - `dates.py` — `SearchDates`: availability across a date range

4. **Data Models** (`rail/models/`)
   - `station.py`: `Station` enum (173 Indian Railway station codes, auto-generated)
   - `indian_railways/base.py`: `TrainClass`, `Quota`, `SortBy`, `TrainResult`, `SeatAvailability`, `PNRStatus`, `LiveStatus`, `DateAvailability`
   - `indian_railways/trains.py`: `TrainSearchFilters`
   - `indian_railways/availability.py`: `AvailabilityFilters`

5. **MCP Server** (`rail/mcp/server.py`)
   - Tools: `search_trains`, `check_availability`, `check_pnr`, `get_live_status`, `search_dates`
   - Config via env vars: `RAIL_API_PROVIDER`, `RAIL_API_KEY`, `RAIL_RATE_LIMIT`

6. **CLI** (`rail/cli/`)
   - Commands: `trains`, `availability`, `pnr`, `live`, `dates`
   - All support `--json` for machine-readable output

## Key Files

- `rail/cli/main.py` — CLI entry point and command registration
- `rail/mcp/server.py` — MCP server with all 5 tools
- `rail/core/parsers.py` — Shared parsing utilities
- `rail/core/builders.py` — Shared filter builders
- `rail/search/trains.py` — Train search implementation
- `rail/search/client.py` — HTTP client with rate limiting
- `rail/models/indian_railways/base.py` — Core enums and result models
- `data/stations.csv` — Station data source (edit here, then regenerate enum)
- `pyproject.toml` — Package config and entry points

## MCP Tool Reference

### `search_trains`
Find trains between two stations on a date.
- `origin`, `destination` — station codes (e.g. `NDLS`, `BCT`)
- `date` — YYYY-MM-DD
- `train_class` — SL, 3A, 2A, 1A, CC, EC, 2S (optional)
- `quota` — GN, TQ, PT, LD, SS (default: GN)
- `sort_by` — DEP, ARR, DUR (default: DEP)

### `check_availability`
Seat availability for a specific train.
- `train_number`, `origin`, `destination`, `date`, `train_class`, `quota`

### `check_pnr`
PNR booking status. `pnr_number` — 10-digit string.

### `get_live_status`
Real-time running position. `train_number`.

### `search_dates`
Availability and fares across a date range.
- `origin`, `destination`, `start_date`, `end_date`, `train_class`, `quota`
- `train_number` — optional, auto-detected if omitted
- `sort_by_price` — bool

## Code Style

- **Linting/Formatting**: Ruff, 100-char line length, 4-space indent
- **Type hints**: Python 3.10+ with full annotations
- **Docstrings**: Google-style
- **Testing**: pytest, no external API calls in unit tests
