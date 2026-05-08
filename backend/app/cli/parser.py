"""Argument parser builder for the NetRadar CLI."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser with full command taxonomy."""
    parser = argparse.ArgumentParser(
        prog="netradar",
        description="NetRadar automation CLI for local and API-driven operations.",
    )
    parser.add_argument("--mode", choices=["local", "api"], default="local")
    parser.add_argument("--api-base-url", default="http://localhost:5001/api")
    parser.add_argument("--timeout-sec", type=float, default=10.0)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--fail-on-empty", action="store_true")
    parser.add_argument("--debug", action="store_true")

    root = parser.add_subparsers(dest="command_group", required=True)

    health = root.add_parser("health", help="Show backend health status.")
    health.set_defaults(command_id="health")

    services = root.add_parser("services", help="Service catalog queries.")
    services_sub = services.add_subparsers(dest="services_command", required=True)
    services_list = services_sub.add_parser("list", help="List services from services.json.")
    services_list.add_argument("--search")
    services_list.add_argument("--group")
    services_list.add_argument("--category")
    services_list.set_defaults(command_id="services.list")

    status = root.add_parser("status", help="Current status views.")
    status_sub = status.add_subparsers(dest="status_command", required=True)
    status_current = status_sub.add_parser("current", help="Latest row per service.")
    status_current.set_defaults(command_id="status.current")

    history = root.add_parser("history", help="Raw history queries.")
    history_sub = history.add_subparsers(dest="history_command", required=True)
    history_recent = history_sub.add_parser("recent", help="Newest checks across services.")
    history_recent.add_argument("--limit", type=int, default=100)
    history_recent.set_defaults(command_id="history.recent")

    history_24h = history_sub.add_parser("24h", help="Checks from last 24 hours.")
    history_24h.set_defaults(command_id="history.24h")

    history_service = history_sub.add_parser("service", help="Newest checks for one service.")
    history_service.add_argument("service")
    history_service.add_argument("--limit", type=int, default=50)
    history_service.set_defaults(command_id="history.service")

    daily = root.add_parser("daily", help="Daily aggregate queries.")
    daily_sub = daily.add_subparsers(dest="daily_command", required=True)
    daily_service = daily_sub.add_parser("service", help="Daily rows for one service.")
    daily_service.add_argument("service")
    daily_service.add_argument("--limit", type=int, default=30)
    daily_service.add_argument("--before-day")
    daily_service.set_defaults(command_id="daily.service")

    daily_services = daily_sub.add_parser("services", help="Daily rows for all services on one day.")
    daily_services.add_argument("--day")
    daily_services.add_argument("--limit", type=int, default=100)
    daily_services.add_argument("--offset", type=int, default=0)
    daily_services.set_defaults(command_id="daily.services")

    export = root.add_parser("export", help="Export raw or daily service history.")
    export_sub = export.add_subparsers(dest="export_command", required=True)
    export_raw = export_sub.add_parser("raw", help="Export raw checks for one service.")
    export_raw.add_argument("service")
    export_raw.add_argument("--days", type=int, default=90)
    export_raw.add_argument("--out")
    export_raw.set_defaults(command_id="export.raw")

    export_daily = export_sub.add_parser("daily", help="Export daily summaries for one service.")
    export_daily.add_argument("service")
    export_daily.add_argument("--days", type=int, default=90)
    export_daily.add_argument("--out")
    export_daily.set_defaults(command_id="export.daily")

    monitor = root.add_parser("monitor", help="Monitor control commands (API mode only).")
    monitor_sub = monitor.add_subparsers(dest="monitor_command", required=True)
    monitor_start = monitor_sub.add_parser("start", help="Start backend monitor.")
    monitor_start.set_defaults(command_id="monitor.start")
    monitor_stop = monitor_sub.add_parser("stop", help="Stop backend monitor.")
    monitor_stop.set_defaults(command_id="monitor.stop")
    monitor_status = monitor_sub.add_parser("status", help="Get backend monitor state.")
    monitor_status.set_defaults(command_id="monitor.status")

    probe = root.add_parser("probe", help="Diagnostic probe commands.")
    probe_sub = probe.add_subparsers(dest="probe_command", required=True)
    probe_service = probe_sub.add_parser("service", help="Run one non-persistent service probe.")
    probe_service.add_argument("service")
    probe_service.set_defaults(command_id="probe.service")

    ops = root.add_parser("ops", help="Agent-oriented operational workflows.")
    ops_sub = ops.add_subparsers(dest="ops_command", required=True)
    ops_snapshot = ops_sub.add_parser("snapshot", help="Build service operational snapshot.")
    ops_snapshot.add_argument("service")
    ops_snapshot.add_argument("--history-limit", type=int, default=100)
    ops_snapshot.add_argument("--daily-limit", type=int, default=30)
    ops_snapshot.set_defaults(command_id="ops.snapshot")

    ops_gate = ops_sub.add_parser("gate", help="Evaluate deterministic service gate.")
    ops_gate.add_argument("service")
    ops_gate.add_argument("--days", type=int, default=30)
    ops_gate.add_argument("--min-uptime", type=float, default=99.0)
    ops_gate.add_argument("--max-p95-latency", type=float, default=120.0)
    ops_gate.set_defaults(command_id="ops.gate")

    return parser
