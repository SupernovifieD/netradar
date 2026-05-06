"""Database helpers for the NetRadar backend.

This module centralizes schema setup and SQLite connection helpers so that
database concerns stay out of the Flask app factory and route modules.
"""

from __future__ import annotations

import sqlite3
from typing import Final

CHECKS_TABLE_SQL: Final[str] = """
    CREATE TABLE IF NOT EXISTS checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT NOT NULL,
        latency TEXT,
        packet_loss TEXT,
        dns TEXT,
        tcp TEXT,
        status TEXT,
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


def get_connection(db_path: str, *, with_row_factory: bool = False) -> sqlite3.Connection:
    """Create a SQLite connection with optional dictionary-style row support.

    Args:
        db_path: Absolute or relative path to the SQLite database file.
        with_row_factory: If ``True``, returned rows behave like mappings.

    Returns:
        Configured SQLite connection.
    """
    connection = sqlite3.connect(db_path)
    if with_row_factory:
        connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: str) -> None:
    """Create required tables and indexes if they do not yet exist.

    This operation is idempotent and safe to call at startup.

    Args:
        db_path: Path to the SQLite database file.
    """
    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(CHECKS_TABLE_SQL)
        for statement in INDEX_SQL:
            cursor.execute(statement)
        connection.commit()
