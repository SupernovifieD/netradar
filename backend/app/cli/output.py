"""Output formatting for NetRadar CLI."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.time_utils import format_iso_utc_for_display, format_storage_datetime_for_display

UTC_TIMESTAMP_KEYS = {
    "computed_at_utc",
    "end_at_utc",
    "first_check_at_utc",
    "last_checked_at_utc",
    "last_check_at_utc",
    "next_due_at_utc",
    "probed_at_utc",
    "start_at_utc",
}


def utc_now_iso() -> str:
    """Return canonical UTC timestamp for CLI envelopes."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_success_envelope(
    *,
    command: str,
    mode: str,
    data: Any,
    meta: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic success envelope."""
    return {
        "ok": True,
        "command": command,
        "mode": mode,
        "timestamp_utc": utc_now_iso(),
        "data": data,
        "meta": meta,
        "error": None,
    }


def build_error_envelope(
    *,
    command: str,
    mode: str,
    error_code: str,
    message: str,
    details: dict[str, Any] | None,
    meta: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic error envelope."""
    return {
        "ok": False,
        "command": command,
        "mode": mode,
        "timestamp_utc": utc_now_iso(),
        "data": None,
        "meta": meta,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
        },
    }


def is_empty_result(data: Any) -> bool:
    """Return True when command result should be treated as empty."""
    if data is None:
        return True
    if isinstance(data, list):
        return len(data) == 0
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            return len(data["data"]) == 0
        return len(data) == 0
    return False


def dumps_json(payload: dict[str, Any]) -> str:
    """Serialize JSON output with stable key ordering for determinism."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def dumps_pretty_json(payload: Any) -> str:
    """Serialize indented JSON for human output."""
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_table(rows: list[dict[str, Any]], columns: list[str], *, max_rows: int = 40) -> str:
    """Render plain-text table for human-mode command output."""
    if not rows:
        return "(no rows)"

    visible = rows[:max_rows]
    widths = [len(column) for column in columns]
    for row in visible:
        for index, column in enumerate(columns):
            widths[index] = max(widths[index], len(str(row.get(column, ""))))

    header = "  ".join(column.ljust(widths[index]) for index, column in enumerate(columns))
    separator = "  ".join("-" * widths[index] for index in range(len(columns)))

    lines = [header, separator]
    for row in visible:
        lines.append(
            "  ".join(str(row.get(column, "")).ljust(widths[index]) for index, column in enumerate(columns))
        )

    remaining = len(rows) - len(visible)
    if remaining > 0:
        lines.append(f"... {remaining} more row(s)")

    return "\n".join(lines)


def _with_local_raw_timestamps(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add display-time columns for human raw-check tables."""
    output = []
    for row in rows:
        display_row = dict(row)
        local_datetime = format_storage_datetime_for_display(
            str(row.get("date") or ""),
            str(row.get("time") or ""),
        )
        if local_datetime != "n/a" and " " in local_datetime:
            local_date, local_time = local_datetime.split(" ", 1)
        else:
            local_date, local_time = "n/a", "n/a"
        display_row["local_date"] = local_date
        display_row["local_time"] = local_time
        output.append(display_row)
    return output


def _with_local_utc_fields(value: Any) -> Any:
    """Add local display timestamp fields beside known ``*_utc`` timestamps."""
    if isinstance(value, list):
        return [_with_local_utc_fields(item) for item in value]
    if not isinstance(value, dict):
        return value

    output: dict[str, Any] = {}
    for key, item in value.items():
        output[key] = _with_local_utc_fields(item)
        if key in UTC_TIMESTAMP_KEYS and isinstance(item, str) and item:
            local_key = f"{key.removesuffix('_utc')}_local"
            output[local_key] = format_iso_utc_for_display(item)

    if "date" in value and "time" in value:
        local_datetime = format_storage_datetime_for_display(
            str(value.get("date") or ""),
            str(value.get("time") or ""),
        )
        if local_datetime != "n/a" and " " in local_datetime:
            output["local_date"], output["local_time"] = local_datetime.split(" ", 1)

    return output


def render_human(command: str, data: Any, meta: dict[str, Any]) -> str:
    """Render concise human-readable output by command."""
    if command == "health":
        return f"Health: {data.get('status', 'unknown')}"

    if command == "services.list":
        rows = data if isinstance(data, list) else []
        return f"Services: {len(rows)}\n{render_table(rows, ['name', 'domain', 'group', 'category'])}"

    if command in {"services.add", "services.update", "services.remove"}:
        return dumps_pretty_json(data)

    if command == "status.current":
        rows = data if isinstance(data, list) else []
        rows = _with_local_raw_timestamps(rows)
        columns = [
            "service",
            "status",
            "probe_reason",
            "http_status_code",
            "dns",
            "tcp",
            "latency",
            "packet_loss",
            "local_date",
            "local_time",
        ]
        return f"Current status rows: {len(rows)}\n{render_table(rows, columns)}"

    if command in {"history.recent", "history.24h", "history.service"}:
        rows = data if isinstance(data, list) else []
        rows = _with_local_raw_timestamps(rows)
        columns = [
            "id",
            "service",
            "status",
            "probe_reason",
            "http_status_code",
            "dns",
            "tcp",
            "latency",
            "packet_loss",
            "local_date",
            "local_time",
        ]
        return f"History rows: {len(rows)}\n{render_table(rows, columns)}"

    if command == "daily.service":
        rows = data if isinstance(data, list) else []
        columns = ["service", "day_utc", "overall_status", "uptime_rate_pct", "coverage_rate_pct", "p95_latency_ms"]
        return f"Daily rows: {len(rows)}\n{render_table(rows, columns)}"

    if command == "daily.services":
        rows = data.get("data", []) if isinstance(data, dict) else []
        day = data.get("day") if isinstance(data, dict) else "unknown"
        columns = ["service", "day_utc", "overall_status", "uptime_rate_pct", "coverage_rate_pct", "p95_latency_ms"]
        return f"Daily rows for {day}: {len(rows)}\n{render_table(rows, columns)}"

    if command in {"export.raw", "export.daily"} and isinstance(data, dict):
        rows = data.get("data", [])
        output_meta = meta.get("output_file")
        line = f"Export rows: {len(rows)}"
        if output_meta:
            line += f"\nSaved: {output_meta.get('path')}"
        return line

    if command in {
        "monitor.start",
        "monitor.stop",
        "monitor.status",
        "monitor.policy",
        "monitor.runtime",
    } and isinstance(data, dict):
        return dumps_pretty_json(_with_local_utc_fields(data))

    if command == "probe.service":
        return dumps_pretty_json(_with_local_utc_fields(data))

    if command in {"ops.snapshot", "ops.gate"}:
        return dumps_pretty_json(_with_local_utc_fields(data))

    return dumps_pretty_json(data)
