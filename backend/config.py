"""Runtime configuration for the NetRadar backend."""

from pathlib import Path


class Config:
    """Application-level configuration values.

    Attributes:
        BASE_DIR: Directory that contains backend source files.
        DATABASE_PATH: SQLite database location used by data-access modules.
        SERVICES_FILE: JSON file that lists services/domains to monitor.
        CHECK_INTERVAL: Delay (seconds) between monitoring cycles.
        MAX_WORKERS: Max thread pool workers used per monitoring cycle.
    """

    BASE_DIR = Path(__file__).resolve().parent
    DATABASE_PATH = str(BASE_DIR / "netradar.db")
    SERVICES_FILE = str(BASE_DIR.parent / "services.json")
    CHECK_INTERVAL = 15
    MAX_WORKERS = 20
