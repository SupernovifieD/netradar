"""HTTP API routes for reading monitor data and controlling the monitor."""

from __future__ import annotations

import json
from typing import Any

from flask import Blueprint, jsonify, request

from app.models import CheckResult
from app.services.monitor import monitor
from config import Config

bp = Blueprint("api", __name__, url_prefix="/api")


def success_response(**payload: Any):
    """Return a standard success JSON response."""
    return jsonify({"success": True, **payload})


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
