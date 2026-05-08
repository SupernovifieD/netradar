"""Local/API transport adapters for CLI command execution."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

from app.cli.errors import CLIError, EXIT_API_ERROR, EXIT_LOCAL_RUNTIME, EXIT_TRANSPORT
from app.core.agent_helpers import build_ops_snapshot_payload, evaluate_gate_payload
from app.core.errors import CoreError
from app.core.operations import NetRadarOperations
from app.services.monitor import monitor


class LocalTransport:
    """Transport that executes operations in-process against shared core layer."""

    def __init__(self) -> None:
        self._operations = NetRadarOperations(monitor=monitor)

    def health(self) -> dict[str, Any]:
        return self._safe(self._operations.health)

    def services_list(
        self,
        *,
        search: str | None = None,
        group: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, str]]:
        return self._safe(
            lambda: self._operations.services_list(search=search, group=group, category=category)
        )

    def status_current(self) -> list[dict[str, Any]]:
        return self._safe(self._operations.status_current)

    def history_recent(self, *, limit: int) -> list[dict[str, Any]]:
        return self._safe(lambda: self._operations.history_recent(limit=limit))

    def history_24h(self) -> list[dict[str, Any]]:
        return self._safe(self._operations.history_24h)

    def history_service(self, service: str, *, limit: int) -> list[dict[str, Any]]:
        return self._safe(lambda: self._operations.history_service(service, limit=limit))

    def daily_service(
        self,
        service: str,
        *,
        limit: int,
        before_day: str | None,
    ) -> list[dict[str, Any]]:
        return self._safe(
            lambda: self._operations.daily_service(service, limit=limit, before_day=before_day)
        )

    def daily_services(
        self,
        *,
        day: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        return self._safe(lambda: self._operations.daily_services(day=day, limit=limit, offset=offset))

    def export_raw(self, service: str, *, days: int) -> dict[str, Any]:
        return self._safe(lambda: self._operations.export_raw(service, days=days))

    def export_daily(self, service: str, *, days: int) -> dict[str, Any]:
        return self._safe(lambda: self._operations.export_daily(service, days=days))

    def monitor_start(self) -> dict[str, Any]:
        return self._safe(self._operations.monitor_start)

    def monitor_stop(self) -> dict[str, Any]:
        return self._safe(self._operations.monitor_stop)

    def monitor_status(self) -> dict[str, Any]:
        return self._safe(self._operations.monitor_status)

    def monitor_policy(self) -> dict[str, Any]:
        return self._safe(self._operations.monitor_policy)

    def monitor_runtime(self) -> dict[str, Any]:
        return self._safe(self._operations.monitor_runtime)

    def probe_service(self, service: str) -> dict[str, Any]:
        return self._safe(lambda: self._operations.probe_service(service))

    def ops_snapshot(
        self,
        service: str,
        *,
        history_limit: int,
        daily_limit: int,
    ) -> dict[str, Any]:
        return self._safe(
            lambda: self._operations.ops_snapshot(
                service=service,
                history_limit=history_limit,
                daily_limit=daily_limit,
            )
        )

    def ops_gate(
        self,
        service: str,
        *,
        days: int,
        min_uptime: float,
        max_p95_latency: float,
    ) -> dict[str, Any]:
        return self._safe(
            lambda: self._operations.ops_gate(
                service=service,
                days=days,
                min_uptime=min_uptime,
                max_p95_latency=max_p95_latency,
            )
        )

    @staticmethod
    def _safe(operation):
        try:
            return operation()
        except CoreError as exc:
            raise CLIError(
                code=exc.code,
                message=exc.message,
                exit_code=exc.exit_code,
                details=exc.details,
            ) from exc
        except CLIError:
            raise
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise CLIError(
                code="LOCAL_RUNTIME_ERROR",
                message=str(exc),
                exit_code=EXIT_LOCAL_RUNTIME,
            ) from exc


class ApiTransport:
    """Transport that executes operations over HTTP API."""

    def __init__(self, *, base_url: str, timeout_sec: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_sec

    def health(self) -> dict[str, Any]:
        payload = self._get("/health")
        return {"status": payload["status"]}

    def services_list(
        self,
        *,
        search: str | None = None,
        group: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, str]]:
        payload = self._get(
            "/services",
            params={
                "search": search,
                "group": group,
                "category": category,
            },
        )
        return payload.get("data", [])

    def status_current(self) -> list[dict[str, Any]]:
        payload = self._get("/status")
        return payload.get("data", [])

    def history_recent(self, *, limit: int) -> list[dict[str, Any]]:
        payload = self._get("/history", params={"limit": limit})
        return payload.get("data", [])

    def history_24h(self) -> list[dict[str, Any]]:
        payload = self._get("/history/24h")
        return payload.get("data", [])

    def history_service(self, service: str, *, limit: int) -> list[dict[str, Any]]:
        payload = self._get(
            f"/service/{quote(service, safe='')}",
            params={"limit": limit},
        )
        return payload.get("data", [])

    def daily_service(
        self,
        service: str,
        *,
        limit: int,
        before_day: str | None,
    ) -> list[dict[str, Any]]:
        payload = self._get(
            f"/service/{quote(service, safe='')}/daily",
            params={"limit": limit, "before_day": before_day},
        )
        return payload.get("data", [])

    def daily_services(
        self,
        *,
        day: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        payload = self._get(
            "/daily/services",
            params={"day": day, "limit": limit, "offset": offset},
        )
        return {"day": payload.get("day"), "data": payload.get("data", [])}

    def export_raw(self, service: str, *, days: int) -> dict[str, Any]:
        return self._get(
            f"/service/{quote(service, safe='')}/export/raw",
            params={"days": days},
        )

    def export_daily(self, service: str, *, days: int) -> dict[str, Any]:
        return self._get(
            f"/service/{quote(service, safe='')}/export/daily",
            params={"days": days},
        )

    def monitor_start(self) -> dict[str, Any]:
        return self._post("/monitor/start")

    def monitor_stop(self) -> dict[str, Any]:
        return self._post("/monitor/stop")

    def monitor_status(self) -> dict[str, Any]:
        return self._get("/monitor/status")

    def monitor_policy(self) -> dict[str, Any]:
        return self._get("/monitor/policy")

    def monitor_runtime(self) -> dict[str, Any]:
        return self._get("/monitor/runtime")

    def probe_service(self, service: str) -> dict[str, Any]:
        # Probe command is intentionally local-only in v1.
        raise CLIError(
            code="UNSUPPORTED_IN_API_MODE",
            message="probe.service is only available in local mode",
            exit_code=8,
            details={"mode": "api"},
        )

    def ops_snapshot(
        self,
        service: str,
        *,
        history_limit: int,
        daily_limit: int,
    ) -> dict[str, Any]:
        services = self.services_list()
        service_meta = next((row for row in services if row["domain"] == service), None)

        current_rows = self.status_current()
        current_row = next((row for row in current_rows if row.get("service") == service), None)

        history_rows = self.history_service(service, limit=history_limit)
        daily_rows = self.daily_service(service, limit=daily_limit, before_day=None)
        monitor_state = self.monitor_status()

        return build_ops_snapshot_payload(
            service=service,
            service_meta=service_meta,
            current_row=current_row,
            history_rows=history_rows,
            daily_rows=daily_rows,
            monitor_state=monitor_state,
        )

    def ops_gate(
        self,
        service: str,
        *,
        days: int,
        min_uptime: float,
        max_p95_latency: float,
    ) -> dict[str, Any]:
        export = self.export_daily(service, days=days)
        return evaluate_gate_payload(
            service=service,
            days=days,
            daily_rows=export.get("data", []),
            min_uptime=min_uptime,
            max_p95_latency=max_p95_latency,
            start_day_utc=export.get("start_day_utc"),
            end_day_utc=export.get("end_day_utc"),
        )

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def _post(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", path, params=params)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        filtered_params = {k: v for k, v in (params or {}).items() if v is not None}
        url = f"{self._base_url}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                params=filtered_params,
                timeout=self._timeout,
            )
        except Timeout as exc:
            raise CLIError(
                code="API_TIMEOUT",
                message=f"request timed out: {method} {path}",
                exit_code=EXIT_TRANSPORT,
                details={"url": url, "timeout_sec": self._timeout},
            ) from exc
        except RequestException as exc:
            raise CLIError(
                code="API_TRANSPORT_ERROR",
                message=f"transport error while calling {method} {path}",
                exit_code=EXIT_TRANSPORT,
                details={"url": url, "error": str(exc)},
            ) from exc

        return self._decode_response(method, path, response)

    @staticmethod
    def _decode_response(method: str, path: str, response: Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise CLIError(
                code="API_INVALID_JSON",
                message=f"API response is not valid JSON for {method} {path}",
                exit_code=EXIT_API_ERROR,
                details={"status_code": response.status_code},
            ) from exc

        if response.status_code >= 400:
            message = payload.get("error") if isinstance(payload, dict) else None
            raise CLIError(
                code="API_HTTP_ERROR",
                message=message or f"API returned HTTP {response.status_code}",
                exit_code=EXIT_API_ERROR,
                details={"status_code": response.status_code, "path": path},
            )

        if not isinstance(payload, dict):
            raise CLIError(
                code="API_INVALID_PAYLOAD",
                message=f"API payload is not an object for {method} {path}",
                exit_code=EXIT_API_ERROR,
                details={"path": path},
            )

        if payload.get("success") is not True:
            raise CLIError(
                code="API_ERROR_RESPONSE",
                message=payload.get("error", "API reported an error"),
                exit_code=EXIT_API_ERROR,
                details={"path": path},
            )

        return {k: v for k, v in payload.items() if k != "success"}
