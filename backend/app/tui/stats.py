"""Data querying and timeline metrics used by the backend TUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.models import CheckResult
from app.tui.catalog import ServiceCatalogItem

HALF_HOUR_SECONDS = 30 * 60


@dataclass(slots=True, frozen=True)
class ServiceLatestStats:
    """Latest known check values for one service."""

    service: ServiceCatalogItem
    status: str
    dns: str
    tcp: str
    latency: str
    packet_loss: str
    date: str
    time: str

    @property
    def last_seen(self) -> str:
        """Return combined timestamp for display."""
        if self.date and self.time:
            return f"{self.date} {self.time}"
        return "n/a"


@dataclass(slots=True, frozen=True)
class BucketSummary:
    """Aggregated status summary for one half-hour bucket."""

    start: datetime
    end: datetime
    up_percent: float
    avg_latency: float | None
    color: str


@dataclass(slots=True, frozen=True)
class SeriesPoint:
    """Simple timestamp-value point used by ASCII graphs."""

    timestamp: datetime
    value: float


def _parse_timestamp(row: dict[str, Any]) -> datetime | None:
    date_value = row.get("date")
    time_value = row.get("time")
    if not date_value or not time_value:
        return None

    try:
        return datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _parse_latency(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def determine_bucket_color(up_percent: float, avg_latency: float | None) -> str:
    """Apply the same bucket coloring rules as the frontend."""
    if up_percent >= 80 and avg_latency is not None and avg_latency < 40:
        return "green"
    if 20 <= up_percent < 80 and avg_latency is not None and avg_latency < 40:
        return "darkgreen"
    if up_percent >= 80 and avg_latency is not None and avg_latency >= 40:
        return "orange"
    if up_percent >= 80 and avg_latency is None:
        return "blue"
    if up_percent >= 20 and avg_latency is None:
        return "darkblue"
    if up_percent < 20:
        return "red"
    return "grey"


def fetch_latest_stats(catalog_items: list[ServiceCatalogItem]) -> list[ServiceLatestStats]:
    """Return latest stats for every service in the catalog.

    Services without data are still included with ``n/a`` placeholders.
    """
    latest_rows = CheckResult.get_services_status()
    rows_by_domain = {row["service"]: row for row in latest_rows}

    stats: list[ServiceLatestStats] = []
    for service in catalog_items:
        row = rows_by_domain.get(service.domain)
        if row is None:
            stats.append(
                ServiceLatestStats(
                    service=service,
                    status="NO_DATA",
                    dns="NO_DATA",
                    tcp="NO_DATA",
                    latency="na",
                    packet_loss="na",
                    date="",
                    time="",
                )
            )
            continue

        stats.append(
            ServiceLatestStats(
                service=service,
                status=row.get("status", "NO_DATA"),
                dns=row.get("dns", "NO_DATA"),
                tcp=row.get("tcp", "NO_DATA"),
                latency=row.get("latency", "na"),
                packet_loss=row.get("packet_loss", "na"),
                date=row.get("date", ""),
                time=row.get("time", ""),
            )
        )

    return stats


def fetch_recent_checks(service_domain: str, limit: int = 10_000) -> list[dict[str, Any]]:
    """Load recent checks for one service, newest first."""
    return CheckResult.get_by_service(service_domain, limit)


def build_half_hour_buckets(
    rows: list[dict[str, Any]],
    *,
    bucket_count: int = 48,
    now: datetime | None = None,
) -> list[BucketSummary]:
    """Aggregate raw checks into half-hour buckets (oldest -> newest)."""
    now_value = now or datetime.now()
    aligned = now_value.replace(second=0, microsecond=0)
    minute = aligned.minute
    aligned = aligned.replace(minute=0 if minute < 30 else 30)

    start_time = aligned - timedelta(seconds=(bucket_count - 1) * HALF_HOUR_SECONDS)
    buckets: list[dict[str, Any]] = []

    for index in range(bucket_count):
        bucket_start = start_time + timedelta(seconds=index * HALF_HOUR_SECONDS)
        bucket_end = bucket_start + timedelta(seconds=HALF_HOUR_SECONDS)
        buckets.append(
            {
                "start": bucket_start,
                "end": bucket_end,
                "checks": [],
            }
        )

    for row in rows:
        ts = _parse_timestamp(row)
        if ts is None:
            continue

        if ts < start_time or ts >= aligned + timedelta(seconds=HALF_HOUR_SECONDS):
            continue

        bucket_index = int((ts - start_time).total_seconds() // HALF_HOUR_SECONDS)
        if 0 <= bucket_index < len(buckets):
            buckets[bucket_index]["checks"].append(row)

    output: list[BucketSummary] = []
    for bucket in buckets:
        checks = bucket["checks"]
        total = len(checks)

        if total == 0:
            output.append(
                BucketSummary(
                    start=bucket["start"],
                    end=bucket["end"],
                    up_percent=0.0,
                    avg_latency=None,
                    color="grey",
                )
            )
            continue

        up_count = sum(1 for check in checks if check.get("status") == "UP")
        up_percent = (up_count / total) * 100

        latencies = [
            parsed
            for parsed in (_parse_latency(check.get("latency")) for check in checks)
            if parsed is not None
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else None

        output.append(
            BucketSummary(
                start=bucket["start"],
                end=bucket["end"],
                up_percent=up_percent,
                avg_latency=avg_latency,
                color=determine_bucket_color(up_percent, avg_latency),
            )
        )

    return output


def _build_latency_series(rows: list[dict[str, Any]], *, window_hours: int = 6) -> list[SeriesPoint]:
    """Return latency points within the time window, sorted ascending."""
    window_start = datetime.now() - timedelta(hours=window_hours)
    points: list[SeriesPoint] = []

    for row in rows:
        ts = _parse_timestamp(row)
        latency = _parse_latency(row.get("latency"))
        if ts is None or latency is None:
            continue
        if ts < window_start:
            continue
        points.append(SeriesPoint(timestamp=ts, value=latency))

    points.sort(key=lambda point: point.timestamp)
    return points


def build_latency_and_jitter(rows: list[dict[str, Any]], *, window_hours: int = 6) -> tuple[list[SeriesPoint], list[SeriesPoint]]:
    """Build latency and jitter time series for detail-screen graphs."""
    latency = _build_latency_series(rows, window_hours=window_hours)
    if len(latency) < 2:
        return latency, []

    jitter: list[SeriesPoint] = []
    for index in range(1, len(latency)):
        previous = latency[index - 1]
        current = latency[index]
        jitter.append(
            SeriesPoint(
                timestamp=current.timestamp,
                value=abs(current.value - previous.value),
            )
        )

    return latency, jitter
