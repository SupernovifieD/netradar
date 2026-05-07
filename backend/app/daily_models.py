"""Data access for daily aggregate history."""

from __future__ import annotations

from typing import Any

from app.daily_db import get_daily_connection
from config import Config

DailySummaryRow = dict[str, Any]
DailyIntervalRow = dict[str, Any]


class DailyServiceHistory:
    """Read/write helpers for daily aggregate tables."""

    @staticmethod
    def has_summary(service: str, day_utc: str) -> bool:
        """Return ``True`` if a daily summary already exists."""
        with get_daily_connection(Config.DAILY_DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM daily_service_stats
                WHERE service = ? AND day_utc = ?
                LIMIT 1
                """,
                (service, day_utc),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def insert_summary_with_intervals(
        summary: DailySummaryRow, intervals: list[DailyIntervalRow]
    ) -> None:
        """Persist one daily summary row and its interval rows atomically."""
        with get_daily_connection(Config.DAILY_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO daily_service_stats (
                    service, day_utc, overall_status, uptime_rate_pct, uptime_seconds,
                    downtime_seconds, no_data_seconds, expected_seconds, observed_seconds,
                    coverage_rate_pct, checks_total, checks_up, checks_down, checks_no_data,
                    avg_latency_ms, min_latency_ms, max_latency_ms, p95_latency_ms,
                    first_check_at_utc, last_check_at_utc, computed_at_utc, algo_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary["service"],
                    summary["day_utc"],
                    summary["overall_status"],
                    summary["uptime_rate_pct"],
                    summary["uptime_seconds"],
                    summary["downtime_seconds"],
                    summary["no_data_seconds"],
                    summary["expected_seconds"],
                    summary["observed_seconds"],
                    summary["coverage_rate_pct"],
                    summary["checks_total"],
                    summary["checks_up"],
                    summary["checks_down"],
                    summary["checks_no_data"],
                    summary["avg_latency_ms"],
                    summary["min_latency_ms"],
                    summary["max_latency_ms"],
                    summary["p95_latency_ms"],
                    summary["first_check_at_utc"],
                    summary["last_check_at_utc"],
                    summary["computed_at_utc"],
                    summary["algo_version"],
                ),
            )

            if intervals:
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO daily_service_intervals (
                        service, day_utc, interval_type, start_at_utc, end_at_utc, duration_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            interval["service"],
                            interval["day_utc"],
                            interval["interval_type"],
                            interval["start_at_utc"],
                            interval["end_at_utc"],
                            interval["duration_seconds"],
                        )
                        for interval in intervals
                    ],
                )

            connection.commit()

    @staticmethod
    def get_services_with_summary(day_utc: str) -> set[str]:
        """Return services that already have a summary row for ``day_utc``."""
        with get_daily_connection(Config.DAILY_DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT service
                FROM daily_service_stats
                WHERE day_utc = ?
                """,
                (day_utc,),
            )
            rows = cursor.fetchall()
        return {row["service"] for row in rows}

    @staticmethod
    def get_intervals(service: str, day_utc: str) -> list[DailyIntervalRow]:
        """Return persisted intervals for one service/day."""
        with get_daily_connection(Config.DAILY_DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT service, day_utc, interval_type, start_at_utc, end_at_utc, duration_seconds
                FROM daily_service_intervals
                WHERE service = ? AND day_utc = ?
                ORDER BY start_at_utc ASC
                """,
                (service, day_utc),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_service_summaries(
        service: str, *, limit: int, before_day: str | None = None
    ) -> list[DailySummaryRow]:
        """Return newest-first daily summaries for one service."""
        with get_daily_connection(Config.DAILY_DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            if before_day:
                cursor.execute(
                    """
                    SELECT *
                    FROM daily_service_stats
                    WHERE service = ? AND day_utc < ?
                    ORDER BY day_utc DESC
                    LIMIT ?
                    """,
                    (service, before_day, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM daily_service_stats
                    WHERE service = ?
                    ORDER BY day_utc DESC
                    LIMIT ?
                    """,
                    (service, limit),
                )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_service_summaries_between(
        service: str,
        *,
        start_day_utc: str,
        end_day_utc: str,
    ) -> list[DailySummaryRow]:
        """Return daily summaries for one service in ``[start_day_utc, end_day_utc)``."""
        with get_daily_connection(Config.DAILY_DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT *
                FROM daily_service_stats
                WHERE service = ?
                  AND day_utc >= ?
                  AND day_utc < ?
                ORDER BY day_utc DESC
                """,
                (service, start_day_utc, end_day_utc),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_day_summaries(day_utc: str, *, limit: int, offset: int) -> list[DailySummaryRow]:
        """Return daily summaries for all services on a specific day."""
        with get_daily_connection(Config.DAILY_DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT *
                FROM daily_service_stats
                WHERE day_utc = ?
                ORDER BY service ASC
                LIMIT ? OFFSET ?
                """,
                (day_utc, limit, offset),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_latest_closed_day() -> str | None:
        """Return the latest aggregated day in the daily stats table."""
        with get_daily_connection(Config.DAILY_DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT MAX(day_utc) AS latest_day
                FROM daily_service_stats
                """
            )
            row = cursor.fetchone()
        if not row:
            return None
        return row["latest_day"]
