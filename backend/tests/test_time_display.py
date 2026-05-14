"""Timestamp storage and local display tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.db import init_db
from app.models import CheckResult
from app.time_utils import format_storage_datetime_for_display
from config import Config


class TimeDisplayTests(unittest.TestCase):
    """Validate UTC database writes and configurable display timezone conversion."""

    def test_raw_check_save_uses_utc_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "checks.db")
            init_db(db_path)

            fixed_now = datetime(2026, 5, 1, 23, 15, 30, tzinfo=timezone.utc)
            with (
                patch.object(Config, "DATABASE_PATH", db_path),
                patch("app.models.utc_now", return_value=fixed_now),
            ):
                CheckResult.save("example.com", "12.3", "0", "OK", "HTTPS", "UP")
                rows = CheckResult.get_latest(limit=1)

            self.assertEqual(rows[0]["date"], "2026-05-01")
            self.assertEqual(rows[0]["time"], "23:15:30")

    def test_storage_timestamp_formats_in_display_timezone(self) -> None:
        with patch.dict(os.environ, {"NETRADAR_DISPLAY_TIMEZONE": "Asia/Tokyo"}, clear=False):
            rendered = format_storage_datetime_for_display("2026-05-01", "00:00:00")

        self.assertEqual(rendered, "2026-05-01 09:00:00")


if __name__ == "__main__":
    unittest.main()
