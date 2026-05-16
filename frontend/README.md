# NetRadar Frontend

This is the Next.js frontend for NetRadar.

It renders:
- Home dashboard (`/`) with service cards and status timelines.
- Service detail page (`/:service-domain`) with daily calendar, detailed buckets, and latency/jitter charts.
- Static pages (`/about`, `/faq`, `/changelog`).

## Tech Stack

- Next.js (App Router)
- React + TypeScript
- Plain CSS (`app/globals.css`)

## Run Locally

From `frontend/`:

```bash
npm install
npm run dev
```

Frontend runs on `http://localhost:3001`.

Important:
- Backend must be running at `http://localhost:5001` for default local setup.
- Browser requests use the frontend `/api/...` proxy by default.
- Server-side requests use `NETRADAR_API_INTERNAL_URL` or `NETRADAR_API_URL` when set.

## Directory Guide

- `app/page.tsx`: home page shell.
- `app/[service]/page.tsx`: service detail page.
- `app/api/[...path]/route.ts`: same-origin proxy to backend API.
- `app/components/`: UI building blocks.
- `lib/api.ts`: frontend data fetching + bucketing + color classification.
- `lib/config.ts`: typed config reader with fallbacks.
- `netradar.config.json`: frontend configuration file.
- `types/service.ts`: TypeScript contracts for API data.
- `app/globals.css`: global styles and CSS variables.

## Configuration (Full Reference)

The frontend reads configuration from:
- `frontend/netradar.config.json`

Parsing and fallback logic lives in:
- `frontend/lib/config.ts`

If a key is missing or invalid type, `lib/config.ts` falls back to safe built-in defaults.

### Schema

```json
{
  "shared": {
    "status_timeline": {
      "up_stable_threshold_pct": 80,
      "up_degraded_threshold_pct": 20,
      "high_latency_threshold_ms": 40,
      "fallback_token": "grey",
      "outage_token": "red",
      "tokens": {
        "green": { "hex": "#2ecc71", "label": "Stable" },
        "darkgreen": { "hex": "#1e8c4e", "label": "Minor instability" },
        "orange": { "hex": "#e67e22", "label": "High latency" },
        "blue": { "hex": "#3498db", "label": "No ping data" },
        "darkblue": { "hex": "#1f5f8b", "label": "Partial response" },
        "red": { "hex": "#e74c3c", "label": "Outage" },
        "grey": { "hex": "#555", "label": "No data" }
      }
    }
  },
  "backend": {
    "runtime": {
      "daily_backfill_days": 90,
      "check_interval_seconds": 60,
      "default_service_interval_seconds": 60,
      "default_service_jitter_seconds": 6,
      "default_max_backoff_seconds": 600,
      "max_workers": 20
    },
    "sqlite": {
      "timeout_seconds": 30.0,
      "busy_timeout_ms": 30000
    },
    "checker": {
      "dns_timeout_seconds": 2,
      "http_timeout_seconds": 2,
      "ping_count": 4,
      "ping_timeout_seconds": 1,
      "http_headers": {
        "User-Agent": "NetRadar/1.0 (+https://github.com/netradar)",
        "Accept": "*/*"
      }
    },
    "daily_aggregation": {
      "algo_version": 1,
      "status_up_threshold_pct": 95.0,
      "status_degraded_threshold_pct": 20.0
    },
    "export": {
      "max_days": 90
    },
    "api_defaults": {
      "history_limit": 100,
      "service_history_limit": 50,
      "service_daily_limit": 30,
      "daily_services_limit": 100,
      "daily_services_offset": 0,
      "export_days": 90
    },
    "cli": {
      "default_api_base_url": "http://localhost:5001/api",
      "default_timeout_seconds": 10.0,
      "ops_snapshot_history_limit": 100,
      "ops_snapshot_daily_limit": 30,
      "ops_gate_days": 30,
      "ops_gate_min_uptime": 99.0,
      "ops_gate_max_p95_latency": 120.0
    },
    "tui": {
      "dashboard_refresh_seconds": 900,
      "detail_refresh_seconds": 60,
      "detail_history_limit": 10000,
      "detail_bucket_count": 12,
      "detail_bucket_marker_step": 2,
      "detail_window_hours": 6,
      "line_colors": {
        "latency": "#4ea3ff",
        "jitter": "#ffd166"
      },
      "metric_thresholds_ms": {
        "latency": {
          "good_lt": 40,
          "warning_lt": 100
        },
        "jitter": {
          "good_lt": 5,
          "warning_lt": 20
        }
      },
      "backoff_warning_seconds": 180
    }
  },
  "frontend": {
    "api": {
      "default_browser_base": "/api",
      "default_server_base": "http://localhost:5001/api",
      "default_internal_base": "http://localhost:5001/api"
    },
    "timeline": {
      "bucket_count": 48,
      "mobile_bucket_count": 24,
      "bucket_window_minutes": 30,
      "outage_consecutive_red_buckets": 4,
      "marker_every_buckets": 4
    },
    "service_data": {
      "history_limit": 8000,
      "daily_limit": 120,
      "default_export_days": 90
    },
    "refresh": {
      "service_list_ms": 60000,
      "service_detail_ms": 120000,
      "clock_ms": 1000
    },
    "charts": {
      "strokes": {
        "latency": "#4ea3ff",
        "jitter": "#ffd166"
      }
    },
    "support_highlight": {
      "min_delay_ms": 15000,
      "max_delay_ms": 45000,
      "pulse_duration_ms": 2000
    },
    "calendar_colors": {
      "up_cell_bg": "#1e8c4e",
      "up_cell_fg": "#ebfff3",
      "degraded_cell_bg": "#a0611f",
      "degraded_cell_fg": "#fff5ea",
      "down_cell_bg": "#8f2d27",
      "down_cell_fg": "#ffecec",
      "nodata_cell_bg": "#d9d9d9",
      "nodata_cell_fg": "#3f3f3f",
      "future_cell_bg": "#252525",
      "future_cell_fg": "#9f9f9f",
      "today_ring": "#f2f2f2"
    }
  }
}
```

