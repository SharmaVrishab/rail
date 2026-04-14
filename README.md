# rail — Indian Railways MCP Server and Library

A Python library for programmatic access to Indian Railways data, with a CLI and an MCP server that lets AI assistants (Claude, etc.) search trains, check availability, look up PNR status, and get live running status.

## MCP Server

```bash
pip install "rail[mcp]"

# Run the MCP server on STDIO (for Claude Desktop)
rail-mcp

# Run over HTTP with streaming
rail-mcp-http  # serves at http://127.0.0.1:8000/mcp/
```

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "rail": {
      "command": "rail-mcp"
    }
  }
}
```

After restarting Claude Desktop you can ask things like:
- "Find trains from New Delhi to Mumbai on 15 June in Sleeper class"
- "Check seat availability for train 12951 on 20 June in 3A"
- "What's the PNR status for 1234567890?"
- "Is train 12951 running on time?"
- "Which dates have confirmed Sleeper availability from NDLS to BCT in June?"

### MCP Tools

| Tool | Description |
|---|---|
| `search_trains` | Find trains between two stations on a date |
| `check_availability` | Seat availability by class and quota |
| `check_pnr` | PNR booking status |
| `get_live_status` | Real-time running position and delay |
| `search_dates` | Cheapest / most available dates in a range |

#### `search_trains`

| Parameter | Type | Description |
|---|---|---|
| `origin` | string | Origin station code (e.g. `NDLS`) |
| `destination` | string | Destination station code (e.g. `BCT`) |
| `date` | string | Journey date — YYYY-MM-DD |
| `train_class` | string | SL, 3A, 2A, 1A, CC, EC, 2S — optional, default: all |
| `quota` | string | GN, TQ, PT, LD, SS — default: GN |
| `sort_by` | string | DEP, ARR, DUR — default: DEP |
| `top_n` | int | Max results to return — default: 10 |

#### `check_availability`

| Parameter | Type | Description |
|---|---|---|
| `train_number` | string | Train number (e.g. `12951`) |
| `origin` | string | Boarding station code |
| `destination` | string | De-boarding station code |
| `date` | string | Journey date — YYYY-MM-DD |
| `train_class` | string | SL, 3A, 2A, 1A, CC, EC, 2S |
| `quota` | string | GN, TQ, PT, LD, SS — default: GN |

#### `check_pnr`

| Parameter | Type | Description |
|---|---|---|
| `pnr_number` | string | 10-digit PNR number |

#### `get_live_status`

| Parameter | Type | Description |
|---|---|---|
| `train_number` | string | Train number (e.g. `12951`) |

#### `search_dates`

| Parameter | Type | Description |
|---|---|---|
| `origin` | string | Origin station code |
| `destination` | string | Destination station code |
| `start_date` | string | Range start — YYYY-MM-DD |
| `end_date` | string | Range end — YYYY-MM-DD |
| `train_class` | string | SL, 3A, 2A, 1A, CC, EC, 2S |
| `quota` | string | GN, TQ, PT, LD, SS — default: GN |
| `train_number` | string | Specific train — optional, auto-detected if omitted |
| `sort_by_price` | bool | Sort by fare (true) or availability status (false) |

---

## Quick Start

```bash
pip install rail
```

```bash
# Or with pipx (recommended for CLI-only use)
pipx install rail

rail --help
```

---

## CLI Usage

### Search trains

```bash
# All trains between New Delhi and Mumbai Central on 1 June
rail trains NDLS BCT 2025-06-01

# Filter by class and quota
rail trains NDLS BCT 2025-06-01 --class SL --quota GN

# Sort by duration, show top 5
rail trains NDLS MAS 2025-06-15 --class 3A --sort DUR --top 5

# JSON output
rail trains NDLS BCT 2025-06-01 --json
```

### Check seat availability

```bash
rail availability 12951 NDLS BCT 2025-06-01 --class SL
rail availability 12951 NDLS BCT 2025-06-01 --class 3A --quota TQ
```

### PNR status

```bash
rail pnr 1234567890
rail pnr 1234567890 --json
```

### Live running status

```bash
rail live 12951
rail live 12951 --json
```

### Find availability across a date range

```bash
# Sorted by price (cheapest first)
rail dates NDLS BCT 2025-06-01 2025-06-30 --class SL

# Sorted by availability status
rail dates NDLS BCT 2025-06-01 2025-06-30 --class 3A --quota TQ --status

