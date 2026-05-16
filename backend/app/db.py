"""Database helpers for the NetRadar backend.

This module centralizes schema setup and SQLite connection helpers so that
database concerns stay out of the Flask app factory and route modules.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Final, Iterator

from config import Config

SQLITE_TIMEOUT_SECONDS = Config.SQLITE_TIMEOUT_SECONDS
SQLITE_BUSY_TIMEOUT_MS = Config.SQLITE_BUSY_TIMEOUT_MS

CHECKS_TABLE_SQL: Final[str] = """
    CREATE TABLE IF NOT EXISTS checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT NOT NULL,
        latency TEXT,
        packet_loss TEXT,
        dns TEXT,
        tcp TEXT,
        status TEXT,
        probe_reason TEXT,
        http_status_code INTEGER,
        date TEXT,
        time TEXT
    )
"""

INDEX_SQL: Final[tuple[str, str]] = (
    """
    CREATE INDEX IF NOT EXISTS idx_service_datetime
    ON checks(service, date DESC, time DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_datetime
    ON checks(date DESC, time DESC)
    """,
)


@contextmanager
def get_connection(
    db_path: str,
    *,
    with_row_factory: bool = False,
) -> Iterator[sqlite3.Connection]:
    """Create a SQLite connection with optional dictionary-style row support.

    Args:
        db_path: Absolute or relative path to the SQLite database file.
        with_row_factory: If ``True``, returned rows behave like mappings.

    Yields:
        Configured SQLite connection that is always closed after use.
    """
    connection = sqlite3.connect(db_path, timeout=SQLITE_TIMEOUT_SECONDS)

    # Wait up to SQLITE_BUSY_TIMEOUT_MS before raising "database is locked".
    connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")

    if with_row_factory:
        connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def init_db(db_path: str) -> None:
    """Create required tables and indexes if they do not yet exist.

    This operation is idempotent and safe to call at startup.

    Args:
        db_path: Path to the SQLite database file.
    """
    Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)

    with get_connection(db_path) as connection:
        cursor = connection.cursor()

        # WAL allows readers and a writer to coexist more smoothly.
        cursor.execute("PRAGMA journal_mode=WAL")
        # Good default tradeoff for an append-heavy monitoring workload.
        cursor.execute("PRAGMA synchronous=NORMAL")

        cursor.execute(CHECKS_TABLE_SQL)
        _ensure_checks_columns(cursor)
        for statement in INDEX_SQL:
            cursor.execute(statement)
        connection.commit()


def _ensure_checks_columns(cursor: sqlite3.Cursor) -> None:
    """Add newly introduced checks columns on existing databases."""
    cursor.execute("PRAGMA table_info(checks)")
    columns = {row[1] for row in cursor.fetchall()}

    if "probe_reason" not in columns:
        cursor.execute("ALTER TABLE checks ADD COLUMN probe_reason TEXT")
    if "http_status_code" not in columns:
        cursor.execute("ALTER TABLE checks ADD COLUMN http_status_code INTEGER")
