"""Runtime configuration for the NetRadar backend."""

from __future__ import annotations

import os
from pathlib import Path


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


class Config:
    """Application-level configuration values.

    Attributes:
        BASE_DIR: Directory that contains backend source files.
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
    DATABASE_PATH = _path_env("NETRADAR_DATABASE_PATH", BASE_DIR / "netradar.db")
    DAILY_DATABASE_PATH = _path_env(
        "NETRADAR_DAILY_DATABASE_PATH",
        BASE_DIR / "netradar_daily.db",
    )
    DAILY_BACKFILL_DAYS = _int_env("NETRADAR_DAILY_BACKFILL_DAYS", 90)
    SERVICES_FILE = _path_env("NETRADAR_SERVICES_FILE", BASE_DIR.parent / "services.json")
    HOST = os.environ.get("NETRADAR_HOST", "0.0.0.0")
    PORT = _int_env("NETRADAR_PORT", 5001)
    CHECK_INTERVAL = _int_env("NETRADAR_CHECK_INTERVAL", 60)
    DEFAULT_SERVICE_INTERVAL_SECONDS = _int_env("NETRADAR_SERVICE_INTERVAL_SECONDS", 60)
    DEFAULT_SERVICE_JITTER_SECONDS = _int_env(
        "NETRADAR_SERVICE_JITTER_SECONDS",
        6,
        minimum=0,
    )
    DEFAULT_MAX_BACKOFF_SECONDS = _int_env("NETRADAR_MAX_BACKOFF_SECONDS", 600)
    MAX_WORKERS = _int_env("NETRADAR_MAX_WORKERS", 20)
