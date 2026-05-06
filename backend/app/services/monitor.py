"""Background monitoring loop for service health checks."""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from app.models import CheckResult
from app.services.checker import check_service
from config import Config


class ServiceMonitor:
    """Run periodic network checks and persist results."""

    def __init__(self) -> None:
        """Initialize monitor state."""
        self.running: bool = False
        self.thread: threading.Thread | None = None

    def load_services(self) -> list[str]:
        """Load monitored domain names from ``services.json``."""
        with open(Config.SERVICES_FILE, encoding="utf-8") as service_file:
            services = json.load(service_file)
        return [service["domain"] for service in services]

    def run_check_cycle(self) -> None:
        """Run one complete concurrent check cycle for all configured services."""
        services = self.load_services()

        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            futures = {executor.submit(check_service, service): service for service in services}

            for future in as_completed(futures):
                service = futures[future]
                try:
                    svc, dns, tcp, latency, packet_loss, status = future.result()

                    CheckResult.save(svc, latency, packet_loss, dns, tcp, status)

                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] [{svc}] "
                        f"DNS:{dns} TCP:{tcp} PING:{latency} STATUS:{status}"
                    )
                except Exception as exc:
                    print(f"Error checking {service}: {exc}")

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Cycle completed\n")

    def monitor_loop(self) -> None:
        """Execute monitoring cycles until stopped."""
        while self.running:
            self.run_check_cycle()
            time.sleep(Config.CHECK_INTERVAL)

    def start(self) -> None:
        """Start the monitor on a daemon thread if not already running."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        print("Service monitor started")

    def stop(self) -> None:
        """Stop monitoring and wait for the worker thread to exit."""
        self.running = False
        if self.thread is not None:
            self.thread.join()
        print("Service monitor stopped")


# Global monitor instance used by API routes and runtime bootstrap.
monitor = ServiceMonitor()
