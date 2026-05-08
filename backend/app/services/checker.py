"""Network probing utilities used by the monitoring loop.

The functions in this module intentionally keep return shapes stable because
their outputs are persisted directly to the database.
"""

from __future__ import annotations

import socket
import subprocess
from typing import Final

import requests
from requests.exceptions import RequestException

DNS_TIMEOUT_SECONDS: Final[int] = 2
HTTP_TIMEOUT_SECONDS: Final[int] = 2
PING_COUNT: Final[int] = 4
PING_TIMEOUT_SECONDS: Final[int] = 1
HTTP_HEADERS: Final[dict[str, str]] = {
    "User-Agent": "NetRadar/1.0 (+https://github.com/netradar)",
    "Accept": "*/*",
}

ServiceCheckResult = tuple[str, str, str, str, str, str, str, int | None]


def dns_check(domain: str, timeout: int = DNS_TIMEOUT_SECONDS) -> str:
    """Return ``OK`` if DNS resolves, otherwise ``FAIL``."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname(domain)
        return "OK"
    except Exception:
        return "FAIL"


def _classify_http_response(protocol: str, status_code: int) -> tuple[str, str, int]:
    """Map HTTP response status to normalized transport/probe reason."""
    if status_code == 403:
        return (protocol, "FORBIDDEN", status_code)
    if status_code == 429:
        return (protocol, "RATE_LIMITED", status_code)
    return (protocol, "OK", status_code)


def tcp_check(domain: str) -> tuple[str, str, int | None]:
    """Return transport accessibility state for a domain.

    Priority is HTTPS first, then HTTP, then ``FAIL`` if both fail.
    """
    try:
        response = requests.head(
            f"https://{domain}",
            timeout=HTTP_TIMEOUT_SECONDS,
            allow_redirects=True,
            verify=False,
            headers=HTTP_HEADERS,
        )
        return _classify_http_response("HTTPS", response.status_code)
    except RequestException:
        pass

    try:
        response = requests.head(
            f"http://{domain}",
            timeout=HTTP_TIMEOUT_SECONDS,
            allow_redirects=True,
            headers=HTTP_HEADERS,
        )
        return _classify_http_response("HTTP", response.status_code)
    except RequestException:
        return ("FAIL", "TCP_FAIL", None)

    return ("FAIL", "TCP_FAIL", None)


def ping_stats(domain: str) -> tuple[str, str]:
    """Return ``(latency, packet_loss)`` strings derived from ping output."""
    try:
        result = subprocess.run(
            ["ping", "-c", str(PING_COUNT), "-W", str(PING_TIMEOUT_SECONDS), domain],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            return ("na", "100")

        output = result.stdout
        loss_line = [line for line in output.split("\n") if "packet loss" in line]
        packet_loss = (
            loss_line[0].split(",")[2].strip().split("%")[0] if loss_line else "100"
        )

        avg_line = [line for line in output.split("\n") if "avg" in line or "mdev" in line]
        latency = avg_line[0].split("=")[1].split("/")[1].strip() if avg_line else "na"

        return (latency, packet_loss)
    except Exception:
        return ("na", "100")


def compute_status(dns: str, tcp: str) -> str:
    """Compute normalized service status from probe outputs.

    The ``dns`` argument is intentionally kept in the signature for backward
    compatibility, even though status currently depends on ``tcp`` only.
    """
    return "UP" if tcp != "FAIL" else "DOWN"


def check_service(service: str) -> ServiceCheckResult:
    """Run all configured checks for one service domain."""
    dns = dns_check(service)
    if dns == "OK":
        tcp, probe_reason, http_status_code = tcp_check(service)
    else:
        tcp, probe_reason, http_status_code = ("FAIL", "DNS_FAIL", None)
    latency, packet_loss = ping_stats(service)
    status = compute_status(dns, tcp)
    return (service, dns, tcp, latency, packet_loss, status, probe_reason, http_status_code)
