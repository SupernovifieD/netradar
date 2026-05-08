# NetRadar Automation Skills

This document is a practical guide for humans and AI agents that need to operate NetRadar programmatically.

## 1) CLI Entry and Modes

Run from `backend/`:

```bash
python cli.py --help
```

Global flags:

- `--mode local|api` (default `local`)
- `--api-base-url http://localhost:5001/api`
- `--timeout-sec <float>`
- `--json` (stable machine envelope)
- `--fail-on-empty`
- `--debug`

Mode behavior:

- `local`: reads local DB/files directly, no backend server required.
- `api`: talks to a running backend over HTTP.
- `monitor start|stop|status`: API mode only.
- `probe service`: local mode only.

## 2) Available CLI Commands

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
- `monitor start|stop|status`
- `probe service <domain>`
- `ops snapshot <domain> [--history-limit N] [--daily-limit N]`
- `ops gate <domain> [--days N] [--min-uptime PCT] [--max-p95-latency MS]`

## 3) JSON Usage Pattern

Use `--json` for automation. Output envelope is stable:

```json
{
  "ok": true,
  "command": "ops.snapshot",
  "mode": "local",
  "timestamp_utc": "2026-05-08T08:00:00Z",
  "data": {},
  "meta": {},
  "error": null
}
```

Error envelope:

```json
{
  "ok": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Message",
    "details": {}
  }
}
```

Recommended machine contract:

- Check process exit code first.
- Parse `ok`.
- On failure, use `error.code` for branching logic.
- Use `meta` to confirm effective args.

## 4) Automation Workflows

### A) CI health and data presence

```bash
python cli.py --json --fail-on-empty status current
```

- Exit `0`: status rows available.
- Exit `4`: no rows (pipeline can fail fast).

### B) Daily SLO gate

```bash
python cli.py --json ops gate google.com --days 30 --min-uptime 99 --max-p95-latency 120
```

- Use `data.passed` and `data.reasons` (`LOW_UPTIME`, `HIGH_P95_LATENCY`, `NO_DAILY_DATA`, ...).

### C) Export for offline analysis

```bash
python cli.py export raw google.com --days 90 --out ./exports/google-raw.json
python cli.py export daily google.com --days 90 --out ./exports/google-daily.json
```

### D) Remote monitor control

```bash
python cli.py --mode api --json monitor status
python cli.py --mode api --json monitor start
python cli.py --mode api --json monitor stop
```

## 5) Reusable Helper Skills (Code-Level)

These helpers are shared and deterministic, designed for future coding agents:

- `backend/app/core/operations.py`
  - Canonical backend operation layer used by API and CLI.
- `backend/app/core/agent_helpers.py`
  - `build_ops_snapshot_payload(...)`
  - `evaluate_gate_payload(...)`
- `backend/app/services_catalog.py`
  - Shared service catalog loader used by API/CLI/TUI.
- `backend/app/cli/transport.py`
  - `LocalTransport` and `ApiTransport` with normalized behavior.

Use these modules instead of duplicating logic in new interfaces.

## 6) Exit Codes (Deterministic)

- `0`: success
- `2`: usage/arg parse error
- `3`: validation/business-rule error
- `4`: empty result with `--fail-on-empty`
- `5`: local runtime/dependency error
- `6`: API returned error
- `7`: transport/timeout error
- `8`: unsupported command in current mode
- `10`: unexpected internal error

## 7) Architectural Philosophy

- One business-logic foundation (`app/core/operations.py`), multiple interfaces (API, CLI, TUI).
- Stable machine output contract for automation.
- Deterministic exit codes and strict validation for CI reliability.
- Explicit mode boundaries to avoid ambiguous side effects.
- Prefer composition (`ops snapshot`, `ops gate`) over ad-hoc script glue.
