"""Daily aggregate builder for service uptime history."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.daily_models import DailyIntervalRow, DailyServiceHistory, DailySummaryRow
from app.models import CheckResult
from app.services.monitoring_policy import ServiceMonitoringPolicy, load_service_monitoring_policies
from config import Config

AGGREGATION_ALGO_VERSION = 1
STATUS_UP_THRESHOLD = 95.0
STATUS_DEGRADED_THRESHOLD = 80.0


class DailyAggregator:
    """Build and persist immutable closed-day aggregate rows."""

    def __init__(self) -> None:
        self._backfill_days = Config.DAILY_BACKFILL_DAYS
        self._backfill_done = False

    def run(self) -> None:
        """Run daily aggregation for missing closed UTC days."""
        today_utc = datetime.now(timezone.utc).date()
        policies = load_service_monitoring_policies()
        target_days = self._get_target_days(today_utc=today_utc)

        for day_utc in target_days:
            if day_utc >= today_utc:
                continue
            self._aggregate_day(day_utc=day_utc, policies=policies)

        self._backfill_done = True

    def _get_target_days(self, today_utc: date) -> list[date]:
        """Return closed UTC days that should be processed in this run."""
        if not self._backfill_done:
            if self._backfill_days <= 0:
                return []
            start_day = today_utc - timedelta(days=self._backfill_days)
            return [start_day + timedelta(days=offset) for offset in range(self._backfill_days)]

        return [today_utc - timedelta(days=1)]

    def _aggregate_day(self, day_utc: date, policies: list[ServiceMonitoringPolicy]) -> None:
        """Aggregate one closed day for all monitored services."""
        day_utc_str = day_utc.isoformat()
        existing_services = DailyServiceHistory.get_services_with_summary(day_utc_str)

        day_start = datetime.combine(day_utc, datetime.min.time(), tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        raw_rows = CheckResult.get_between(
            day_start.strftime("%Y-%m-%d %H:%M:%S"),
            day_end.strftime("%Y-%m-%d %H:%M:%S"),
        )

        rows_by_service: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in raw_rows:
            rows_by_service[row["service"]].append(row)

        for policy in policies:
            service = policy.domain
            if not policy.enabled:
                continue
            if service in existing_services:
                continue
            summary, intervals = self._build_service_day_summary(
                policy=policy,
                day_start_utc=day_start,
                service_rows=rows_by_service.get(service, []),
            )
            DailyServiceHistory.insert_summary_with_intervals(summary, intervals)

    def _build_service_day_summary(
        self,
        policy: ServiceMonitoringPolicy,
        day_start_utc: datetime,
        service_rows: list[dict[str, Any]],
    ) -> tuple[DailySummaryRow, list[DailyIntervalRow]]:
        """Build one service/day summary plus interval rows."""
        service = policy.domain
        slot_bounds = self._build_slot_bounds(
            day_start_utc=day_start_utc,
            interval_seconds=policy.interval_seconds,
        )
        slots: list[dict[str, Any] | None] = [None] * len(slot_bounds)
        check_times: list[datetime] = []
        latencies: list[float] = []
        checks_up = 0
        checks_down = 0

        for row in service_rows:
            timestamp = self._parse_utc_timestamp(row["date"], row["time"])
            slot_index = int((timestamp - day_start_utc).total_seconds() // policy.interval_seconds)
            if slot_index < 0 or slot_index >= len(slot_bounds):
                continue

            current = slots[slot_index]
            if current is None or timestamp >= current["timestamp"]:
                slots[slot_index] = {
                    "timestamp": timestamp,
                    "status": row["status"],
                }

            check_times.append(timestamp)

            if row["status"] == "UP":
                checks_up += 1
            else:
                checks_down += 1

            latency = self._parse_latency_ms(row["latency"])
            if latency is not None:
                latencies.append(latency)

        slot_states = self._build_slot_states(slots)
        uptime_seconds = 0
        downtime_seconds = 0
        no_data_seconds = 0
        for index, state in enumerate(slot_states):
            slot_duration = slot_bounds[index][2]
            if state == "UP":
                uptime_seconds += slot_duration
            elif state == "DOWN":
                downtime_seconds += slot_duration
            else:
                no_data_seconds += slot_duration

        no_data_slots = sum(1 for state in slot_states if state == "NO_DATA")

        expected_seconds = sum(duration for _, _, duration in slot_bounds)
        observed_seconds = uptime_seconds + downtime_seconds

        uptime_rate_pct = (uptime_seconds / expected_seconds) * 100 if expected_seconds > 0 else 0.0
        coverage_rate_pct = (
            (observed_seconds / expected_seconds) * 100 if expected_seconds > 0 else 0.0
        )
        checks_total = checks_up + checks_down
        checks_no_data = no_data_slots

        summary: DailySummaryRow = {
            "service": service,
            "day_utc": day_start_utc.date().isoformat(),
            "overall_status": self._classify_day_status(uptime_rate_pct),
            "uptime_rate_pct": round(uptime_rate_pct, 6),
            "uptime_seconds": uptime_seconds,
            "downtime_seconds": downtime_seconds,
            "no_data_seconds": no_data_seconds,
            "expected_seconds": expected_seconds,
            "observed_seconds": observed_seconds,
            "coverage_rate_pct": round(coverage_rate_pct, 6),
            "checks_total": checks_total,
            "checks_up": checks_up,
            "checks_down": checks_down,
            "checks_no_data": checks_no_data,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 6) if latencies else None,
            "min_latency_ms": round(min(latencies), 6) if latencies else None,
            "max_latency_ms": round(max(latencies), 6) if latencies else None,
            "p95_latency_ms": round(self._percentile(latencies, 95.0), 6) if latencies else None,
            "first_check_at_utc": self._format_datetime(min(check_times)) if check_times else None,
            "last_check_at_utc": self._format_datetime(max(check_times)) if check_times else None,
            "computed_at_utc": self._format_datetime(datetime.now(timezone.utc)),
            "algo_version": AGGREGATION_ALGO_VERSION,
        }
        intervals = self._build_intervals(
            service=service,
            day_utc=summary["day_utc"],
            slot_bounds=slot_bounds,
            slot_states=slot_states,
        )
        return summary, intervals

    def _build_slot_states(self, slots: list[dict[str, Any] | None]) -> list[str]:
        """Convert slot samples into normalized UP/DOWN/NO_DATA states."""
        states: list[str] = []
        for slot in slots:
            if slot is None:
                states.append("NO_DATA")
            elif slot["status"] == "UP":
                states.append("UP")
            else:
                states.append("DOWN")
        return states

    def _build_intervals(
        self,
        service: str,
        day_utc: str,
        slot_bounds: list[tuple[datetime, datetime, int]],
        slot_states: list[str],
    ) -> list[DailyIntervalRow]:
        """Compress contiguous DOWN/NO_DATA slot runs into interval rows."""
        intervals: list[DailyIntervalRow] = []
        index = 0
        while index < len(slot_states):
            state = slot_states[index]
            if state not in ("DOWN", "NO_DATA"):
                index += 1
                continue

            start = index
            while index < len(slot_states) and slot_states[index] == state:
                index += 1
            end = index

            start_time = slot_bounds[start][0]
            end_time = slot_bounds[end - 1][1]
            duration_seconds = sum(slot_bounds[offset][2] for offset in range(start, end))
            intervals.append(
                {
                    "service": service,
                    "day_utc": day_utc,
                    "interval_type": state,
                    "start_at_utc": self._format_datetime(start_time),
                    "end_at_utc": self._format_datetime(end_time),
                    "duration_seconds": duration_seconds,
                }
            )
        return intervals

    def _build_slot_bounds(
        self,
        *,
        day_start_utc: datetime,
        interval_seconds: int,
    ) -> list[tuple[datetime, datetime, int]]:
        """Build day slot boundaries for a service cadence."""
        bounds: list[tuple[datetime, datetime, int]] = []
        day_end_utc = day_start_utc + timedelta(days=1)
        cursor = day_start_utc

        while cursor < day_end_utc:
            end = min(day_end_utc, cursor + timedelta(seconds=interval_seconds))
            duration_seconds = int((end - cursor).total_seconds())
            bounds.append((cursor, end, duration_seconds))
            cursor = end

        return bounds

    def _classify_day_status(self, uptime_rate_pct: float) -> str:
        """Return UP/DEGRADED/DOWN classification from uptime percentage."""
        if uptime_rate_pct >= STATUS_UP_THRESHOLD:
            return "UP"
        if uptime_rate_pct >= STATUS_DEGRADED_THRESHOLD:
            return "DEGRADED"
        return "DOWN"

    def _parse_utc_timestamp(self, date_str: str, time_str: str) -> datetime:
        """Parse a raw check timestamp to a UTC-aware datetime."""
        naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        return naive.replace(tzinfo=timezone.utc)

    def _parse_latency_ms(self, latency_value: str) -> float | None:
        """Parse a latency value to float milliseconds when valid."""
        try:
            value = float(latency_value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value):
            return None
        return value

    def _percentile(self, values: list[float], percentile: float) -> float:
        """Compute percentile using linear interpolation."""
        if not values:
            raise ValueError("percentile values cannot be empty")
        sorted_values = sorted(values)
        if len(sorted_values) == 1:
            return sorted_values[0]

        rank = (percentile / 100.0) * (len(sorted_values) - 1)
        lower = math.floor(rank)
        upper = math.ceil(rank)
        if lower == upper:
            return sorted_values[lower]
        weight = rank - lower
        return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * weight

    def _format_datetime(self, value: datetime) -> str:
        """Format UTC datetime to canonical storage format."""
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
