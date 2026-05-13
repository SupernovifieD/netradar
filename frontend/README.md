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

Important: backend must be running at `http://localhost:5001` for the default local setup.
Browser requests use the frontend `/api/...` proxy by default, and server-side rendering uses
`NETRADAR_API_INTERNAL_URL` or `NETRADAR_API_URL` when set.

## Directory Guide

- `app/page.tsx`: home page shell.
- `app/[service]/page.tsx`: service detail page.
- `app/api/[...path]/route.ts`: same-origin proxy to the backend API.
- `app/components/`: UI building blocks.
- `lib/api.ts`: frontend data fetching + bucketing + core color logic.
- `types/service.ts`: TypeScript contracts for API data.
- `app/globals.css`: all global styles and color tokens.

## Data Flow (High-Level)

1. `lib/api.ts` fetches:
   - `/api/services` for metadata
   - `/api/history/24h` or `/api/service/:name` for raw checks
   - `/api/service/:name/daily` for daily aggregate summaries
2. Raw checks are grouped into 30-minute buckets in `lib/api.ts`.
3. Each bucket gets a color token from `determineColor(...)`.
4. Components render color tokens as timeline blocks, legends, and tooltips.

## Coloring Logic

### 1) Bucket color classification (core logic)

Location: `frontend/lib/api.ts` → `determineColor(upPercent, avgLatency)`

Rules (exact current behavior):

- `green`: `upPercent >= 80` and `avgLatency < 40`
- `darkgreen`: `20 <= upPercent < 80` and `avgLatency < 40`
- `orange`: `upPercent >= 80` and `avgLatency >= 40`
- `blue`: `upPercent >= 80` and no latency data (`avgLatency === null`)
- `darkblue`: `20 <= upPercent` and no latency data (`avgLatency === null`)
- `red`: `upPercent < 20`
- `grey`: fallback / no data

These color keys are the canonical status tokens used by timeline rendering.

### 2) Bucket color-to-hex + text mapping

Location: `frontend/app/components/StatusBar.tsx`

- `colorToHex(...)` maps tokens (`green`, `darkgreen`, etc.) to hex values used in bars.
- `translateStatus(...)` maps tokens to tooltip labels.

If you add or rename a token in `determineColor`, update both functions.

### 3) Color guide text block

Location: `frontend/app/components/ColorGuide.tsx`

This is the lightweight user-facing legend shown in header/service pages. Keep it aligned with the status model used in `determineColor` and `StatusBar`.

### 4) Daily calendar colors (service page)

Locations:
- Logic: `frontend/app/components/ServiceStatusCalendar.tsx`
- CSS: `frontend/app/globals.css`

Mapping uses backend daily aggregate status (`overall_status`):

- `UP` → `.service-calendar-cell--up`
- `DEGRADED` → `.service-calendar-cell--degraded`
- `DOWN` → `.service-calendar-cell--down`
- `NO_DATA` (or missing day summary) → `.service-calendar-cell--nodata` (pale gray)

### 5) Chart line colors

Location: `frontend/app/[service]/page.tsx`

- Jitter line `stroke="#ffd166"`
- Latency line `stroke="#4ea3ff"`

## How to Modify Colors Safely

If you want to tune status behavior, change files in this order:

1. Update threshold rules in `lib/api.ts` (`determineColor`).
2. Update token rendering in `StatusBar.tsx` (`colorToHex`, `translateStatus`).
3. Update `ColorGuide.tsx` wording if the meaning changed.
4. If daily meanings changed, update `ServiceStatusCalendar.tsx` and related calendar CSS classes.
5. Run checks:

```bash
npm run lint
npm run build
```

## Other Useful Customization Points

- Bucket width/time span:
  - `HALF_HOUR_MS` and bucket generation in `lib/api.ts`.
- Desktop vs mobile bucket count on cards:
  - Home: `ServiceList.tsx` (mobile slices last 24 buckets)
  - Service page: `[service]/page.tsx` (same behavior)
- Refresh intervals:
  - Home list refresh: `ServiceList.tsx` (currently 60s)
  - Service page refresh: `[service]/page.tsx` (currently 120s)

## Build & Quality

```bash
npm run lint
npm run build
```

Use these before committing UI or color-rule changes.
