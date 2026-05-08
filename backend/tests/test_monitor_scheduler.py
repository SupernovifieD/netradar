"""Unit tests for due scheduling and backoff behavior."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.services.monitor import ServiceMonitor, ServiceRuntimeState
from app.services.monitoring_policy import ServiceMonitoringPolicy


class MonitorSchedulerTests(unittest.TestCase):
    """Validate scheduler backoff growth, cap, and reset semantics."""

    def setUp(self) -> None:
        self.monitor = ServiceMonitor()
        self.monitor._compute_jitter = lambda _policy: 0.0  # type: ignore[assignment]
        self.policy = ServiceMonitoringPolicy(
            domain="example.com",
            enabled=True,
            interval_seconds=60,
            jitter_seconds=6,
            max_backoff_seconds=600,
        )

    def test_compute_backoff_caps_at_max(self) -> None:
        values = [
            self.monitor._compute_backoff(
                interval_seconds=60,
                max_backoff_seconds=600,
                consecutive_failures=failures,
            )
            for failures in (1, 2, 3, 4, 5, 6, 7, 8)
        ]
        self.assertEqual(values, [60, 120, 240, 480, 600, 600, 600, 600])

    def test_schedule_next_probe_resets_on_success(self) -> None:
        now = datetime(2026, 5, 8, 0, 0, tzinfo=timezone.utc)
        state = ServiceRuntimeState(policy=self.policy, next_due_at_utc=now)

        self.monitor._schedule_next_probe(state=state, now_utc=now, failed=True)
        self.assertEqual(state.consecutive_failures, 1)
        self.assertEqual(state.current_backoff_seconds, 60)

        self.monitor._schedule_next_probe(state=state, now_utc=now, failed=True)
        self.assertEqual(state.consecutive_failures, 2)
        self.assertEqual(state.current_backoff_seconds, 120)

        self.monitor._schedule_next_probe(state=state, now_utc=now, failed=False)
        self.assertEqual(state.consecutive_failures, 0)
        self.assertEqual(state.current_backoff_seconds, 0)
        self.assertEqual(int((state.next_due_at_utc - now).total_seconds()), 60)


if __name__ == "__main__":
    unittest.main()
