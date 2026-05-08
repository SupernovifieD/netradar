"""Output formatting for NetRadar CLI."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


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


def render_human(command: str, data: Any, meta: dict[str, Any]) -> str:
    """Render concise human-readable output by command."""
    if command == "health":
        return f"Health: {data.get('status', 'unknown')}"

    if command == "services.list":
        rows = data if isinstance(data, list) else []
        return f"Services: {len(rows)}\n{render_table(rows, ['name', 'domain', 'group', 'category'])}"

    if command == "status.current":
        rows = data if isinstance(data, list) else []
        columns = ["service", "status", "dns", "tcp", "latency", "packet_loss", "date", "time"]
        return f"Current status rows: {len(rows)}\n{render_table(rows, columns)}"

    if command in {"history.recent", "history.24h", "history.service"}:
        rows = data if isinstance(data, list) else []
        columns = ["id", "service", "status", "dns", "tcp", "latency", "packet_loss", "date", "time"]
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

    if command in {"monitor.start", "monitor.stop", "monitor.status"} and isinstance(data, dict):
        return dumps_pretty_json(data)

    if command == "probe.service":
        return dumps_pretty_json(data)

    if command in {"ops.snapshot", "ops.gate"}:
        return dumps_pretty_json(data)

    return dumps_pretty_json(data)
