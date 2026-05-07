# NetRadar Backend

This directory contains the Flask API and background monitor that powers NetRadar.

## High-level architecture

1. `run.py` boots Flask and starts the background monitor thread.
2. `app/services/monitor.py` runs check cycles on a fixed interval.
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
  - Response payload: `data` (array of raw check rows).

- `GET /history?limit=<int>`
  - Returns newest raw checks across all services.
  - Default `limit`: `100`.
  - Response payload: `data` (array of raw check rows).

- `GET /history/24h`
  - Returns raw checks from the last 24 hours.
  - Response payload: `data` (array of raw check rows).

- `GET /service/<service>?limit=<int>`
  - Returns newest raw checks for a specific service.
  - Default `limit`: `50`.
  - Response payload: `service`, `data`.

- `GET /services`
  - Returns static service metadata loaded from `services.json`.
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
