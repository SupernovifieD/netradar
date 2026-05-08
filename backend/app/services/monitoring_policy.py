"""Service monitoring policy parsing from ``services.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from config import Config


@dataclass(slots=True, frozen=True)
class ServiceMonitoringPolicy:
    """Effective monitoring policy for one service."""

    domain: str
    enabled: bool
    interval_seconds: int
    jitter_seconds: int
    max_backoff_seconds: int


@dataclass(slots=True, frozen=True)
class ServiceMonitoringSnapshot:
    """Snapshot used by API/CLI monitor policy introspection."""

    domain: str
    name: str
    group: str
    category: str
    monitoring: dict[str, Any]


def load_service_monitoring_policies() -> list[ServiceMonitoringPolicy]:
    """Load effective monitoring policies for all configured services."""
    with open(Config.SERVICES_FILE, encoding="utf-8") as service_file:
        services = json.load(service_file)

    policies: list[ServiceMonitoringPolicy] = []
    for service in services:
        domain = str(service.get("domain", "")).strip()
        if not domain:
            continue
        monitoring_raw = service.get("monitoring")
        monitoring = monitoring_raw if isinstance(monitoring_raw, dict) else {}
        policy = _build_policy(domain, monitoring)
        policies.append(policy)
    return policies


def load_service_monitoring_snapshots() -> list[ServiceMonitoringSnapshot]:
    """Load user-facing service rows with resolved monitoring defaults."""
    with open(Config.SERVICES_FILE, encoding="utf-8") as service_file:
        services = json.load(service_file)

    snapshots: list[ServiceMonitoringSnapshot] = []
    for service in services:
        domain = str(service.get("domain", "")).strip()
        if not domain:
            continue

        monitoring_raw = service.get("monitoring")
        monitoring = monitoring_raw if isinstance(monitoring_raw, dict) else {}
        policy = _build_policy(domain, monitoring)
        snapshots.append(
            ServiceMonitoringSnapshot(
                domain=domain,
                name=str(service.get("name", "")).strip(),
                group=str(service.get("group", "")).strip(),
                category=str(service.get("category", "")).strip(),
                monitoring={
                    "enabled": policy.enabled,
                    "interval_seconds": policy.interval_seconds,
                    "jitter_seconds": policy.jitter_seconds,
                    "max_backoff_seconds": policy.max_backoff_seconds,
                },
            )
        )
    return snapshots


def _build_policy(domain: str, monitoring: dict[str, Any]) -> ServiceMonitoringPolicy:
    enabled = _coerce_bool(monitoring.get("enabled"), default=True)
    interval_seconds = _coerce_int(
        monitoring.get("interval_seconds"),
        default=Config.DEFAULT_SERVICE_INTERVAL_SECONDS,
        minimum=1,
    )
    jitter_seconds = _coerce_int(
        monitoring.get("jitter_seconds"),
        default=Config.DEFAULT_SERVICE_JITTER_SECONDS,
        minimum=0,
    )
    if jitter_seconds > interval_seconds:
        jitter_seconds = interval_seconds

    max_backoff_seconds = _coerce_int(
        monitoring.get("max_backoff_seconds"),
        default=Config.DEFAULT_MAX_BACKOFF_SECONDS,
        minimum=interval_seconds,
    )
    return ServiceMonitoringPolicy(
        domain=domain,
        enabled=enabled,
        interval_seconds=interval_seconds,
        jitter_seconds=jitter_seconds,
        max_backoff_seconds=max_backoff_seconds,
    )


def _coerce_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _coerce_int(value: Any, *, default: int, minimum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    if parsed < minimum:
        return minimum
    return parsed
