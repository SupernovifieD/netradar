# NetRadar Backend

This directory contains the Flask API and background monitor that powers NetRadar.

## High-level architecture

1. `run.py` boots Flask and starts the background monitor thread.
2. `app/services/monitor.py` runs schedule-aware due checks with jitter and capped backoff.
3. `app/services/checker.py` performs DNS, HTTP(S), and ping probes for each domain.
4. `app/models.py` writes/reads probe results from `netradar.db`.
5. `app/services/daily_aggregator.py` builds closed-day summaries in `netradar_daily.db`.
6. `app/routes/api.py` exposes raw and aggregated history endpoints.

## Module map

- `config.py`: central runtime configuration values.
- `app/__init__.py`: Flask app factory and startup wiring.
- `app/db.py`: SQLite connection and schema initialization helpers.
- `app/daily_db.py`: schema/connection helpers for daily aggregates DB.
- `app/models.py`: data-access layer for the `checks` table.
- `app/daily_models.py`: read/write layer for daily summaries and intervals.
- `app/routes/api.py`: API blueprint.
- `app/services/checker.py`: probe functions.
- `app/services/daily_aggregator.py`: closed-day aggregation logic.
- `app/services/monitor.py`: scheduler/worker loop.
- `app/services/monitoring_policy.py`: per-service schedule policy parsing.

## Database schema

The backend stores raw checks in `netradar.db`:

- `checks`
  - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
  - `service` (TEXT)
  - `latency` (TEXT)
  - `packet_loss` (TEXT)
  - `dns` (TEXT)
  - `tcp` (TEXT)
  - `status` (TEXT)
  - `probe_reason` (TEXT, nullable)
  - `http_status_code` (INTEGER, nullable)
  - `date` (TEXT, `YYYY-MM-DD`)
  - `time` (TEXT, `HH:MM:SS`)

Indexes:

- `idx_service_datetime` on `(service, date DESC, time DESC)`
- `idx_datetime` on `(date DESC, time DESC)`

Daily aggregates are stored in `netradar_daily.db`:

- `daily_service_stats` (one immutable row per `service + day_utc`)
- `daily_service_intervals` (compressed `DOWN`/`NO_DATA` intervals per day)

Daily classification policy:

- UTC day boundary.
- Closed days only (`day < current_utc_day`).
- Thresholds: `UP >= 95`, `DEGRADED >= 80`, else `DOWN`.
- Existing closed-day rows are not recomputed.
- Backfill window: last 90 closed days.

Runtime SQLite settings (both DBs):

- `WAL` journal mode for better read/write concurrency.
- `busy_timeout=30000` to wait for transient locks before failing.
- Batched insert writes per monitor cycle to reduce lock churn.

Monitor runtime defaults:

- global scheduler tick: `CHECK_INTERVAL = 60s`
- per-service default probe interval: `60s`
- default jitter: `6s`
- default max backoff cap: `600s`
- ping sample count: `4`

Optional per-service schedule config in `services.json`:

```json
{
  "domain": "example.com",
  "name": "Example",
  "group": "International Service",
  "category": "General Services",
  "monitoring": {
    "enabled": true,
    "interval_seconds": 60,
    "jitter_seconds": 6,
    "max_backoff_seconds": 600
  }
}
```

Raw status model remains `UP`/`DOWN`; richer classification is surfaced through:

- `probe_reason`: `OK`, `FORBIDDEN`, `RATE_LIMITED`, `DNS_FAIL`, `TCP_FAIL`, ...
- `http_status_code`: last HTTP response code when available.

## API endpoints

Base URL: `http://localhost:5001/api`

All success responses use this shape:

```json
{ "success": true, ...payload }
```

Validation failures use:

```json
{ "success": false, "error": "..." }
```

### Raw check endpoints

- `GET /status`
  - Returns latest raw check row per service.
  - Response payload: `data` (array of raw check rows, including optional `probe_reason` and `http_status_code`).

- `GET /history?limit=<int>`
  - Returns newest raw checks across all services.
  - Default `limit`: `100`.
  - Response payload: `data` (array of raw check rows with probe reason/code when present).

- `GET /history/24h`
  - Returns raw checks from the last 24 hours.
  - Response payload: `data` (array of raw check rows with probe reason/code when present).

- `GET /service/<service>?limit=<int>`
  - Returns newest raw checks for a specific service.
  - Default `limit`: `50`.
  - Response payload: `service`, `data`.

- `GET /services`
  - Returns static service metadata loaded from `services.json`.
  - Optional filters:
    - `search=<text>` (matches name/domain, case-insensitive)
    - `group=<exact group>`
    - `category=<exact category>`
  - Response payload: `data` (service metadata array).

### Daily aggregate endpoints

- `GET /service/<service>/daily?limit=<int>&before_day=<YYYY-MM-DD>`
  - Returns newest-first daily summaries for one service.
  - Default `limit`: `30`.
  - `before_day` is optional and filters results to days `< before_day`.
  - Response payload: `service`, `data`.
  - Each summary row includes inline `intervals` (`DOWN` and `NO_DATA` windows).
  - Validation: `before_day` must match `YYYY-MM-DD`; `limit` must be positive.

