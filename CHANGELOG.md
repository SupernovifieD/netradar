<!-- IMPORTANT: Whenever this file is updated, the frontend changelog page at frontend/app/changelog/page.tsx must be updated with the same release content. -->

# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

Pre-release notes for the next version after `0.1.0`.

### Added

- CLI service catalog mutation commands (local mode):
  - `services add` to add a new service entry to `services.json`
  - `services update` to modify domain/name/group/category/monitoring fields
  - `services remove --yes` to remove a service with explicit confirmation
- Backend TUI detail-screen quit shortcut:
  - `q` now exits directly from service detail screen (no need to go back first).

### Changed

- Backend TUI add-service modal presentation:
  - modal panel is now a smaller, center-aligned box
  - action buttons (`Cancel` / `Save`) are centered
  - add-service panel background is fully black for visual clarity
- Header description now explicitly explains service timeline direction:
  oldest on the left, newest on the right.
- Daily aggregate status policy updated:
  - `DEGRADED` now covers `20%` to `<95%` uptime
  - `NO_DATA` is used when a closed day has zero observed seconds
  - daily DB init now migrates legacy `daily_service_stats` constraints to allow `NO_DATA`

### Fixed

- Backend TUI detail-screen refresh cadence:
  - removed near-immediate extra auto-refresh on screen entry/switch
  - screen now refreshes once on entry, then continues on the normal interval
  - manual refresh remains available any time
- Removed leftover unused time-marker label rendering line in detail bucket section.
- Frontend outage badge logic now triggers only when the latest 4 buckets are red.
  If the newest bucket is not red, outage is not shown.
- Frontend service-card status ribbons now render buckets and time markers in matching
  chronological order (oldest on left, newest on right).
- Service-page calendar now distinguishes future days from no-data days:
  - future days use dark gray
  - no-data historical days use pale gray

## [0.1.0] - 2026-05-08

Initial public release of NetRadar.

### Added

- Full-stack service monitoring platform with:
  - Flask backend API (`backend/`)
  - Next.js frontend dashboard (`frontend/`)
  - SQLite persistence for raw checks (`netradar.db`)
  - Separate SQLite layer for daily aggregates (`netradar_daily.db`)
- Continuous monitoring pipeline with DNS, HTTP(S), and ping checks.
- Raw history API endpoints for current status, recent history, 24-hour history, and per-service history.
- Daily service history feature:
  - Closed UTC day aggregation
  - Daily status classification (`UP`, `DEGRADED`, `DOWN`)
  - Uptime/coverage/latency metrics
  - `DOWN` and `NO_DATA` interval compression
  - 90-day backfill behavior
- Export APIs for raw and daily data (up to 90 days).
- Dedicated service detail pages in frontend (`/<service-domain>`) with:
  - Daily calendar-based status view
  - Per-service status ribbon
  - Latency and jitter graphs
  - Download options
- Responsive mobile-first improvements:
  - Header/control-bar reflow
  - Mobile bucket density tuning (12-hour / 24-bucket display for service cards where required)
- Backend Textual TUI with:
  - Main dashboard
  - Service detail screen
  - Search, scroll, refresh, and navigation
  - Add/remove service management with safety confirmation
- Deterministic automation CLI with:
  - Local and API modes
  - Stable JSON envelope format
  - Structured exit codes
  - Operational helper commands (`ops snapshot`, `ops gate`)
  - Monitor controls (`start`, `stop`, `status`, `policy`, `runtime`)
- Root/project documentation:
  - Root `README.md`
  - Detailed `backend/README.md`
  - Frontend documentation
  - `skills.md` for automation and AI-agent usage
- MIT license.

### Changed

- Repository localization migrated to full English/LTR presentation:
  - UI text, metadata, docs, and alignment
  - Service catalog refined to international-facing entries
- Backend structure refactored to be more Pythonic and modular:
  - Clear separation of DB, models, services, routes, and shared operation layer
  - Improved inline documentation and comments for open-source maintainability
- Footer/layout and shared page UX consistency improved across static pages and service pages.
- Service-card and header behaviors refined for clarity and consistency between index and detail views.

### Fixed

- SQLite lock resilience improvements for long-running backend operation:
  - WAL mode, busy timeout, and safer write patterns
- Service-page defaults and UI regressions (including graph default time window behavior).
- TUI interaction fixes:
  - Search-mode lock/cancel behavior
  - Bucket and graph width/layout consistency on detail screen
  - Better navigation ergonomics

### Hardened Monitoring Policy

- Safer schedule-aware probing defaults:
  - `CHECK_INTERVAL = 60`
  - `PING_COUNT = 4`
  - `DEFAULT_MAX_BACKOFF_SECONDS = 600`
- Per-service optional monitoring policy in `services.json`:
  - `enabled`
  - `interval_seconds`
  - `jitter_seconds`
  - `max_backoff_seconds`
- Due-based scheduler with randomized jitter and capped exponential backoff.
- Explicit probe reason tracking without changing raw `UP/DOWN` model:
  - `probe_reason` and `http_status_code` added to raw checks
  - `403`/`429` surfaced as restriction states instead of hard downtime
- Schedule-aware daily aggregation to avoid false degradation under sparse cadences.
- Monitor introspection endpoints/API support:
  - `GET /api/monitor/policy`
  - `GET /api/monitor/runtime`
