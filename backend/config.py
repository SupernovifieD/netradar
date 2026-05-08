"""Runtime configuration for the NetRadar backend."""

from pathlib import Path


class Config:
    """Application-level configuration values.

    Attributes:
        BASE_DIR: Directory that contains backend source files.
        DATABASE_PATH: SQLite database location used by data-access modules.
        DAILY_DATABASE_PATH: SQLite database used for daily aggregate history.
        DAILY_BACKFILL_DAYS: Number of recent closed UTC days to backfill.
        SERVICES_FILE: JSON file that lists services/domains to monitor.
        CHECK_INTERVAL: Base scheduler tick in seconds.
        DEFAULT_SERVICE_INTERVAL_SECONDS: Default per-service probe interval.
        DEFAULT_SERVICE_JITTER_SECONDS: Default randomized per-service jitter.
        DEFAULT_MAX_BACKOFF_SECONDS: Default max exponential backoff cap.
        MAX_WORKERS: Max thread pool workers used per monitoring cycle.
    """

    BASE_DIR = Path(__file__).resolve().parent
    DATABASE_PATH = str(BASE_DIR / "netradar.db")
    DAILY_DATABASE_PATH = str(BASE_DIR / "netradar_daily.db")
    DAILY_BACKFILL_DAYS = 90
    SERVICES_FILE = str(BASE_DIR.parent / "services.json")
    CHECK_INTERVAL = 60
    DEFAULT_SERVICE_INTERVAL_SECONDS = 60
    DEFAULT_SERVICE_JITTER_SECONDS = 6
    DEFAULT_MAX_BACKOFF_SECONDS = 600
    MAX_WORKERS = 20
