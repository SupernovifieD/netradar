# NetRadar Backend

This directory contains the Flask API and background monitor that powers NetRadar.

## High-level architecture

1. `run.py` boots Flask and starts the background monitor thread.
2. `app/services/monitor.py` runs check cycles on a fixed interval.
3. `app/services/checker.py` performs DNS, HTTP(S), and ping probes for each domain.
4. `app/models.py` writes/reads probe results from SQLite.
5. `app/routes/api.py` exposes the data and monitor control endpoints.

## Module map

- `config.py`: central runtime configuration values.
- `app/__init__.py`: Flask app factory and startup wiring.
- `app/db.py`: SQLite connection and schema initialization helpers.
- `app/models.py`: data-access layer for the `checks` table.
- `app/routes/api.py`: API blueprint.
- `app/services/checker.py`: probe functions.
- `app/services/monitor.py`: scheduler/worker loop.

## Database schema

The backend stores checks in one table:

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

Runtime SQLite settings:

- `WAL` journal mode for better read/write concurrency.
- `busy_timeout=30000` to wait for transient locks before failing.
- Batched insert writes per monitor cycle to reduce lock churn.

## Running locally

From `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

API base URL: `http://localhost:5001/api`
