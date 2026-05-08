"""Command execution pipeline for NetRadar CLI."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any

from app.cli.errors import CLIError, EXIT_EMPTY, EXIT_UNSUPPORTED_MODE
from app.cli.output import is_empty_result


def execute_command(args: Namespace, transport: Any) -> tuple[Any, dict[str, Any]]:
    """Execute one command and return ``(data, meta)``."""
    command = args.command_id
    meta: dict[str, Any] = {}

    if command.startswith("monitor.") and args.mode != "api":
        raise CLIError(
            code="UNSUPPORTED_MODE",
            message="monitor commands are supported only in api mode",
            exit_code=EXIT_UNSUPPORTED_MODE,
            details={"mode": args.mode, "command": command},
        )
    if command == "probe.service" and args.mode != "local":
        raise CLIError(
            code="UNSUPPORTED_MODE",
            message="probe.service is supported only in local mode",
            exit_code=EXIT_UNSUPPORTED_MODE,
            details={"mode": args.mode, "command": command},
        )

    if command == "health":
        data = transport.health()
    elif command == "services.list":
        data = transport.services_list(search=args.search, group=args.group, category=args.category)
    elif command == "status.current":
        data = transport.status_current()
    elif command == "history.recent":
        data = transport.history_recent(limit=args.limit)
        meta["limit"] = args.limit
    elif command == "history.24h":
        data = transport.history_24h()
    elif command == "history.service":
        data = transport.history_service(args.service, limit=args.limit)
        meta["service"] = args.service
        meta["limit"] = args.limit
    elif command == "daily.service":
        data = transport.daily_service(args.service, limit=args.limit, before_day=args.before_day)
        meta["service"] = args.service
        meta["limit"] = args.limit
        if args.before_day:
            meta["before_day"] = args.before_day
    elif command == "daily.services":
        data = transport.daily_services(day=args.day, limit=args.limit, offset=args.offset)
        meta["limit"] = args.limit
        meta["offset"] = args.offset
        if args.day:
            meta["day"] = args.day
    elif command == "export.raw":
        data = transport.export_raw(args.service, days=args.days)
        meta["service"] = args.service
        meta["days"] = args.days
    elif command == "export.daily":
        data = transport.export_daily(args.service, days=args.days)
        meta["service"] = args.service
        meta["days"] = args.days
    elif command == "monitor.start":
        data = transport.monitor_start()
    elif command == "monitor.stop":
        data = transport.monitor_stop()
    elif command == "monitor.status":
        data = transport.monitor_status()
    elif command == "probe.service":
        data = transport.probe_service(args.service)
        meta["service"] = args.service
    elif command == "ops.snapshot":
        data = transport.ops_snapshot(
            args.service,
            history_limit=args.history_limit,
            daily_limit=args.daily_limit,
        )
        meta["service"] = args.service
        meta["history_limit"] = args.history_limit
        meta["daily_limit"] = args.daily_limit
    elif command == "ops.gate":
        data = transport.ops_gate(
            args.service,
            days=args.days,
            min_uptime=args.min_uptime,
            max_p95_latency=args.max_p95_latency,
        )
        meta["service"] = args.service
        meta["days"] = args.days
        meta["min_uptime"] = args.min_uptime
        meta["max_p95_latency"] = args.max_p95_latency
    else:  # pragma: no cover - parser guards this already
        raise CLIError(
            code="UNKNOWN_COMMAND",
            message=f"unsupported command id: {command}",
            exit_code=EXIT_UNSUPPORTED_MODE,
        )

    if command in {"export.raw", "export.daily"} and getattr(args, "out", None):
        out_path = _write_export_output(args.out, data)
        records = len(data.get("data", [])) if isinstance(data, dict) and isinstance(data.get("data"), list) else 0
        meta["output_file"] = {"path": str(out_path), "records": records}

    if args.fail_on_empty and is_empty_result(data):
        raise CLIError(
            code="EMPTY_RESULT",
            message="command returned an empty result",
            exit_code=EXIT_EMPTY,
            details={"command": command},
        )

    return data, meta


def _write_export_output(path_value: str, data: Any) -> Path:
    """Write export payload to disk in deterministic JSON format."""
    path = Path(path_value).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return path
