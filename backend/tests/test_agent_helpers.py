"""Tests for reusable AI-agent operational helper logic."""

from __future__ import annotations

import unittest

from app.core.agent_helpers import evaluate_gate_payload


class AgentHelpersTests(unittest.TestCase):
    """Validate deterministic gate evaluation behavior."""

    def test_gate_no_daily_data(self) -> None:
        payload = evaluate_gate_payload(
            service="google.com",
            days=30,
            daily_rows=[],
            min_uptime=99.0,
            max_p95_latency=120.0,
            start_day_utc="2026-04-01",
            end_day_utc="2026-05-01",
        )
        self.assertFalse(payload["passed"])
        self.assertIn("NO_DAILY_DATA", payload["reasons"])

    def test_gate_passes_with_good_metrics(self) -> None:
        rows = [
            {
                "overall_status": "UP",
                "uptime_rate_pct": 99.9,
                "p95_latency_ms": 55.0,
            },
            {
                "overall_status": "UP",
                "uptime_rate_pct": 99.5,
                "p95_latency_ms": 65.0,
            },
        ]
        payload = evaluate_gate_payload(
            service="google.com",
            days=2,
            daily_rows=rows,
            min_uptime=99.0,
            max_p95_latency=90.0,
        )
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["reasons"], [])

    def test_gate_fails_on_high_latency(self) -> None:
        rows = [
            {
                "overall_status": "DEGRADED",
                "uptime_rate_pct": 99.2,
                "p95_latency_ms": 180.0,
            }
        ]
        payload = evaluate_gate_payload(
            service="google.com",
            days=1,
            daily_rows=rows,
            min_uptime=99.0,
            max_p95_latency=120.0,
        )
        self.assertFalse(payload["passed"])
        self.assertIn("HIGH_P95_LATENCY", payload["reasons"])


if __name__ == "__main__":
    unittest.main()
