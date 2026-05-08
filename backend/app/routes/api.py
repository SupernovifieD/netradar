"""HTTP API routes for reading monitor data and controlling the monitor."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from app.core.errors import CoreError
from app.core.operations import NetRadarOperations
from app.services.monitor import monitor

bp = Blueprint("api", __name__, url_prefix="/api")
core = NetRadarOperations(monitor=monitor)


def success_response(**payload: Any):
    """Return a standard success JSON response."""
    return jsonify({"success": True, **payload})


def error_response(message: str, status_code: int = 400):
    """Return a standard error JSON response."""
    return jsonify({"success": False, "error": message}), status_code


def _int_query_arg(name: str, *, default: int | None = None) -> int:
    """Parse integer query arguments with clear validation errors."""
    raw_value = request.args.get(name)
    if raw_value is None:
        if default is None:
            raise CoreError(
                code="MISSING_QUERY_PARAM",
                message=f"{name} is required",
                details={"field": name},
                http_status=400,
                exit_code=3,
            )
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise CoreError(
            code="INVALID_QUERY_INT",
            message=f"{name} must be an integer",
            details={"field": name, "value": raw_value},
            http_status=400,
            exit_code=3,
        ) from exc


def _run(operation):
    """Execute one core operation and map domain errors to API responses."""
    try:
        return operation(), None
    except CoreError as exc:
        return None, error_response(exc.message, exc.http_status)


@bp.route("/status", methods=["GET"])
def get_status():
    """Get the latest status row for each monitored service."""
    payload, error = _run(core.status_current)
    if error:
        return error
    return success_response(data=payload)


@bp.route("/history", methods=["GET"])
def get_history():
    """Get recent checks across services, newest first."""
    payload, error = _run(lambda: core.history_recent(limit=_int_query_arg("limit", default=100)))
    if error:
        return error
    return success_response(data=payload)


@bp.route("/history/24h", methods=["GET"])
def get_last_24h():
    """Get all checks within the last 24 hours."""
    payload, error = _run(core.history_24h)
    if error:
        return error
    return success_response(data=payload)


@bp.route("/service/<service>", methods=["GET"])
def get_service_history(service: str):
    """Get recent history for one service."""
    payload, error = _run(
        lambda: core.history_service(service, limit=_int_query_arg("limit", default=50))
    )
    if error:
        return error
    return success_response(service=service, data=payload)


@bp.route("/service/<service>/daily", methods=["GET"])
def get_service_daily_history(service: str):
    """Return daily summaries for one service with inline interval details."""
    payload, error = _run(
        lambda: core.daily_service(
            service,
            limit=_int_query_arg("limit", default=30),
            before_day=request.args.get("before_day"),
        )
    )
    if error:
        return error
    return success_response(service=service, data=payload)


@bp.route("/service/<service>/export/raw", methods=["GET"])
def export_service_raw(service: str):
    """Return service-level raw checks for the last N days (max 90)."""
    payload, error = _run(lambda: core.export_raw(service, days=_int_query_arg("days", default=90)))
    if error:
        return error
    return success_response(**payload)


@bp.route("/service/<service>/export/daily", methods=["GET"])
def export_service_daily(service: str):
    """Return service-level daily summaries for the last N closed UTC days (max 90)."""
    payload, error = _run(lambda: core.export_daily(service, days=_int_query_arg("days", default=90)))
    if error:
        return error
    return success_response(**payload)


@bp.route("/daily/services", methods=["GET"])
def get_daily_services():
    """Return all-service daily summaries for one UTC day."""
    payload, error = _run(
        lambda: core.daily_services(
            day=request.args.get("day"),
            limit=_int_query_arg("limit", default=100),
            offset=_int_query_arg("offset", default=0),
        )
    )
    if error:
        return error
    return success_response(**payload)


@bp.route("/monitor/start", methods=["POST"])
def start_monitor():
    """Start the in-process background monitor."""
    payload, error = _run(core.monitor_start)
    if error:
        return error
    return success_response(**payload)


@bp.route("/monitor/stop", methods=["POST"])
def stop_monitor():
    """Stop the in-process background monitor."""
    payload, error = _run(core.monitor_stop)
    if error:
        return error
    return success_response(**payload)


@bp.route("/monitor/status", methods=["GET"])
def monitor_status():
    """Return in-process background monitor state."""
    payload, error = _run(core.monitor_status)
    if error:
        return error
    return success_response(**payload)


@bp.route("/monitor/policy", methods=["GET"])
def monitor_policy():
    """Return effective monitor defaults and per-service schedule config."""
    payload, error = _run(core.monitor_policy)
    if error:
        return error
    return success_response(**payload)


@bp.route("/monitor/runtime", methods=["GET"])
def monitor_runtime():
    """Return in-memory monitor runtime state (due time + backoff)."""
    payload, error = _run(core.monitor_runtime)
    if error:
        return error
    return success_response(**payload)


@bp.route("/health", methods=["GET"])
def health():
    """Simple health endpoint for uptime checks."""
    payload, error = _run(core.health)
    if error:
        return error
    return success_response(**payload)


@bp.route("/services", methods=["GET"])
def get_services():
    """Return static service metadata from ``services.json``."""
    search = request.args.get("search")
    group = request.args.get("group")
    category = request.args.get("category")
    payload, error = _run(lambda: core.services_list(search=search, group=group, category=category))
    if error:
        return error
    return success_response(data=payload)
