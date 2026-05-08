"""Reusable AI-agent-friendly helpers for NetRadar operational workflows."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.core.errors import CoreError
from app.core.validation import validate_positive_int


def build_ops_snapshot_payload(
    *,
    service: str,
    service_meta: dict[str, Any] | None,
    current_row: dict[str, Any] | None,
    history_rows: list[dict[str, Any]],
    daily_rows: list[dict[str, Any]],
    monitor_state: dict[str, Any],
) -> dict[str, Any]:
    """Build a compact deterministic snapshot payload for one service."""
    return {
        "service": service,
        "service_meta": service_meta,
        "current": current_row,
        "history": history_rows,
        "daily": daily_rows,
        "monitor": monitor_state,
    }


def evaluate_gate_payload(
    *,
    service: str,
    days: int,
    daily_rows: list[dict[str, Any]],
    min_uptime: float,
    max_p95_latency: float,
    start_day_utc: str | None = None,
    end_day_utc: str | None = None,
) -> dict[str, Any]:
    """Evaluate deterministic gate criteria from daily summary rows."""
    validate_positive_int(days, field_name="days")
    if min_uptime < 0 or min_uptime > 100:
        raise CoreError(
            code="INVALID_MIN_UPTIME",
            message="min_uptime must be between 0 and 100",
            details={"min_uptime": min_uptime},
            http_status=400,
            exit_code=3,
        )
    if max_p95_latency <= 0:
        raise CoreError(
            code="INVALID_MAX_P95_LATENCY",
            message="max_p95_latency must be a positive number",
            details={"max_p95_latency": max_p95_latency},
            http_status=400,
            exit_code=3,
        )

    reasons: list[str] = []

    if not daily_rows:
        reasons.append("NO_DAILY_DATA")
        return {
            "service": service,
            "days": days,
            "passed": False,
            "reasons": reasons,
            "summary": {
                "evaluated_days": 0,
                "average_uptime_rate_pct": None,
                "average_p95_latency_ms": None,
                "status_counts": {},
                "min_uptime_threshold_pct": min_uptime,
                "max_p95_latency_threshold_ms": max_p95_latency,
            },
            "window": {
                "start_day_utc": start_day_utc,
                "end_day_utc": end_day_utc,
            },
        }

    uptime_values = [float(row["uptime_rate_pct"]) for row in daily_rows]
    avg_uptime = sum(uptime_values) / len(uptime_values)

    p95_values = [float(row["p95_latency_ms"]) for row in daily_rows if row.get("p95_latency_ms") is not None]
    avg_p95 = (sum(p95_values) / len(p95_values)) if p95_values else None

    if avg_uptime < min_uptime:
        reasons.append("LOW_UPTIME")
    if avg_p95 is None:
        reasons.append("NO_LATENCY_DATA")
    elif avg_p95 > max_p95_latency:
        reasons.append("HIGH_P95_LATENCY")

    status_counts = Counter(str(row.get("overall_status", "UNKNOWN")) for row in daily_rows)
    return {
        "service": service,
        "days": days,
        "passed": len(reasons) == 0,
        "reasons": reasons,
        "summary": {
            "evaluated_days": len(daily_rows),
            "average_uptime_rate_pct": round(avg_uptime, 6),
            "average_p95_latency_ms": round(avg_p95, 6) if avg_p95 is not None else None,
            "status_counts": dict(status_counts),
            "min_uptime_threshold_pct": min_uptime,
            "max_p95_latency_threshold_ms": max_p95_latency,
        },
        "window": {
            "start_day_utc": start_day_utc,
            "end_day_utc": end_day_utc,
        },
    }