# Check a specific train
rail dates NDLS MAS 2025-06-01 2025-07-31 --class SL --train 12163
```

### CLI Options Reference

#### `rail trains`

| Option | Short | Description |
|---|---|---|
| `--class` | `-c` | Coach class: SL, 3A, 2A, 1A, CC, EC, 2S |
| `--quota` | `-q` | Booking quota: GN, TQ, PT, LD, SS |
| `--sort` | `-o` | Sort: DEP (departure), ARR (arrival), DUR (duration) |
| `--top` | `-n` | Max results (default: 10) |
| `--json` | | Output as JSON |

#### `rail availability`

| Option | Short | Description |
|---|---|---|
| `--class` | `-c` | Coach class (required) |
| `--quota` | `-q` | Booking quota (default: GN) |
| `--json` | | Output as JSON |

#### `rail dates`

| Option | Short | Description |
|---|---|---|
| `--class` | `-c` | Coach class (default: SL) |
| `--quota` | `-q` | Booking quota (default: GN) |
| `--train` | `-t` | Specific train number |
| `--price / --status` | | Sort by price (default) or availability status |
| `--json` | | Output as JSON |

---

## Reference Data

### Train Classes

| Code | Name |
|---|---|
| SL | Sleeper Class |
| 3A | 3-Tier AC |
| 2A | 2-Tier AC |
| 1A | 1st Class AC |
| CC | AC Chair Car |
| EC | Executive Chair Car |
| 2S | 2nd Sitting (non-AC) |
| FC | First Class (non-AC) |

### Quota Codes

| Code | Name |
|---|---|
| GN | General |
| TQ | Tatkal |
| PT | Premium Tatkal |
| LD | Ladies |
| SS | Senior Citizen |
| HP | Divyaang (Physically Handicapped) |
| YU | Youth |
| DF | Defence |

### Common Station Codes

| Code | Station |
|---|---|
| NDLS | New Delhi |
| BCT | Mumbai Central |
| CSTM | Mumbai CSMT |
| HWH | Howrah (Kolkata) |
| MAS | Chennai Central |
| SBC | Bengaluru City |
| HYB | Hyderabad Deccan |
| SC | Secunderabad |
| PUNE | Pune Junction |
| ADI | Ahmedabad Junction |
| LKO | Lucknow Charbagh |
| JP | Jaipur Junction |
| ASR | Amritsar Junction |
| PNBE | Patna Junction |
| BBS | Bhubaneswar |
| GHY | Guwahati |

---

## Configuration

Set environment variables to configure the data source:

| Variable | Default | Description |
|---|---|---|
| `RAIL_API_PROVIDER` | `ntes` | Data source: `ntes`, `rapidapi`, `railwayapi` |
| `RAIL_API_KEY` | — | API key for third-party providers (RapidAPI, etc.) |
| `RAIL_RATE_LIMIT` | `5` | Max requests per second |

```bash
# Use NTES (default, public, no key required)
rail trains NDLS BCT 2025-06-01

# Use RapidAPI for availability / PNR
RAIL_API_PROVIDER=rapidapi RAIL_API_KEY=your_key rail availability 12951 NDLS BCT 2025-06-01 --class SL
```

---

## Python API

```python
from rail.search import SearchTrains, SearchAvailability, CheckPNR, GetLiveStatus, SearchDates
from rail.core import build_train_search, build_availability_search
from rail.models.indian_railways.base import TrainClass, Quota, SortBy

# Search trains
filters = build_train_search(
    origin="NDLS",
    destination="BCT",
    departure_date="2025-06-01",
    train_class=TrainClass.SL,
    quota=Quota.GENERAL,
    sort_by=SortBy.DEPARTURE_TIME,
)
trains = SearchTrains().search(filters, top_n=10)
for t in trains:
    print(f"{t.train_number}  {t.train_name}  {t.departure_time} → {t.arrival_time}")

# Check seat availability
avail_filters = build_availability_search(
    train_number="12951",
    origin="NDLS",
    destination="BCT",
    departure_date="2025-06-01",
    train_class=TrainClass.THREE_AC,
    quota=Quota.GENERAL,
)
results = SearchAvailability().search(avail_filters)
for a in results:
    print(f"{a.train_class.value}  {a.status}  ₹{a.fare}")

# PNR status
status = CheckPNR().check("1234567890")
if status:
    print(status.train_number, status.journey_date)
    for p in status.passengers:
        print(p["current_status"])

# Live running status
live = GetLiveStatus().get("12951")
if live:
    print(f"At {live.current_station_name}, {live.delay_minutes} min late")

# Availability across a date range
dates = SearchDates().search(
    origin="NDLS",
    destination="BCT",
    start_date="2025-06-01",
    end_date="2025-06-30",
    train_class=TrainClass.SL,
    quota=Quota.GENERAL,
    sort_by_price=True,
)
for d in dates[:5]:
    print(f"{d.date}  {d.status}  ₹{d.fare}")
```

---

## Development

```bash
# Clone and install
git clone https://github.com/securitylamb/rail.git
cd rail
uv sync --all-extras

# Run tests
uv run pytest -v

# Lint and format
uv run ruff check .
uv run ruff format .

# Regenerate station enum from CSV
uv run python scripts/generate_station_enum.py

# Run MCP server locally
uv run rail-mcp
```

### Adding Stations

Edit [data/stations.csv](data/stations.csv) (columns: `code,name,city,state`), then regenerate:

```bash
uv run python scripts/generate_station_enum.py
```

---

## License

MIT
