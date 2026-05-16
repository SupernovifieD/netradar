"""Runtime configuration for the NetRadar backend."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _path_env(name: str, default: Path) -> str:
    """Return a filesystem path from the environment or a local default."""
    value = os.environ.get(name)
    if value is None or not value.strip():
        return str(default)
    return str(Path(value).expanduser())


def _int_env(name: str, default: int, *, minimum: int = 1) -> int:
    """Return a bounded integer from the environment."""
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if parsed < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return parsed


def _load_json_file(path: Path) -> dict[str, Any]:
    """Load a JSON object from ``path``.

    Missing files intentionally fall back to empty settings for compatibility.
    """
    try:
        with path.open(encoding="utf-8") as file:
            loaded = json.load(file)
    except FileNotFoundError:
        return {}

    if not isinstance(loaded, dict):
        raise ValueError(f"Settings file must contain a top-level object: {path}")
    return loaded


def _read_nested(mapping: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = mapping
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _setting_int(
    settings: dict[str, Any],
    path: tuple[str, ...],
    default: int,
    *,
    minimum: int = 0,
) -> int:
    value = _read_nested(settings, path)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, parsed)


def _setting_float(
    settings: dict[str, Any],
    path: tuple[str, ...],
    default: float,
    *,
    minimum: float = 0.0,
) -> float:
    value = _read_nested(settings, path)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, parsed)


def _setting_str(settings: dict[str, Any], path: tuple[str, ...], default: str) -> str:
    value = _read_nested(settings, path)
    if isinstance(value, str) and value.strip():
        return value
    return default


def _setting_dict(
    settings: dict[str, Any],
    path: tuple[str, ...],
    default: dict[str, Any],
) -> dict[str, Any]:
    value = _read_nested(settings, path)
    if isinstance(value, dict):
        return value
    return default


class Config:
    """Application-level configuration values.

    Attributes:
        BASE_DIR: Directory that contains backend source files.
        SETTINGS_FILE: Shared JSON settings file read by backend + frontend.
        DATABASE_PATH: SQLite database location used by data-access modules.
        DAILY_DATABASE_PATH: SQLite database used for daily aggregate history.
        DAILY_BACKFILL_DAYS: Number of recent closed UTC days to backfill.
        SERVICES_FILE: JSON file that lists services/domains to monitor.
        HOST: Interface used by the development server entrypoint.
        PORT: Port used by the development server entrypoint.
        CHECK_INTERVAL: Base scheduler tick in seconds.
        DEFAULT_SERVICE_INTERVAL_SECONDS: Default per-service probe interval.
        DEFAULT_SERVICE_JITTER_SECONDS: Default randomized per-service jitter.
        DEFAULT_MAX_BACKOFF_SECONDS: Default max exponential backoff cap.
        MAX_WORKERS: Max thread pool workers used per monitoring cycle.
    """

    BASE_DIR = Path(__file__).resolve().parent
    SETTINGS_FILE = _path_env(
        "NETRADAR_SETTINGS_FILE",
        BASE_DIR.parent / "frontend" / "netradar.config.json",
    )
    SETTINGS = _load_json_file(Path(SETTINGS_FILE))

    DATABASE_PATH = _path_env("NETRADAR_DATABASE_PATH", BASE_DIR / "netradar.db")
    DAILY_DATABASE_PATH = _path_env(
        "NETRADAR_DAILY_DATABASE_PATH",
        BASE_DIR / "netradar_daily.db",
    )
    SERVICES_FILE = _path_env("NETRADAR_SERVICES_FILE", BASE_DIR.parent / "services.json")

    HOST = os.environ.get("NETRADAR_HOST", "0.0.0.0")
    PORT = _int_env("NETRADAR_PORT", 5001)

    DAILY_BACKFILL_DAYS = _int_env(
        "NETRADAR_DAILY_BACKFILL_DAYS",
        _setting_int(SETTINGS, ("backend", "runtime", "daily_backfill_days"), 90, minimum=0),
        minimum=0,
    )
    CHECK_INTERVAL = _int_env(
        "NETRADAR_CHECK_INTERVAL",
        _setting_int(SETTINGS, ("backend", "runtime", "check_interval_seconds"), 60, minimum=1),
    )
    DEFAULT_SERVICE_INTERVAL_SECONDS = _int_env(
        "NETRADAR_SERVICE_INTERVAL_SECONDS",
        _setting_int(
            SETTINGS,
            ("backend", "runtime", "default_service_interval_seconds"),
            60,
            minimum=1,
        ),
    )
    DEFAULT_SERVICE_JITTER_SECONDS = _int_env(
        "NETRADAR_SERVICE_JITTER_SECONDS",
        _setting_int(
            SETTINGS,
            ("backend", "runtime", "default_service_jitter_seconds"),
            6,
            minimum=0,
        ),
        minimum=0,
    )
    DEFAULT_MAX_BACKOFF_SECONDS = _int_env(
        "NETRADAR_MAX_BACKOFF_SECONDS",
        _setting_int(
            SETTINGS,
            ("backend", "runtime", "default_max_backoff_seconds"),
            600,
            minimum=1,
        ),
    )
    MAX_WORKERS = _int_env(
        "NETRADAR_MAX_WORKERS",
        _setting_int(SETTINGS, ("backend", "runtime", "max_workers"), 20, minimum=1),
    )

    SQLITE_TIMEOUT_SECONDS = _setting_float(
        SETTINGS,
        ("backend", "sqlite", "timeout_seconds"),
        30.0,
        minimum=0.1,
    )
    SQLITE_BUSY_TIMEOUT_MS = _setting_int(
        SETTINGS,
        ("backend", "sqlite", "busy_timeout_ms"),
        30_000,
        minimum=1,
    )

    DNS_TIMEOUT_SECONDS = _setting_int(
        SETTINGS,
        ("backend", "checker", "dns_timeout_seconds"),
        2,
        minimum=1,
    )
    HTTP_TIMEOUT_SECONDS = _setting_int(
        SETTINGS,
        ("backend", "checker", "http_timeout_seconds"),
        2,
        minimum=1,
    )
    PING_COUNT = _setting_int(
        SETTINGS,
        ("backend", "checker", "ping_count"),
        4,
        minimum=1,
    )
    PING_TIMEOUT_SECONDS = _setting_int(
        SETTINGS,
        ("backend", "checker", "ping_timeout_seconds"),
        1,
        minimum=1,
    )
    HTTP_HEADERS = {
        str(key): str(value)
        for key, value in _setting_dict(
            SETTINGS,
            ("backend", "checker", "http_headers"),
            {
                "User-Agent": "NetRadar/1.0 (+https://github.com/netradar)",
                "Accept": "*/*",
            },
        ).items()
    }

    AGGREGATION_ALGO_VERSION = _setting_int(
        SETTINGS,
        ("backend", "daily_aggregation", "algo_version"),
        1,
        minimum=1,
    )
    DAILY_STATUS_UP_THRESHOLD = _setting_float(
        SETTINGS,
        ("backend", "daily_aggregation", "status_up_threshold_pct"),
        95.0,
        minimum=0.0,
    )
    DAILY_STATUS_DEGRADED_THRESHOLD = _setting_float(
        SETTINGS,
        ("backend", "daily_aggregation", "status_degraded_threshold_pct"),
        20.0,
        minimum=0.0,
    )

    MAX_EXPORT_DAYS = _setting_int(
        SETTINGS,
        ("backend", "export", "max_days"),
        90,
        minimum=1,
    )

    API_DEFAULT_HISTORY_LIMIT = _setting_int(
        SETTINGS,
        ("backend", "api_defaults", "history_limit"),
        100,
        minimum=1,
    )
    API_DEFAULT_SERVICE_HISTORY_LIMIT = _setting_int(
        SETTINGS,
        ("backend", "api_defaults", "service_history_limit"),
        50,
        minimum=1,
    )
    API_DEFAULT_SERVICE_DAILY_LIMIT = _setting_int(
        SETTINGS,
        ("backend", "api_defaults", "service_daily_limit"),
        30,
        minimum=1,
    )
    API_DEFAULT_DAILY_SERVICES_LIMIT = _setting_int(
        SETTINGS,
        ("backend", "api_defaults", "daily_services_limit"),
        100,
        minimum=1,
    )
    API_DEFAULT_DAILY_SERVICES_OFFSET = _setting_int(
        SETTINGS,
        ("backend", "api_defaults", "daily_services_offset"),
        0,
        minimum=0,
    )
    API_DEFAULT_EXPORT_DAYS = _setting_int(
        SETTINGS,
        ("backend", "api_defaults", "export_days"),
        90,
        minimum=1,
    )

    CLI_DEFAULT_API_BASE_URL = _setting_str(
        SETTINGS,
        ("backend", "cli", "default_api_base_url"),
        "http://localhost:5001/api",
    )
    CLI_DEFAULT_TIMEOUT_SECONDS = _setting_float(
        SETTINGS,
        ("backend", "cli", "default_timeout_seconds"),
        10.0,
        minimum=0.1,
    )
    CLI_DEFAULT_OPS_SNAPSHOT_HISTORY_LIMIT = _setting_int(
        SETTINGS,
        ("backend", "cli", "ops_snapshot_history_limit"),
        100,
        minimum=1,
    )
    CLI_DEFAULT_OPS_SNAPSHOT_DAILY_LIMIT = _setting_int(
        SETTINGS,
        ("backend", "cli", "ops_snapshot_daily_limit"),
        30,
        minimum=1,
    )
    CLI_DEFAULT_OPS_GATE_DAYS = _setting_int(
        SETTINGS,
        ("backend", "cli", "ops_gate_days"),
        30,
        minimum=1,
    )
    CLI_DEFAULT_OPS_GATE_MIN_UPTIME = _setting_float(
        SETTINGS,
        ("backend", "cli", "ops_gate_min_uptime"),
        99.0,
        minimum=0.0,
    )
    CLI_DEFAULT_OPS_GATE_MAX_P95_LATENCY = _setting_float(
        SETTINGS,
        ("backend", "cli", "ops_gate_max_p95_latency"),
        120.0,
        minimum=0.1,
    )

    TUI_DASHBOARD_REFRESH_SECONDS = _setting_int(
        SETTINGS,
        ("backend", "tui", "dashboard_refresh_seconds"),
        900,
        minimum=1,
    )
    TUI_DETAIL_REFRESH_SECONDS = _setting_int(
        SETTINGS,
        ("backend", "tui", "detail_refresh_seconds"),
        60,
        minimum=1,
    )
    TUI_DETAIL_HISTORY_LIMIT = _setting_int(
        SETTINGS,
        ("backend", "tui", "detail_history_limit"),
        10_000,
        minimum=1,
    )
    TUI_DETAIL_BUCKET_COUNT = _setting_int(
        SETTINGS,
        ("backend", "tui", "detail_bucket_count"),
        12,
        minimum=1,
    )
    TUI_DETAIL_BUCKET_MARKER_STEP = _setting_int(
        SETTINGS,
        ("backend", "tui", "detail_bucket_marker_step"),
        2,
        minimum=1,
    )
    TUI_DETAIL_WINDOW_HOURS = _setting_int(
        SETTINGS,
        ("backend", "tui", "detail_window_hours"),
        6,
        minimum=1,
    )
    TUI_LINE_COLOR_LATENCY = _setting_str(
        SETTINGS,
        ("backend", "tui", "line_colors", "latency"),
        "#4ea3ff",
    )
    TUI_LINE_COLOR_JITTER = _setting_str(
        SETTINGS,
        ("backend", "tui", "line_colors", "jitter"),
        "#ffd166",
    )
    TUI_LATENCY_GOOD_LT = _setting_float(
        SETTINGS,
        ("backend", "tui", "metric_thresholds_ms", "latency", "good_lt"),
        40.0,
        minimum=0.0,
    )
    TUI_LATENCY_WARNING_LT = _setting_float(
        SETTINGS,
        ("backend", "tui", "metric_thresholds_ms", "latency", "warning_lt"),
        100.0,
        minimum=0.0,
    )
    TUI_JITTER_GOOD_LT = _setting_float(
        SETTINGS,
        ("backend", "tui", "metric_thresholds_ms", "jitter", "good_lt"),
        5.0,
        minimum=0.0,
    )
    TUI_JITTER_WARNING_LT = _setting_float(
        SETTINGS,
        ("backend", "tui", "metric_thresholds_ms", "jitter", "warning_lt"),
        20.0,
        minimum=0.0,
    )
    TUI_BACKOFF_WARNING_SECONDS = _setting_int(
        SETTINGS,
        ("backend", "tui", "backoff_warning_seconds"),
        180,
        minimum=1,
    )

    TIMELINE_UP_STABLE_THRESHOLD = _setting_float(
        SETTINGS,
        ("shared", "status_timeline", "up_stable_threshold_pct"),
        80.0,
        minimum=0.0,
    )
    TIMELINE_UP_DEGRADED_THRESHOLD = _setting_float(
        SETTINGS,
        ("shared", "status_timeline", "up_degraded_threshold_pct"),
        20.0,
        minimum=0.0,
    )
    TIMELINE_HIGH_LATENCY_THRESHOLD_MS = _setting_float(
        SETTINGS,
        ("shared", "status_timeline", "high_latency_threshold_ms"),
        40.0,
        minimum=0.0,
    )
    TIMELINE_BUCKET_WINDOW_MINUTES = _setting_int(
        SETTINGS,
        ("frontend", "timeline", "bucket_window_minutes"),
        30,
        minimum=1,
    )
    TIMELINE_FALLBACK_TOKEN = _setting_str(
        SETTINGS,
        ("shared", "status_timeline", "fallback_token"),
        "grey",
    )
    TIMELINE_OUTAGE_TOKEN = _setting_str(
        SETTINGS,
        ("shared", "status_timeline", "outage_token"),
        "red",
    )
    TIMELINE_TOKENS = {
        str(key): {
            "hex": str(value.get("hex", "")),
            "label": str(value.get("label", "")),
        }
        for key, value in _setting_dict(
            SETTINGS,
            ("shared", "status_timeline", "tokens"),
            {
                "green": {"hex": "#2ecc71", "label": "Stable"},
                "darkgreen": {"hex": "#1e8c4e", "label": "Minor instability"},
                "orange": {"hex": "#e67e22", "label": "High latency"},
                "blue": {"hex": "#3498db", "label": "No ping data"},
                "darkblue": {"hex": "#1f5f8b", "label": "Partial response"},
                "red": {"hex": "#e74c3c", "label": "Outage"},
                "grey": {"hex": "#555", "label": "No data"},
            },
        ).items()
        if isinstance(value, dict)
    }
