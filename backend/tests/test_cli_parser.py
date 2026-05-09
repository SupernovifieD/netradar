"""Parser-level tests for NetRadar CLI."""

from __future__ import annotations

import unittest

from app.cli.parser import build_parser


class CliParserTests(unittest.TestCase):
    """Validate command taxonomy and argument wiring."""

    def setUp(self) -> None:
        self.parser = build_parser()

    def test_history_recent_parsing(self) -> None:
        args = self.parser.parse_args(["history", "recent", "--limit", "12"])
        self.assertEqual(args.command_id, "history.recent")
        self.assertEqual(args.limit, 12)
        self.assertEqual(args.mode, "local")

    def test_daily_service_parsing(self) -> None:
        args = self.parser.parse_args(
            ["--mode", "api", "daily", "service", "google.com", "--before-day", "2026-05-01"]
        )
        self.assertEqual(args.command_id, "daily.service")
        self.assertEqual(args.service, "google.com")
        self.assertEqual(args.before_day, "2026-05-01")
        self.assertEqual(args.mode, "api")

    def test_ops_gate_parsing(self) -> None:
        args = self.parser.parse_args(
            [
                "ops",
                "gate",
                "google.com",
                "--days",
                "14",
                "--min-uptime",
                "98.5",
                "--max-p95-latency",
                "85.0",
            ]
        )
        self.assertEqual(args.command_id, "ops.gate")
        self.assertEqual(args.service, "google.com")
        self.assertEqual(args.days, 14)
        self.assertAlmostEqual(args.min_uptime, 98.5)
        self.assertAlmostEqual(args.max_p95_latency, 85.0)

    def test_monitor_runtime_parsing(self) -> None:
        args = self.parser.parse_args(["--mode", "api", "monitor", "runtime"])
        self.assertEqual(args.command_id, "monitor.runtime")
        self.assertEqual(args.mode, "api")

    def test_services_add_parsing(self) -> None:
        args = self.parser.parse_args(
            [
                "services",
                "add",
                "example.com",
                "--name",
                "Example",
                "--group",
                "International Service",
                "--category",
                "General Services",
                "--enabled",
                "true",
                "--interval-seconds",
                "120",
            ]
        )
        self.assertEqual(args.command_id, "services.add")
        self.assertEqual(args.domain, "example.com")
        self.assertTrue(args.enabled)
        self.assertEqual(args.interval_seconds, 120)


if __name__ == "__main__":
    unittest.main()
