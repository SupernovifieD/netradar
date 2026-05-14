import Link from "next/link";
import Footer from "../components/Footer";

export default function ChangelogPage() {
  return (
    <div className="simple-page">
      <div className="box simple-header">
        <Link href="/" className="back-button">
          ← Back to home
        </Link>
      </div>

      <div className="box simple-content">
        <h1>Changelog</h1>

        <h3>Unreleased</h3>
        <p>No unreleased changes yet.</p>

        <h3>v0.1.1</h3>
        <p>2026-05-14</p>
        <p>Self-hosting, display-time, and service-management maintenance release.</p>

        <h4>Added</h4>
        <ul>
          <li>
            Docker Compose self-hosting setup with backend and frontend images, persistent SQLite
            storage, mounted <code>services.json</code>, backend healthcheck, and a frontend API
            proxy for container networking.
          </li>
          <li>
            Environment-based backend runtime configuration for database paths, services catalog
            path, host/port, and scheduler defaults.
          </li>
          <li>
            CLI service catalog mutation commands in local mode:
            <code>services add</code>, <code>services update</code>, and{" "}
            <code>services remove --yes</code>.
          </li>
          <li>
            Backend TUI detail-screen quit shortcut: <code>q</code> now exits directly from
            service detail screen.
          </li>
          <li>README TODO and research sections for known follow-up work.</li>
        </ul>

        <h4>Changed</h4>
        <ul>
          <li>
            Raw check timestamps remain stored in UTC, while frontend displays use the browser
            timezone and backend terminal/TUI/CLI displays use <code>NETRADAR_DISPLAY_TIMEZONE</code>{" "}
            or <code>TZ</code>.
          </li>
          <li>
            Docker backend images now include timezone data and default display timezone
            configuration to UTC unless overridden.
          </li>
          <li>
            Frontend build/runtime configuration now supports standalone Next.js container output
            and binding to <code>0.0.0.0</code>.
          </li>
          <li>
            Backend TUI add-service modal is now a smaller, center-aligned panel with centered
            action buttons.
          </li>
          <li>Backend TUI add-service panel background is now fully black for clarity.</li>
          <li>
            Header description now explicitly explains service timeline direction: oldest on the
            left, newest on the right.
          </li>
          <li>
            Daily aggregate status policy updated: <code>DEGRADED</code> now covers 20% to &lt;95%
            uptime, and <code>NO_DATA</code> is used when a closed day has zero observed seconds.
          </li>
          <li>
            Daily DB initialization now migrates legacy <code>daily_service_stats</code>{" "}
            constraints to allow <code>NO_DATA</code>.
          </li>
        </ul>

        <h4>Fixed</h4>
        <ul>
          <li>
            Backend TUI detail-screen refresh behavior no longer triggers a near-immediate extra
            auto-refresh after entering/switching services.
          </li>
          <li>
            Detail screen now refreshes once on entry, then continues on the normal interval;
            manual refresh is still available.
          </li>
          <li>Removed leftover unused time-marker label rendering line in detail buckets.</li>
          <li>
            Frontend outage badge logic now triggers only when the latest 4 buckets are red. If
            the newest bucket is not red, outage is not shown.
          </li>
          <li>
            Frontend service-card status ribbons now render buckets and time markers in matching
            chronological order (oldest on left, newest on right).
          </li>
          <li>
            Service-page calendar now distinguishes future days from no-data days: future days use
            dark gray, while no-data historical days use pale gray.
          </li>
          <li>
            Suppressed noisy urllib3 <code>InsecureRequestWarning</code> entries emitted during
            HTTPS reachability probes with certificate verification disabled.
          </li>
        </ul>

        <h3>v0.1.0</h3>
        <p>2026-05-08</p>
        <p>Initial public release of NetRadar.</p>

        <h4>Added</h4>
        <ul>
          <li>Flask backend API, Next.js frontend dashboard, and SQLite persistence.</li>
          <li>Continuous DNS, HTTP(S), and ping monitoring pipeline.</li>
          <li>Raw history APIs for status, recent checks, 24-hour history, and per-service history.</li>
          <li>Daily aggregate layer with closed-day UTC summaries and interval compression.</li>
          <li>Raw and daily export endpoints (up to 90 days).</li>
          <li>Dedicated frontend service pages with calendar, status ribbon, and latency/jitter graphs.</li>
          <li>Responsive mobile layout refinements for header, control bar, and service visualization.</li>
          <li>Backend Textual TUI with dashboard/detail screens and service catalog management.</li>
          <li>Deterministic automation CLI with local/API modes, JSON envelope, and ops helpers.</li>
          <li>Project documentation (`README`, backend/frontend docs, `skills.md`) and MIT license.</li>
        </ul>

        <h4>Changed</h4>
        <ul>
          <li>Project migrated to full English/LTR presentation and international service metadata.</li>
          <li>Backend refactored into clearer modular layers with stronger documentation.</li>
          <li>Shared page layout consistency improved across home, service, and static pages.</li>
        </ul>

        <h4>Fixed</h4>
        <ul>
          <li>Improved long-running SQLite stability with WAL/timeout/write-pattern hardening.</li>
          <li>Addressed service-page and graph default-window regressions.</li>
          <li>Resolved TUI search lock/cancel and detail-screen bucket/graph layout issues.</li>
        </ul>

        <h4>Hardened Monitoring Policy</h4>
        <ul>
          <li>Safer defaults: `CHECK_INTERVAL=60`, `PING_COUNT=4`, `MAX_BACKOFF_SECONDS=600`.</li>
          <li>Per-service optional monitoring schedule (`enabled`, `interval`, `jitter`, `max_backoff`).</li>
          <li>Due-based scheduling with jitter and capped exponential backoff.</li>
          <li>Added raw-check metadata fields: `probe_reason`, `http_status_code`.</li>
          <li>Separated restriction states (`403/429`) from hard unreachability diagnosis.</li>
          <li>Added monitor policy/runtime introspection endpoints for API and CLI usage.</li>
        </ul>
      </div>

      <Footer />
    </div>
  );
}
