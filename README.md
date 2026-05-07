# NetRadar

NetRadar is an open-source internet service monitoring dashboard focused on service accessibility.

It has two parts:
- `backend/`: a Flask API + background monitor that checks services and stores results.
- `frontend/`: a Next.js dashboard that shows live and historical status.

## What This Project Shows

- Live status of many popular services (Iranian and international).
- Color-coded status timelines (bucket view) for quick health checks.
- Dedicated page per service at `/<service-domain>`.
- Daily historical status using aggregated daily data.
- Latency and jitter charts (6h / 12h / 24h).
- Data export endpoints (up to 90 days) for raw and daily summary data.

## How It Works

1. The backend monitor runs continuously (every few seconds).
2. For each service, it performs DNS, TCP/HTTP(S), and ping checks.
3. Raw check results are stored in `backend/netradar.db`.
4. Daily aggregates are generated into `backend/netradar_daily.db`.
5. The frontend calls backend APIs and renders the dashboard.

## Quick Start

### Prerequisites

- Python 3.10+ (recommended)
- Node.js 18+ and npm

### 1) Clone and enter the repository

Clone the repo and open it in your preferred IDE.

### 2) Start backend (Terminal 1)

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

### 3) Start frontend (Terminal 2)

Open a **new terminal window/tab**:

```bash
cd netradar/frontend
npm install
npm run dev
```

Frontend runs on:
- Dashboard: `http://localhost:3001`

## Important: Use Two Terminals

You must run backend and frontend in **separate terminals** at the same time:
- Terminal 1: backend
- Terminal 2: frontend

If backend is not running, frontend pages will load but data requests will fail.

## Configuration Notes

- Service list is defined in `services.json` (root).
- Backend default DB files:
  - `backend/netradar.db` (raw checks)
  - `backend/netradar_daily.db` (daily aggregates)

## Need More Backend Details?

For backend architecture, full endpoint docs, aggregation behavior, and operational details, see:
- [backend/README.md](backend/README.md)

## License

This project is open source under MIT license. 
