"""Tests for preserving monitoring and unknown keys in services catalog writes."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.services_catalog import ServiceCatalog, ServiceCatalogItem


class ServicesCatalogPreservationTests(unittest.TestCase):
    """Ensure add/remove flows do not strip non-core keys."""

    def test_monitoring_and_extras_are_preserved_after_save_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "services.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "domain": "example.com",
                            "name": "Example",
                            "group": "International Service",
                            "category": "General Services",
                            "monitoring": {
                                "enabled": True,
                                "interval_seconds": 300,
                                "jitter_seconds": 10,
                                "max_backoff_seconds": 600,
                            },
                            "note": "keep-me",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            catalog = ServiceCatalog(str(file_path))
            catalog.add(
                ServiceCatalogItem(
                    domain="zz-temp.example",
                    name="Temp",
                    group="International Service",
                    category="General Services",
                )
            )
            catalog.remove_by_domain("zz-temp.example")

            saved = json.loads(file_path.read_text(encoding="utf-8"))
            row = next(item for item in saved if item["domain"] == "example.com")
            self.assertEqual(row["note"], "keep-me")
            self.assertEqual(row["monitoring"]["interval_seconds"], 300)
            self.assertEqual(row["monitoring"]["max_backoff_seconds"], 600)


if __name__ == "__main__":
    unittest.main()
