"""Top-level CLI main tests for JSON envelope behavior."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from app.cli.errors import CLIError
from app.cli.main import run_cli


class FakeTransport:
    def health(self):
        return {"status": "healthy"}


class CliMainTests(unittest.TestCase):
    """Validate JSON output contract for success and error paths."""

    @patch("app.cli.main._create_transport", return_value=FakeTransport())
    def test_json_success_envelope(self, _mock_transport) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = run_cli(["--json", "health"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue().strip())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "health")
        self.assertEqual(payload["mode"], "local")
        self.assertIn("timestamp_utc", payload)
        self.assertIn("data", payload)
        self.assertIn("meta", payload)
        self.assertIn("error", payload)

    @patch("app.cli.main._create_transport", return_value=FakeTransport())
    @patch(
        "app.cli.main.execute_command",
        side_effect=CLIError(code="X", message="boom", exit_code=6, details={"a": 1}),
    )
    def test_json_error_envelope(self, _mock_execute, _mock_transport) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = run_cli(["--json", "health"])
        self.assertEqual(exit_code, 6)
        payload = json.loads(stderr.getvalue().strip())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "X")
        self.assertEqual(payload["error"]["message"], "boom")


if __name__ == "__main__":
    unittest.main()
