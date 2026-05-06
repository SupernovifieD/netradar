"""Data-access layer for persisted service check results."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db import get_connection
from config import Config

CheckWriteRow = tuple[str, str, str, str, str, str]


class CheckResult:
    """CRUD-style helpers for the ``checks`` SQLite table."""

    @staticmethod
    def save(
        service: str,
        latency: str,
        packet_loss: str,
        dns: str,
        tcp: str,
        status: str,
    ) -> None:
        """Persist one monitoring result row.

        The schema stores date and time as separate text fields to preserve
        compatibility with existing queries and dashboard parsing.
        """
        CheckResult.save_many([(service, latency, packet_loss, dns, tcp, status)])

    @staticmethod
    def save_many(rows: list[CheckWriteRow]) -> None:
        """Persist multiple monitoring rows in a single transaction.

        Batching writes drastically reduces lock churn when many services are
        checked in the same cycle.
        """
        if not rows:
            return

        dated_rows = []
        for service, latency, packet_loss, dns, tcp, status in rows:
            now = datetime.now()
            date = now.strftime("%Y-%m-%d")
            time = now.strftime("%H:%M:%S")
            dated_rows.append((service, latency, packet_loss, dns, tcp, status, date, time))

        with get_connection(Config.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.executemany(
                """
                INSERT INTO checks (service, latency, packet_loss, dns, tcp, status, date, time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                dated_rows,
            )
            connection.commit()

    @staticmethod
    def get_latest(limit: int = 100) -> list[dict[str, Any]]:
        """Return the newest check rows across all services."""
        with get_connection(Config.DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT * FROM checks
                ORDER BY date DESC, time DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_service(service: str, limit: int = 2000) -> list[dict[str, Any]]:
        """Return newest check rows for a single service."""
        with get_connection(Config.DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT * FROM checks
                WHERE service = ?
                ORDER BY date DESC, time DESC
                LIMIT ?
                """,
                (service, limit),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_services_status() -> list[dict[str, Any]]:
        """Return one latest row per service."""
        with get_connection(Config.DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT c1.*
                FROM checks c1
                INNER JOIN (
                    SELECT service, MAX(date || ' ' || time) AS maxts
                    FROM checks
                    GROUP BY service
                ) c2 ON c1.service = c2.service
                     AND (c1.date || ' ' || c1.time) = c2.maxts
                ORDER BY c1.service
                """
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_last_24h() -> list[dict[str, Any]]:
        """Return rows from the last 24 hours."""
        with get_connection(Config.DATABASE_PATH, with_row_factory=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT *
                FROM checks
                WHERE datetime(date || ' ' || time) >= datetime('now', '-24 hours')
                ORDER BY date DESC, time DESC
                """
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]
