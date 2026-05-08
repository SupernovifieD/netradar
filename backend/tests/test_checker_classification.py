"""Unit tests for checker status/reason classification behavior."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.checker import _classify_http_response, check_service


class CheckerClassificationTests(unittest.TestCase):
    """Verify HTTP reason mapping and raw probe tuple behavior."""

    def test_http_response_classification(self) -> None:
        self.assertEqual(_classify_http_response("HTTPS", 200), ("HTTPS", "OK", 200))
        self.assertEqual(_classify_http_response("HTTPS", 403), ("HTTPS", "FORBIDDEN", 403))
        self.assertEqual(_classify_http_response("HTTP", 429), ("HTTP", "RATE_LIMITED", 429))

    @patch("app.services.checker.ping_stats", return_value=("12.5", "0"))
    @patch("app.services.checker.dns_check", return_value="FAIL")
    def test_dns_fail_sets_down_and_reason(self, _mock_dns, _mock_ping) -> None:
        result = check_service("example.com")
        self.assertEqual(result[0], "example.com")
        self.assertEqual(result[1], "FAIL")
        self.assertEqual(result[2], "FAIL")
        self.assertEqual(result[5], "DOWN")
        self.assertEqual(result[6], "DNS_FAIL")
        self.assertIsNone(result[7])

    @patch("app.services.checker.ping_stats", return_value=("42.0", "0"))
    @patch("app.services.checker.tcp_check", return_value=("HTTPS", "FORBIDDEN", 403))
    @patch("app.services.checker.dns_check", return_value="OK")
    def test_forbidden_keeps_service_up_with_reason(self, _mock_dns, _mock_tcp, _mock_ping) -> None:
        result = check_service("example.com")
        self.assertEqual(result[5], "UP")
        self.assertEqual(result[6], "FORBIDDEN")
        self.assertEqual(result[7], 403)


if __name__ == "__main__":
    unittest.main()
