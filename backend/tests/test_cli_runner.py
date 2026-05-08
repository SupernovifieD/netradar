"""Runner-level tests for CLI mode guards and output side effects."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.cli.errors import CLIError, EXIT_EMPTY, EXIT_UNSUPPORTED_MODE
from app.cli.parser import build_parser
from app.cli.runner import execute_command


class FakeTransport:
    """Minimal transport double for runner tests."""

    def monitor_status(self):
        return {"running": True, "thread_alive": True}

    def monitor_policy(self):
        return {"defaults": {"check_interval_seconds": 60}, "services": []}

    def monitor_runtime(self):
        return {"services": []}

    def probe_service(self, service: str):
        return {"service": service, "status": "UP"}

    def history_recent(self, *, limit: int):
        if limit == 0:
            return []
        return [{"id": 1, "service": "google.com", "status": "UP"}]

    def export_raw(self, service: str, *, days: int):
        return {
            "service": service,
            "days": days,
            "start_utc": "2026-05-01 00:00:00",
            "end_utc": "2026-05-02 00:00:00",
            "data": [{"id": 1, "service": service}],
        }


class CliRunnerTests(unittest.TestCase):
    """Validate mode guards and fail-on-empty behavior."""

    def setUp(self) -> None:
        self.parser = build_parser()
        self.transport = FakeTransport()

    def test_monitor_commands_are_api_mode_only(self) -> None:
        args = self.parser.parse_args(["monitor", "policy"])
        with self.assertRaises(CLIError) as context:
            execute_command(args, self.transport)
        self.assertEqual(context.exception.exit_code, EXIT_UNSUPPORTED_MODE)

    def test_probe_is_local_mode_only(self) -> None:
        args = self.parser.parse_args(["--mode", "api", "probe", "service", "google.com"])
        with self.assertRaises(CLIError) as context:
            execute_command(args, self.transport)
        self.assertEqual(context.exception.exit_code, EXIT_UNSUPPORTED_MODE)

    def test_fail_on_empty_maps_to_exit_4(self) -> None:
        args = self.parser.parse_args(["--fail-on-empty", "history", "recent", "--limit", "0"])
        with self.assertRaises(CLIError) as context:
            execute_command(args, self.transport)
        self.assertEqual(context.exception.exit_code, EXIT_EMPTY)

    def test_export_out_writes_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "export.json"
            args = self.parser.parse_args(
                ["export", "raw", "google.com", "--days", "2", "--out", str(out_path)]
            )
            data, meta = execute_command(args, self.transport)
            self.assertTrue(out_path.exists())
            self.assertEqual(meta["output_file"]["records"], 1)
            self.assertEqual(data["service"], "google.com")


if __name__ == "__main__":
    unittest.main()