- `GET /daily/services?day=<YYYY-MM-DD>&limit=<int>&offset=<int>`
  - Returns daily summaries for all services for one UTC day.
  - If `day` is omitted, latest aggregated closed day is used.
  - Defaults: `limit=100`, `offset=0`.
  - Response payload: `day`, `data`.
  - Each summary row includes inline `intervals`.
  - Validation: `day` must match `YYYY-MM-DD`; `limit` must be positive; `offset >= 0`.

### Export endpoints (max 90 days)

- `GET /service/<service>/export/raw?days=<int>`
  - Returns raw checks for one service in the last `days` (UTC window).
  - Default: `days=90`.
  - Hard limit: `days <= 90`.
  - Response payload: `service`, `days`, `start_utc`, `end_utc`, `data`.
  - If `days > 90`, API returns an error asking user to contact the administrator.

- `GET /service/<service>/export/daily?days=<int>`
  - Returns daily summary rows for one service in the last `days` closed UTC days.
  - Default: `days=90`.
  - Hard limit: `days <= 90`.
  - Response payload: `service`, `days`, `start_day_utc`, `end_day_utc`, `data`.
  - Rows include inline `intervals`.
  - If `days > 90`, API returns an error asking user to contact the administrator.

### Monitor control and health

- `POST /monitor/start`
  - Starts the in-process background monitor thread.
  - Response payload: `message`.

- `POST /monitor/stop`
  - Stops the in-process background monitor thread.
  - Response payload: `message`.

- `GET /monitor/status`
  - Returns monitor runtime state for this backend process.
  - Response payload: `running`, `thread_alive`.

- `GET /monitor/policy`
  - Returns effective monitor defaults + per-service schedule config.
  - Response payload: `defaults`, `services`.

- `GET /monitor/runtime`
  - Returns per-service in-memory scheduler state.
  - Response payload: `services` including due time, backoff, and last probe reason.

- `GET /health`
  - Basic liveness endpoint.
  - Response payload: `status` (`healthy`).

## Running locally

From `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

API base URL: `http://localhost:5001/api`

## Backend TUI

The backend now includes a Textual TUI with two screens:

1. **Main dashboard**:
   - Lists all services from `services.json`.
   - Shows latest status, probe reason, HTTP code, DNS/TCP, latency, packet loss, backoff, and next due time.
   - Auto-refreshes every 15 minutes.
   - Supports search, scroll, add service, and delete service actions.
2. **Service detail**:
   - Opens from the selected row on the dashboard (`Enter`).
   - Shows service metadata + latest check metrics.
   - Shows 6h status buckets (same color logic as frontend).
   - Shows latency and jitter graphs for the last 6 hours.

### Run the TUI

From `backend/`:

```bash
python tui.py
```

### Main key bindings

- `Enter`: open selected service detail
- `/`: focus search input
- `Esc`: clear search and return focus to table
- `r`: refresh now
- `a`: add service to `services.json`
- `d`: delete selected service from `services.json` (requires typed confirmation)
- `q`: quit

### Detail key bindings

- `b` or `Esc`: back to dashboard
- `r`: refresh now

## CLI Automation Interface

NetRadar provides a deterministic CLI for scripts, CI/CD, and AI agents.

Run from `backend/`:

```bash
python cli.py --help
```

### Global flags

- `--mode local|api` (default: `local`)
- `--api-base-url` (default: `http://localhost:5001/api`)
- `--timeout-sec` (API mode request timeout)
- `--json` (machine-friendly output envelope)
- `--fail-on-empty` (treat empty result as failure)
- `--debug` (print traceback on error)

### Command groups

- `health`
- `services list [--search TEXT] [--group TEXT] [--category TEXT]`
- `status current`
- `history recent [--limit N]`
- `history 24h`
- `history service <domain> [--limit N]`
- `daily service <domain> [--limit N] [--before-day YYYY-MM-DD]`
- `daily services [--day YYYY-MM-DD] [--limit N] [--offset N]`
- `export raw <domain> [--days N<=90] [--out PATH]`
- `export daily <domain> [--days N<=90] [--out PATH]`
- `monitor start|stop|status|policy|runtime` (API mode only)
- `probe service <domain>` (local mode only)
- `ops snapshot <domain> [--history-limit N] [--daily-limit N]`
- `ops gate <domain> [--days N] [--min-uptime PCT] [--max-p95-latency MS]`

### JSON envelope contract (`--json`)

All commands return:

```json
{
  "ok": true,
  "command": "history.service",
  "mode": "local",
  "timestamp_utc": "2026-05-08T08:00:00Z",
  "data": {},
  "meta": {},
  "error": null
}
```

Error responses keep the same envelope with:

```json
{
  "ok": false,
  "error": {
    "code": "SOME_ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

### Exit codes

- `0`: success
- `2`: CLI argument/usage error
- `3`: validation/business-rule error
- `4`: empty result when `--fail-on-empty` is set
- `5`: local runtime/dependency error
- `6`: API returned error response
- `7`: API transport/timeout error
- `8`: unsupported command in selected mode
- `10`: unexpected internal error

### Example automation commands

```bash
# JSON health check
python cli.py --json health

# Gate decision (fails if no data/threshold violations; inspect JSON reasons)
python cli.py --json ops gate google.com --days 30 --min-uptime 99 --max-p95-latency 120

# Remote monitor status
python cli.py --mode api --json monitor status

# Remote monitor policy/runtime introspection
python cli.py --mode api --json monitor policy
python cli.py --mode api --json monitor runtime
```
