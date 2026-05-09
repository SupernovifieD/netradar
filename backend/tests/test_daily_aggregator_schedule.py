"""Schedule-aware daily aggregation unit tests."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from app.services.daily_aggregator import DailyAggregator
from app.services.monitoring_policy import ServiceMonitoringPolicy


class DailyAggregatorScheduleTests(unittest.TestCase):
    """Validate cadence-aware duration math for daily summaries."""

    def setUp(self) -> None:
        self.aggregator = DailyAggregator()
        self.day_start = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.policy_5m = ServiceMonitoringPolicy(
            domain="example.com",
            enabled=True,
            interval_seconds=300,
            jitter_seconds=6,
            max_backoff_seconds=600,
        )

    def test_sparse_interval_day_does_not_count_false_no_data(self) -> None:
        rows = []
        current = self.day_start
        while current < self.day_start + timedelta(days=1):
            rows.append(
                {
                    "service": "example.com",
                    "date": current.strftime("%Y-%m-%d"),
                    "time": current.strftime("%H:%M:%S"),
                    "status": "UP",
                    "latency": "25.0",
                }
            )
            current += timedelta(seconds=300)

        summary, intervals = self.aggregator._build_service_day_summary(  # noqa: SLF001
            policy=self.policy_5m,
            day_start_utc=self.day_start,
            service_rows=rows,
        )
        self.assertEqual(summary["uptime_seconds"], 86400)
        self.assertEqual(summary["downtime_seconds"], 0)
        self.assertEqual(summary["no_data_seconds"], 0)
        self.assertEqual(summary["checks_no_data"], 0)
        self.assertEqual(summary["overall_status"], "UP")
        self.assertEqual(intervals, [])

    def test_no_rows_day_is_full_no_data(self) -> None:
        summary, intervals = self.aggregator._build_service_day_summary(  # noqa: SLF001
            policy=self.policy_5m,
            day_start_utc=self.day_start,
            service_rows=[],
        )
        self.assertEqual(summary["uptime_seconds"], 0)
        self.assertEqual(summary["downtime_seconds"], 0)
        self.assertEqual(summary["no_data_seconds"], 86400)
        self.assertEqual(summary["coverage_rate_pct"], 0.0)
        self.assertEqual(summary["overall_status"], "NO_DATA")
        self.assertTrue(intervals)
        self.assertEqual(intervals[0]["interval_type"], "NO_DATA")
        self.assertEqual(intervals[0]["duration_seconds"], 86400)

    def test_low_uptime_day_is_degraded_with_new_threshold(self) -> None:
        rows = []
        current = self.day_start
        slot_index = 0
        while current < self.day_start + timedelta(days=1):
            rows.append(
                {
                    "service": "example.com",
                    "date": current.strftime("%Y-%m-%d"),
                    "time": current.strftime("%H:%M:%S"),
                    "status": "UP" if slot_index < 72 else "DOWN",
                    "latency": "30.0",
                }
            )
            current += timedelta(seconds=300)
            slot_index += 1

        summary, _intervals = self.aggregator._build_service_day_summary(  # noqa: SLF001
            policy=self.policy_5m,
            day_start_utc=self.day_start,
            service_rows=rows,
        )
        self.assertEqual(summary["uptime_rate_pct"], 25.0)
        self.assertEqual(summary["overall_status"], "DEGRADED")


if __name__ == "__main__":
    unittest.main()