### Key-by-Key Behavior

`shared.status_timeline`:
- `up_stable_threshold_pct`: threshold used by `determineColor(...)` for stable classification.
- `up_degraded_threshold_pct`: lower threshold used by `determineColor(...)`.
- `high_latency_threshold_ms`: latency threshold for orange/high-latency branch.
- `fallback_token`: fallback token when no branch matches.
- `outage_token`: token used for outage classification and outage badges.
- `tokens.<token>.hex`: timeline/calendar/UI color values.
- `tokens.<token>.label`: user-visible status labels (tooltips/guide).

`backend.runtime`:
- Monitor scheduler defaults, backfill window, and worker count.

`backend.sqlite`:
- SQLite timeout settings used by backend DB connections.

`backend.checker`:
- DNS/HTTP/ping probe timeouts and request headers.

`backend.daily_aggregation`:
- Daily status thresholds and aggregation algorithm version.

`backend.export`:
- Backend hard cap for export days.

`backend.api_defaults`:
- API default query limits/offsets/days when query params are omitted.

`backend.cli`:
- CLI defaults for API URL, timeout, and ops commands.

`backend.tui`:
- Backend TUI refresh intervals, bucket/chart rendering defaults, and thresholds.

`frontend.api`:
- `default_browser_base`: browser-side API base (`/api` proxy by default).
- `default_server_base`: server-side API base fallback.
- `default_internal_base`: fallback for the frontend proxy route target.

`frontend.timeline`:
- `bucket_count`: total buckets on desktop service timelines.
- `mobile_bucket_count`: bucket count shown on mobile cards/details.
- `bucket_window_minutes`: bucket width in minutes.
- `outage_consecutive_red_buckets`: outage badge trigger depth.
- `marker_every_buckets`: time marker spacing on timeline bars.

`frontend.service_data`:
- `history_limit`: raw checks fetch limit for detail/card generation.
- `daily_limit`: daily summary fetch limit for service page.
- `default_export_days`: default days used by export buttons.

`frontend.refresh`:
- `service_list_ms`: dashboard service list auto-refresh interval.
- `service_detail_ms`: service detail auto-refresh interval.
- `clock_ms`: header clock tick interval.

`frontend.charts.strokes`:
- `latency`: latency line chart stroke color.
- `jitter`: jitter line chart stroke color.

`frontend.support_highlight`:
- `min_delay_ms`: minimum delay before support button pulse.
- `max_delay_ms`: maximum delay before support button pulse.
- `pulse_duration_ms`: highlight pulse duration.

`frontend.calendar_colors`:
- Colors for status cells, text, and today ring in service-day calendar.

## API Base Resolution Order

In `frontend/lib/api.ts`:
- Browser requests: `NEXT_PUBLIC_NETRADAR_API_URL` -> `frontend.api.default_browser_base`
- Server-side requests: `NETRADAR_API_INTERNAL_URL` -> `NETRADAR_API_URL` -> `frontend.api.default_server_base`

In `frontend/app/api/[...path]/route.ts`:
- Proxy target: `NETRADAR_API_INTERNAL_URL` -> `NETRADAR_API_URL` -> `frontend.api.default_internal_base`

## Data Flow (High-Level)

1. `lib/api.ts` fetches metadata/history/daily summaries.
2. Raw checks are grouped into time buckets (`bucket_window_minutes`).
3. `determineColor(...)` maps each bucket to a status token.
4. Components render tokens via config-driven token labels and hex values.
5. `app/layout.tsx` injects CSS variables from config for global color usage.

Raw check `date`/`time` fields from the API are UTC. The frontend parses them as UTC and displays labels in the viewer's browser timezone.

## Important Notes

- `frontend/netradar.config.json` is currently a shared settings file used by both frontend and backend.
- Backend default config path resolves to this file via `backend/config.py` (`../frontend/netradar.config.json`).
- Token IDs are currently code-coupled: `green`, `darkgreen`, `orange`, `blue`, `darkblue`, `red`, `grey`.
- If you rename token keys in config, update logic that emits or references token IDs.
- Backend also reads `frontend.timeline.bucket_window_minutes` for bucket sizing, so timeline window edits affect both frontend and backend bucketing behavior.

## Safe Change Workflow

1. Edit `frontend/netradar.config.json`.
2. If you changed backend-relevant keys (`backend.*` or `shared.*`), restart backend.
3. If you changed frontend-rendered values, restart `npm run dev` if needed and rebuild Docker frontend images for deployments.
4. Run checks:

```bash
npm run lint
npm run build
```

For Dockerized deployments:

```bash
docker compose up --build
```

## Build & Quality

```bash
npm run lint
npm run build
```
