"""Database helpers for the daily aggregate history SQLite database."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Final, Iterator

from app.db import SQLITE_BUSY_TIMEOUT_MS, SQLITE_TIMEOUT_SECONDS

DAILY_STATS_TABLE_SQL: Final[str] = """
    CREATE TABLE IF NOT EXISTS daily_service_stats (
        service TEXT NOT NULL,
        day_utc TEXT NOT NULL,
        overall_status TEXT NOT NULL CHECK (overall_status IN ('UP', 'DEGRADED', 'DOWN', 'NO_DATA')),
        uptime_rate_pct REAL NOT NULL,
        uptime_seconds INTEGER NOT NULL,
        downtime_seconds INTEGER NOT NULL,
        no_data_seconds INTEGER NOT NULL,
        expected_seconds INTEGER NOT NULL,
        observed_seconds INTEGER NOT NULL,
        coverage_rate_pct REAL NOT NULL,
        checks_total INTEGER NOT NULL,
        checks_up INTEGER NOT NULL,
        checks_down INTEGER NOT NULL,
        checks_no_data INTEGER NOT NULL,
        avg_latency_ms REAL,
        min_latency_ms REAL,
        max_latency_ms REAL,
        p95_latency_ms REAL,
        first_check_at_utc TEXT,
        last_check_at_utc TEXT,
        computed_at_utc TEXT NOT NULL,
        algo_version INTEGER NOT NULL DEFAULT 1,
        UNIQUE(service, day_utc)
    )
"""

DAILY_INTERVALS_TABLE_SQL: Final[str] = """
    CREATE TABLE IF NOT EXISTS daily_service_intervals (
        service TEXT NOT NULL,
        day_utc TEXT NOT NULL,
        interval_type TEXT NOT NULL CHECK (interval_type IN ('DOWN', 'NO_DATA')),
        start_at_utc TEXT NOT NULL,
        end_at_utc TEXT NOT NULL,
        duration_seconds INTEGER NOT NULL,
        UNIQUE(service, day_utc, interval_type, start_at_utc, end_at_utc)
    )
"""

DAILY_INDEX_SQL: Final[tuple[str, ...]] = (
    """
    CREATE INDEX IF NOT EXISTS idx_daily_stats_day
    ON daily_service_stats(day_utc DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_daily_stats_service_day
    ON daily_service_stats(service, day_utc DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_daily_intervals_service_day_start
    ON daily_service_intervals(service, day_utc, start_at_utc)
    """,
)

DAILY_STATS_COPY_COLUMNS: Final[tuple[str, ...]] = (
    "service",
    "day_utc",
    "overall_status",
    "uptime_rate_pct",
    "uptime_seconds",
    "downtime_seconds",
    "no_data_seconds",
    "expected_seconds",
    "observed_seconds",
    "coverage_rate_pct",
    "checks_total",
    "checks_up",
    "checks_down",
    "checks_no_data",
    "avg_latency_ms",
    "min_latency_ms",
    "max_latency_ms",
    "p95_latency_ms",
    "first_check_at_utc",
    "last_check_at_utc",
    "computed_at_utc",
    "algo_version",
)


@contextmanager
def get_daily_connection(
    db_path: str,
    *,
    with_row_factory: bool = False,
) -> Iterator[sqlite3.Connection]:
    """Create a SQLite connection for the daily aggregate database."""
    connection = sqlite3.connect(db_path, timeout=SQLITE_TIMEOUT_SECONDS)
    connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    if with_row_factory:
        connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def init_daily_db(db_path: str) -> None:
    """Create tables and indexes required by the daily aggregate layer."""
    with get_daily_connection(db_path) as connection:
        cursor = connection.cursor()

        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")

        cursor.execute(DAILY_STATS_TABLE_SQL)
        _ensure_daily_stats_supports_no_data(cursor)
        cursor.execute(DAILY_INTERVALS_TABLE_SQL)
        for statement in DAILY_INDEX_SQL:
            cursor.execute(statement)
        connection.commit()


def _ensure_daily_stats_supports_no_data(cursor: sqlite3.Cursor) -> None:
    """Migrate legacy daily stats table to allow ``overall_status='NO_DATA'``."""
    cursor.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'daily_service_stats'
        """
    )
    row = cursor.fetchone()
    if not row:
        return

    create_sql = (row[0] or "").upper()
    if "'NO_DATA'" in create_sql:
        return

    cursor.execute("ALTER TABLE daily_service_stats RENAME TO daily_service_stats_legacy")
    cursor.execute(DAILY_STATS_TABLE_SQL)

    columns = ", ".join(DAILY_STATS_COPY_COLUMNS)
    cursor.execute(
        f"""
        INSERT INTO daily_service_stats ({columns})
        SELECT {columns}
        FROM daily_service_stats_legacy
        """
    )
    cursor.execute("DROP TABLE daily_service_stats_legacy")
