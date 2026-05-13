#!/usr/bin/env python3
"""Executable entrypoint for the NetRadar backend API server."""

from __future__ import annotations

from app import create_app
from app.services.monitor import monitor
from config import Config

app = create_app()


def print_startup_banner() -> None:
    """Print API URL and available endpoints."""
    display_host = "localhost" if Config.HOST in {"0.0.0.0", "::"} else Config.HOST
    print(f"\nFlask API running on http://{display_host}:{Config.PORT}")
    print("API endpoints:")
    print("  GET  /api/status                       - Current status of all services")
    print("  GET  /api/history                      - Recent check history")
    print("  GET  /api/history/24h                  - 24h check history")
    print("  GET  /api/services                     - Services metadata")
    print("  GET  /api/service/<name>               - History for specific service")
    print("  GET  /api/service/<name>/daily         - Daily history for a specific service")
    print("  GET  /api/service/<name>/export/raw    - Raw checks export (max 90 days)")
    print("  GET  /api/service/<name>/export/daily  - Daily summary export (max 90 days)")
    print("  GET  /api/daily/services               - Daily summaries for all services")
    print("  POST /api/monitor/start                - Start monitoring")
    print("  POST /api/monitor/stop                 - Stop monitoring")
    print("  GET  /api/monitor/status               - Monitor runtime state")
    print("  GET  /api/monitor/policy               - Effective monitor policy")
    print("  GET  /api/monitor/runtime              - Per-service due/backoff state")
    print("  GET  /api/health                       - Health check\n")


def main() -> None:
    """Start the monitor and run the Flask development server."""
    monitor.start()
    print_startup_banner()
    app.run(host=Config.HOST, port=Config.PORT, debug=False)


if __name__ == "__main__":
    main()
