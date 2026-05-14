# NetRadar

NetRadar is an open-source dashboard for monitoring internet service availability and basic performance.

It has two parts:
- `backend/`: a Flask API + background monitor that checks services and stores results.
- `frontend/`: a Next.js dashboard that shows live and historical status.

## What This Project Shows

- Live status of popular international services.
- Color-coded status timelines (bucket view) for quick health checks.
- Dedicated page per service at `/<service-domain>`.
- Daily historical status using aggregated daily data.
- Latency and jitter charts (6h / 12h / 24h).
- Data export endpoints (up to 90 days) for raw and daily summary data.

## How It Works

1. The backend monitor runs continuously on a schedule-aware loop.
2. Each service is probed when due (default every 60 seconds) with jitter and capped backoff.
3. For each due service, NetRadar performs DNS, TCP/HTTP(S), and ping checks.
4. Probe outcomes include reason metadata such as `OK`, `FORBIDDEN`, `RATE_LIMITED`, or failure reasons.
5. Raw check results are stored in SQLite (`backend/netradar.db` locally, `/data/netradar.db` in Docker).
6. Daily aggregates are generated into SQLite (`backend/netradar_daily.db` locally, `/data/netradar_daily.db` in Docker).
7. The frontend calls backend APIs and renders the dashboard.

## Quick Start

### Prerequisites

- Docker with Docker Compose for containerized self-hosting.
- Python 3.10+ plus Node.js 18+ and npm for manual local development.

### 1) Clone and enter the repository

Clone the repo and open it in your preferred IDE.

### 2) Self-host with Docker Compose

This runs the backend, frontend, and persistent SQLite storage:

```bash
docker compose up --build
```

First-time builds need internet access to pull base images and install image dependencies. The
dashboard runs at `http://localhost:3001`; the backend API is exposed at
`http://localhost:5001/api`.

Container data is stored in the `netradar-data` Docker volume. The root `services.json` file is
mounted into the backend container so CLI/TUI service edits and host-side edits use the same
catalog.

Raw check timestamps are stored in UTC. The frontend renders them in the browser's local timezone.
For backend terminal logs, CLI human output, and TUI output in Docker, set a display timezone
before starting:

```bash
NETRADAR_DISPLAY_TIMEZONE=Asia/Tehran docker compose up --build
```

Useful container commands:

```bash
# Stop containers without deleting stored SQLite history
docker compose down

# Run CLI commands inside the backend container
docker compose exec backend python cli.py status current

# Run the TUI inside the backend container
docker compose exec backend python tui.py
```

### 3) Manual local development: start backend (Terminal 1)

Open a terminal and run the following commands:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Backend runs on:
- API: `http://localhost:5001/api`

### 4) Manual local development: start frontend (Terminal 2)

Open a **new terminal window/tab**:

```bash
cd netradar/frontend
npm install
npm run dev
```

Frontend runs on:
- Dashboard: `http://localhost:3001`

## Important: Use Two Terminals

For manual local development, you must run backend and frontend in **separate terminals** at the same time:
- Terminal 1: backend
- Terminal 2: frontend

If backend is not running, frontend pages will load but data requests will fail.

## Optional: Use the Backend TUI (Terminal UI)

If you prefer a terminal dashboard, NetRadar also includes a TUI in `backend/`.

### When to use it

- Use it to monitor services directly in terminal.
- Use it to quickly search services.
- Use it to add/remove services in `services.json` with built-in prompts.

### Important

- The TUI reads data from the backend database.
- To keep data updating continuously, keep `python run.py` running in another terminal.
- If you want backend + TUI together, use **2 terminals**:
  - Terminal 1: `python run.py`
  - Terminal 2: `python tui.py`

### How to run the TUI

From `backend/` (after installing backend requirements):

```bash
cd backend
source .venv/bin/activate
python tui.py
```

### TUI controls (quick guide)

- `Enter`: open selected service details
- `/`: search by service name/domain
- `Esc`: clear search and return to table
- `r`: refresh now
- `a`: add service
- `d`: delete selected service (with confirmation)
- `b` or `Esc` (detail screen): go back
- `q`: quit

## CLI Automation Interface

NetRadar includes a robust automation CLI for scripts, CI/CD, and AI agents.

### Run it

From `backend/`:

```bash
source .venv/bin/activate
python cli.py --help
```

### Quick examples

```bash
# Health check
python cli.py health

# Current status for all services
python cli.py status current

# Recent history
python cli.py history recent --limit 200

# Daily history for one service
python cli.py daily service google.com --limit 60

# Export raw data and save it
python cli.py export raw google.com --days 30 --out ./exports/google-raw-30d.json

# JSON mode for automation
python cli.py --json ops snapshot google.com --history-limit 200 --daily-limit 30

# Add a new service to services.json (local mode only)
python cli.py services add example.com --name "Example" --group "International Service" --category "General Services"

# Update an existing service (local mode only)
python cli.py services update example.com --name "Example (Primary)" --interval-seconds 120

# Remove a service (local mode only, requires confirmation flag)
python cli.py services remove example.com --yes
```

### CLI modes

- `--mode local` (default): reads directly from local backend databases/files.
- `--mode api`: calls a running backend API (default URL: `http://localhost:5001/api`, or `NETRADAR_API_BASE_URL` when set).
- `services add|update|remove` are local-mode only because they edit local `services.json`.

Monitor control commands are API-mode only:

```bash
python cli.py --mode api monitor status
python cli.py --mode api monitor policy
python cli.py --mode api monitor runtime
python cli.py --mode api monitor start
python cli.py --mode api monitor stop
```

### Machine-friendly behavior

- Use `--json` for stable automation output envelopes.
- Use `--fail-on-empty` when empty results should fail pipelines.
- Exit codes are deterministic (`0` success, non-zero for validation/API/transport/runtime errors).

## Configuration Notes

- Service list is defined in `services.json` (root).
- Optional per-service policy can be added via `monitoring`:
  - `enabled` (default `true`)
  - `interval_seconds` (default `60`)
  - `jitter_seconds` (default `6`)
  - `max_backoff_seconds` (default `600`)
- Backend default DB files:
  - `backend/netradar.db` (raw checks)
  - `backend/netradar_daily.db` (daily aggregates)
- Docker defaults:
  - `/data/netradar.db` and `/data/netradar_daily.db` inside the backend container.
  - `/config/services.json` inside the backend container.
  - `NETRADAR_API_INTERNAL_URL=http://backend:5001/api` inside the frontend container.
  - `TZ=UTC` unless you override `NETRADAR_DISPLAY_TIMEZONE` or `TZ` for backend terminal/TUI/CLI display time.

## Need More Details?

For backend architecture, full endpoint docs, aggregation behavior, and operational details, see:
- [backend/README.md](backend/README.md)

For frontend coloring logic and notes, see:
- [frontend/README.md](frontend/README.md)

For AI-agent and automation workflows, see:
- [skills.md](skills.md)

## License

This project is open source under MIT license.
