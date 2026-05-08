"""API regression tests for monitor status endpoint."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import create_app


class ApiMonitorStatusTests(unittest.TestCase):
    """Verify monitor introspection endpoint response shapes."""

    def test_monitor_status_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            class TestConfig:
                BASE_DIR = Path(tmp_dir)
                DATABASE_PATH = str(BASE_DIR / "test_raw.db")
                DAILY_DATABASE_PATH = str(BASE_DIR / "test_daily.db")
                DAILY_BACKFILL_DAYS = 1
                SERVICES_FILE = str(Path(__file__).resolve().parents[2] / "services.json")
                CHECK_INTERVAL = 15
                MAX_WORKERS = 2

            app = create_app(TestConfig)
            client = app.test_client()
            response = client.get("/api/monitor/status")
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertTrue(payload["success"])
            self.assertIn("running", payload)
            self.assertIn("thread_alive", payload)

            policy_response = client.get("/api/monitor/policy")
            self.assertEqual(policy_response.status_code, 200)
            policy_payload = policy_response.get_json()
            self.assertTrue(policy_payload["success"])
            self.assertIn("defaults", policy_payload)
            self.assertIn("services", policy_payload)

            runtime_response = client.get("/api/monitor/runtime")
            self.assertEqual(runtime_response.status_code, 200)
            runtime_payload = runtime_response.get_json()
            self.assertTrue(runtime_payload["success"])
            self.assertIn("services", runtime_payload)


if __name__ == "__main__":
    unittest.main()
