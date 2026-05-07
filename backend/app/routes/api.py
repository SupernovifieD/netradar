"""HTTP API routes for reading monitor data and controlling the monitor."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import Blueprint, jsonify, request

from app.daily_models import DailyServiceHistory
from app.models import CheckResult
from app.services.monitor import monitor
from config import Config

bp = Blueprint("api", __name__, url_prefix="/api")


def success_response(**payload: Any):
    """Return a standard success JSON response."""
    return jsonify({"success": True, **payload})


def error_response(message: str, status_code: int = 400):
    """Return a standard error JSON response."""
    return jsonify({"success": False, "error": message}), status_code


def validate_day(day_value: str) -> bool:
    """Return True when day string matches ``YYYY-MM-DD`` format."""
    try:
        datetime.strptime(day_value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def with_intervals(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach interval rows inline for each daily summary."""
    enriched = []
    for summary in summaries:
        intervals = DailyServiceHistory.get_intervals(summary["service"], summary["day_utc"])
        enriched.append({**summary, "intervals": intervals})
    return enriched


@bp.route("/status", methods=["GET"])
def get_status():
    """Get the latest status row for each monitored service."""
    results = CheckResult.get_services_status()
    return success_response(data=results)


@bp.route("/history", methods=["GET"])
def get_history():
    """Get recent checks across services, newest first."""
    limit = request.args.get("limit", 100, type=int)
    results = CheckResult.get_latest(limit)
    return success_response(data=results)


@bp.route("/history/24h", methods=["GET"])
def get_last_24h():
    """Get all checks within the last 24 hours."""
    results = CheckResult.get_last_24h()
    return success_response(data=results)


@bp.route("/service/<service>", methods=["GET"])
def get_service_history(service: str):
    """Get recent history for one service."""
    limit = request.args.get("limit", 50, type=int)
    results = CheckResult.get_by_service(service, limit)
    return success_response(service=service, data=results)


@bp.route("/service/<service>/daily", methods=["GET"])
def get_service_daily_history(service: str):
    """Return daily summaries for one service with inline interval details."""
    limit = request.args.get("limit", 30, type=int)
    if limit is None or limit <= 0:
        return error_response("limit must be a positive integer")

    before_day = request.args.get("before_day")
    if before_day and not validate_day(before_day):
        return error_response("before_day must be in YYYY-MM-DD format")

    summaries = DailyServiceHistory.get_service_summaries(
        service=service,
        limit=limit,
        before_day=before_day,
    )
    return success_response(service=service, data=with_intervals(summaries))


@bp.route("/daily/services", methods=["GET"])
def get_daily_services():
    """Return all-service daily summaries for one UTC day."""
    day = request.args.get("day")
    if day and not validate_day(day):
        return error_response("day must be in YYYY-MM-DD format")

    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)
    if limit is None or limit <= 0:
        return error_response("limit must be a positive integer")
    if offset is None or offset < 0:
        return error_response("offset must be zero or a positive integer")

    resolved_day = day
    if not resolved_day:
        resolved_day = DailyServiceHistory.get_latest_closed_day()
        if not resolved_day:
            resolved_day = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    summaries = DailyServiceHistory.get_day_summaries(
        day_utc=resolved_day,
        limit=limit,
        offset=offset,
    )
    return success_response(day=resolved_day, data=with_intervals(summaries))


@bp.route("/monitor/start", methods=["POST"])
def start_monitor():
    """Start the in-process background monitor."""
    monitor.start()
    return success_response(message="Monitor started")


@bp.route("/monitor/stop", methods=["POST"])
def stop_monitor():
    """Stop the in-process background monitor."""
    monitor.stop()
    return success_response(message="Monitor stopped")


@bp.route("/health", methods=["GET"])
def health():
    """Simple health endpoint for uptime checks."""
    return success_response(status="healthy")


@bp.route("/services", methods=["GET"])
def get_services():
    """Return static service metadata from ``services.json``."""
    with open(Config.SERVICES_FILE, encoding="utf-8") as service_file:
        services = json.load(service_file)
    return success_response(data=services)
