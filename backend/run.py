#!/usr/bin/env python3
"""Executable entrypoint for the NetRadar backend API server."""

from __future__ import annotations

from app import create_app
from app.services.monitor import monitor

app = create_app()


def print_startup_banner() -> None:
    """Print API URL and available endpoints."""
    print("\nFlask API running on http://localhost:5001")
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
    print("  GET  /api/health                       - Health check\n")


def main() -> None:
    """Start the monitor and run the Flask development server."""
    monitor.start()
    print_startup_banner()
    app.run(host="0.0.0.0", port=5001, debug=False)


if __name__ == "__main__":
    main()
