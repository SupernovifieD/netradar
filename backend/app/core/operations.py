"""Shared business operations for NetRadar API and CLI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.agent_helpers import build_ops_snapshot_payload, evaluate_gate_payload
from app.core.errors import CoreError
from app.core.validation import (
    validate_day,
    validate_non_negative_int,
    validate_positive_int,
)
from app.daily_models import DailyServiceHistory
from app.models import CheckResult
from app.services.checker import check_service
from app.services.monitor import ServiceMonitor
from app.services_catalog import ServiceCatalog

MAX_EXPORT_DAYS = 90


class NetRadarOperations:
    """High-level query/control operations shared by interface layers."""

    def __init__(
        self,
        *,
        monitor: ServiceMonitor,
        service_catalog: ServiceCatalog | None = None,
    ) -> None:
        self._monitor = monitor
        self._service_catalog = service_catalog or ServiceCatalog()

    def health(self) -> dict[str, str]:
        """Return health payload."""
        return {"status": "healthy"}

    def services_list(
        self,
        *,
        search: str | None = None,
        group: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, str]]:
        """Return services with optional case-insensitive filters."""
        try:
            services = self._service_catalog.load_dicts()
        except Exception as exc:  # pragma: no cover - defensive IO surface
            raise CoreError(
                code="SERVICES_FILE_ERROR",
                message="failed to load services catalog",
                details={"error": str(exc)},
                http_status=500,
                exit_code=5,
            ) from exc

        search_value = (search or "").strip().lower()
        group_value = (group or "").strip().lower()
        category_value = (category or "").strip().lower()

        filtered: list[dict[str, str]] = []
        for service in services:
            if search_value:
                text = f"{service['name']} {service['domain']}".lower()
                if search_value not in text:
                    continue
            if group_value and service["group"].lower() != group_value:
                continue
            if category_value and service["category"].lower() != category_value:
                continue
            filtered.append(service)

        return filtered

    def status_current(self) -> list[dict[str, Any]]:
        """Return latest status rows for all services."""
        return CheckResult.get_services_status()

    def history_recent(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """Return newest checks across services."""
        validate_positive_int(limit, field_name="limit")
        return CheckResult.get_latest(limit)

    def history_24h(self) -> list[dict[str, Any]]:
        """Return checks from the last 24 hours."""
        return CheckResult.get_last_24h()

    def history_service(self, service: str, *, limit: int = 50) -> list[dict[str, Any]]:
        """Return newest checks for one service."""
        validate_positive_int(limit, field_name="limit")
        return CheckResult.get_by_service(service, limit)

    def daily_service(
        self,
        service: str,
        *,
        limit: int = 30,
        before_day: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return daily summaries for one service with inline intervals."""
        validate_positive_int(limit, field_name="limit")
        normalized_before_day = validate_day(before_day, field_name="before_day") if before_day else None

        rows = DailyServiceHistory.get_service_summaries(
            service=service,
            limit=limit,
            before_day=normalized_before_day,
        )
        return self._attach_intervals(rows)

    def daily_services(
        self,
        *,
        day: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return all-service daily summaries for one day."""
        validate_positive_int(limit, field_name="limit")
        validate_non_negative_int(offset, field_name="offset")

        resolved_day = validate_day(day, field_name="day") if day else None
        if not resolved_day:
            resolved_day = DailyServiceHistory.get_latest_closed_day()
            if not resolved_day:
                resolved_day = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

        rows = DailyServiceHistory.get_day_summaries(day_utc=resolved_day, limit=limit, offset=offset)
        return {
            "day": resolved_day,
            "data": self._attach_intervals(rows),
        }

    def export_raw(self, service: str, *, days: int = MAX_EXPORT_DAYS) -> dict[str, Any]:
        """Return raw checks export payload for one service."""
        resolved_days = self._resolve_export_days(days)

        end_utc = datetime.now(timezone.utc)
        start_utc = end_utc - timedelta(days=resolved_days)
        start_value = start_utc.strftime("%Y-%m-%d %H:%M:%S")
        end_value = end_utc.strftime("%Y-%m-%d %H:%M:%S")

        rows = CheckResult.get_by_service_between(
            service=service,
            start_datetime=start_value,
            end_datetime=end_value,
        )
        return {
            "service": service,
            "days": resolved_days,
            "start_utc": start_value,
            "end_utc": end_value,
            "data": rows,
        }

    def export_daily(self, service: str, *, days: int = MAX_EXPORT_DAYS) -> dict[str, Any]:
        """Return daily summaries export payload for one service."""
        resolved_days = self._resolve_export_days(days)

        today_utc = datetime.now(timezone.utc).date()
        start_day_utc = (today_utc - timedelta(days=resolved_days)).isoformat()
        end_day_utc = today_utc.isoformat()

        rows = DailyServiceHistory.get_service_summaries_between(
            service=service,
            start_day_utc=start_day_utc,
            end_day_utc=end_day_utc,
        )
        return {
            "service": service,
            "days": resolved_days,
            "start_day_utc": start_day_utc,
            "end_day_utc": end_day_utc,
            "data": self._attach_intervals(rows),
        }

    def monitor_start(self) -> dict[str, Any]:
        """Start monitor thread in current process."""
        was_running = self._monitor.running
        self._monitor.start()
        return {
            "message": "Monitor started" if not was_running else "Monitor already running",
            "running": self._monitor.running,
            "thread_alive": bool(self._monitor.thread and self._monitor.thread.is_alive()),
        }

    def monitor_stop(self) -> dict[str, Any]:
        """Stop monitor thread in current process."""
        was_running = self._monitor.running
        self._monitor.stop()
        return {
            "message": "Monitor stopped" if was_running else "Monitor already stopped",
            "running": self._monitor.running,
            "thread_alive": bool(self._monitor.thread and self._monitor.thread.is_alive()),
        }

    def monitor_status(self) -> dict[str, Any]:
        """Return current in-process monitor state."""
        return {
            "running": self._monitor.running,
            "thread_alive": bool(self._monitor.thread and self._monitor.thread.is_alive()),
        }

    def probe_service(self, service: str) -> dict[str, Any]:
        """Run one diagnostic probe without persistence side effects."""
        try:
            svc, dns, tcp, latency, packet_loss, status = check_service(service)
        except Exception as exc:  # pragma: no cover - defensive network surface
            raise CoreError(
                code="PROBE_FAILED",
                message=f"probe failed for service '{service}'",
                details={"service": service, "error": str(exc)},
                http_status=500,
                exit_code=5,
            ) from exc

        return {
            "service": svc,
            "dns": dns,
            "tcp": tcp,
            "latency": latency,
            "packet_loss": packet_loss,
            "status": status,
            "probed_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }

    def ops_snapshot(
        self,
        service: str,
        *,
        history_limit: int = 100,
        daily_limit: int = 30,
    ) -> dict[str, Any]:
        """Return compact agent-oriented operational snapshot."""
        validate_positive_int(history_limit, field_name="history_limit")
        validate_positive_int(daily_limit, field_name="daily_limit")

        services = self.services_list()
        service_meta = next((row for row in services if row["domain"] == service), None)
        current = self.status_current()
        current_row = next((row for row in current if row.get("service") == service), None)
        history = self.history_service(service, limit=history_limit)
        daily = self.daily_service(service, limit=daily_limit)

        return build_ops_snapshot_payload(
            service=service,
            service_meta=service_meta,
            current_row=current_row,
            history_rows=history,
            daily_rows=daily,
            monitor_state=self.monitor_status(),
        )

    def ops_gate(
        self,
        service: str,
        *,
        days: int = 30,
        min_uptime: float = 99.0,
        max_p95_latency: float = 120.0,
    ) -> dict[str, Any]:
        """Evaluate deterministic gate criteria using daily summaries."""
        export = self.export_daily(service, days=days)
        return evaluate_gate_payload(
            service=service,
            days=days,
            daily_rows=export["data"],
            min_uptime=min_uptime,
            max_p95_latency=max_p95_latency,
            start_day_utc=export["start_day_utc"],
            end_day_utc=export["end_day_utc"],
        )

    def _resolve_export_days(self, days: int) -> int:
        validate_positive_int(days, field_name="days")
        if days > MAX_EXPORT_DAYS:
            raise CoreError(
                code="EXPORT_DAYS_LIMIT_EXCEEDED",
                message=(
                    f"days cannot be greater than {MAX_EXPORT_DAYS}; "
                    "contact administrator for longer exports"
                ),
                details={"days": days, "max_days": MAX_EXPORT_DAYS},
                http_status=400,
                exit_code=3,
            )
        return days

    @staticmethod
    def _attach_intervals(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Attach interval rows inline for each daily summary."""
        enriched: list[dict[str, Any]] = []
        for summary in summaries:
            intervals = DailyServiceHistory.get_intervals(summary["service"], summary["day_utc"])
            enriched.append({**summary, "intervals": intervals})
        return enriched
