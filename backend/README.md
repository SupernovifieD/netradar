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

## API additions

- `GET /api/service/<service>/daily?limit=<int>&before_day=<YYYY-MM-DD>`
  - Newest-first daily summaries for one service.
  - Includes inline interval details (`DOWN` and `NO_DATA`).
- `GET /api/daily/services?day=<YYYY-MM-DD>&limit=<int>&offset=<int>`
  - Daily summaries for all services on one UTC day.
  - If `day` is omitted, latest aggregated closed day is returned.

## Running locally

From `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

API base URL: `http://localhost:5001/api`
