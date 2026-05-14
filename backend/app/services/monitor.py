"""Background monitoring loop for service health checks."""

from __future__ import annotations

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.models import CheckWriteRow, CheckResult
from app.services.checker import check_service
from app.services.daily_aggregator import DailyAggregator
from app.services.monitoring_policy import (
    ServiceMonitoringPolicy,
    load_service_monitoring_policies,
    load_service_monitoring_snapshots,
)
from app.time_utils import format_time_for_display
from config import Config

FAILURE_REASONS = {"DNS_FAIL", "TCP_FAIL", "FORBIDDEN", "RATE_LIMITED", "CHECK_EXCEPTION"}


@dataclass(slots=True)
class ServiceRuntimeState:
    """Mutable in-memory runtime state for one monitored service."""

    policy: ServiceMonitoringPolicy
    next_due_at_utc: datetime
    consecutive_failures: int = 0
    current_backoff_seconds: int = 0
    last_probe_reason: str | None = None
    last_http_status_code: int | None = None
    last_checked_at_utc: datetime | None = None


class ServiceMonitor:
    """Run periodic network checks and persist results."""

    def __init__(self) -> None:
        """Initialize monitor state."""
        self.running: bool = False
        self.thread: threading.Thread | None = None
        self.daily_aggregator = DailyAggregator()
        self._state_lock = threading.RLock()
        self._runtime_states: dict[str, ServiceRuntimeState] = {}
        self._rng = random.Random()

    def run_check_cycle(self) -> None:
        """Run one scheduling cycle and probe only due services."""
        now_utc = datetime.now(timezone.utc)
        policies = load_service_monitoring_policies()

        with self._state_lock:
            self._sync_runtime_states(policies=policies, now_utc=now_utc)
            due_domains = [
                domain
                for domain, state in self._runtime_states.items()
                if state.policy.enabled and now_utc >= state.next_due_at_utc
            ]

        self._rng.shuffle(due_domains)
        rows_to_persist: list[CheckWriteRow] = []
        due_count = len(due_domains)

        if due_domains:
            with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
                futures = {executor.submit(check_service, service): service for service in due_domains}

                for future in as_completed(futures):
                    service = futures[future]
                    checked_at_utc = datetime.now(timezone.utc)
                    try:
                        svc, dns, tcp, latency, packet_loss, status, probe_reason, http_status_code = future.result()
                        next_due_str = "-"
                        backoff_seconds = 0
                        rows_to_persist.append(
                            (
                                svc,
                                latency,
                                packet_loss,
                                dns,
                                tcp,
                                status,
                                probe_reason,
                                http_status_code,
                            )
                        )
                        failed = probe_reason in FAILURE_REASONS
                        with self._state_lock:
                            state = self._runtime_states.get(svc)
                            if state is not None:
                                state.last_probe_reason = probe_reason
                                state.last_http_status_code = http_status_code
                                state.last_checked_at_utc = checked_at_utc
                                self._schedule_next_probe(state=state, now_utc=checked_at_utc, failed=failed)
                                next_due_str = format_time_for_display(state.next_due_at_utc)
                                backoff_seconds = state.current_backoff_seconds
                        print(
                            f"[{format_time_for_display(checked_at_utc)}] [{svc}] "
                            f"DNS:{dns} TCP:{tcp} PING:{latency} STATUS:{status} "
                            f"REASON:{probe_reason}"
                            f"{f' HTTP:{http_status_code}' if http_status_code is not None else ''} "
                            f"NEXT:{next_due_str} BACKOFF:{backoff_seconds}s"
                        )
                    except Exception as exc:
                        print(f"Error checking {service}: {exc}")
                        with self._state_lock:
                            state = self._runtime_states.get(service)
                            if state is not None:
                                state.last_probe_reason = "CHECK_EXCEPTION"
                                state.last_http_status_code = None
                                state.last_checked_at_utc = checked_at_utc
                                self._schedule_next_probe(state=state, now_utc=checked_at_utc, failed=True)
        else:
            print(f"[{format_time_for_display(now_utc)}] No services due this cycle.")

        if rows_to_persist:
            try:
                CheckResult.save_many(rows_to_persist)
            except Exception as exc:
                print(f"Error persisting check cycle: {exc}")
                for row in rows_to_persist:
                    try:
                        CheckResult.save(*row)
                    except Exception as row_exc:
                        print(f"Error persisting row for {row[0]}: {row_exc}")

        try:
            self.daily_aggregator.run()
        except Exception as exc:
            print(f"Error aggregating daily history: {exc}")

        print(
            f"[{format_time_for_display(datetime.now(timezone.utc))}] "
            f"Cycle completed (due={due_count}, persisted={len(rows_to_persist)})\n"
        )

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

    def get_policy_snapshot(self) -> dict[str, Any]:
        """Return effective monitor policy and per-service schedule defaults."""
        services = load_service_monitoring_snapshots()
        return {
            "defaults": {
                "check_interval_seconds": Config.CHECK_INTERVAL,
                "service_interval_seconds": Config.DEFAULT_SERVICE_INTERVAL_SECONDS,
                "service_jitter_seconds": Config.DEFAULT_SERVICE_JITTER_SECONDS,
                "max_backoff_seconds": Config.DEFAULT_MAX_BACKOFF_SECONDS,
            },
            "services": [
                {
                    "domain": item.domain,
                    "name": item.name,
                    "group": item.group,
                    "category": item.category,
                    "monitoring": item.monitoring,
                }
                for item in services
            ],
        }

    def get_runtime_snapshot(self) -> dict[str, Any]:
        """Return in-memory runtime scheduling state for monitored services."""
        now_utc = datetime.now(timezone.utc)
        policies = load_service_monitoring_policies()
        with self._state_lock:
            self._sync_runtime_states(policies=policies, now_utc=now_utc)
            services = []
            for domain in sorted(self._runtime_states.keys()):
                state = self._runtime_states[domain]
                services.append(
                    {
                        "domain": domain,
                        "enabled": state.policy.enabled,
                        "interval_seconds": state.policy.interval_seconds,
                        "jitter_seconds": state.policy.jitter_seconds,
                        "max_backoff_seconds": state.policy.max_backoff_seconds,
                        "next_due_at_utc": self._format_dt(state.next_due_at_utc),
                        "consecutive_failures": state.consecutive_failures,
                        "current_backoff_seconds": state.current_backoff_seconds,
                        "last_probe_reason": state.last_probe_reason,
                        "last_http_status_code": state.last_http_status_code,
                        "last_checked_at_utc": self._format_dt(state.last_checked_at_utc),
                    }
                )
        return {"services": services}

    def _sync_runtime_states(
        self,
        *,
        policies: list[ServiceMonitoringPolicy],
        now_utc: datetime,
    ) -> None:
        """Reconcile runtime states with current service policy list."""
        policy_by_domain = {policy.domain: policy for policy in policies}

        removed_domains = [domain for domain in self._runtime_states.keys() if domain not in policy_by_domain]
        for domain in removed_domains:
            self._runtime_states.pop(domain, None)

        for domain, policy in policy_by_domain.items():
            existing = self._runtime_states.get(domain)
            if existing is None:
                initial_delay = self._compute_jitter(policy)
                self._runtime_states[domain] = ServiceRuntimeState(
                    policy=policy,
                    next_due_at_utc=now_utc + timedelta(seconds=initial_delay),
                )
                continue

            existing.policy = policy
            if existing.next_due_at_utc < now_utc - timedelta(days=1):
                existing.next_due_at_utc = now_utc

    def _schedule_next_probe(self, *, state: ServiceRuntimeState, now_utc: datetime, failed: bool) -> None:
        """Update per-service schedule state after a probe result."""
        if failed:
            state.consecutive_failures += 1
            state.current_backoff_seconds = self._compute_backoff(
                interval_seconds=state.policy.interval_seconds,
                max_backoff_seconds=state.policy.max_backoff_seconds,
                consecutive_failures=state.consecutive_failures,
            )
            delay = state.current_backoff_seconds
        else:
            state.consecutive_failures = 0
            state.current_backoff_seconds = 0
            delay = state.policy.interval_seconds

        state.next_due_at_utc = now_utc + timedelta(seconds=delay + self._compute_jitter(state.policy))

    @staticmethod
    def _compute_backoff(
        *,
        interval_seconds: int,
        max_backoff_seconds: int,
        consecutive_failures: int,
    ) -> int:
        """Return exponential backoff duration capped by service policy."""
        multiplier = 2 ** max(0, consecutive_failures - 1)
        return min(max_backoff_seconds, interval_seconds * multiplier)

    def _compute_jitter(self, policy: ServiceMonitoringPolicy) -> float:
        """Return randomized jitter seconds for next due scheduling."""
        if policy.jitter_seconds <= 0:
            return 0.0
        return self._rng.uniform(0.0, float(policy.jitter_seconds))

    @staticmethod
    def _format_dt(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.replace(microsecond=0).isoformat()


# Global monitor instance used by API routes and runtime bootstrap.
monitor = ServiceMonitor()
