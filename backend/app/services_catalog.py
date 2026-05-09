"""Service catalog helpers shared by API, CLI, and TUI layers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import Config

_MONITORING_UNSET = object()


@dataclass(slots=True, frozen=True)
class ServiceCatalogItem:
    """One service entry stored in ``services.json``."""

    domain: str
    name: str
    group: str
    category: str
    monitoring: dict[str, Any] | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        output: dict[str, Any] = {
            "domain": self.domain,
            "name": self.name,
            "group": self.group,
            "category": self.category,
        }
        if self.monitoring is not None:
            output["monitoring"] = self.monitoring
        output.update(self.extras)
        return output


class ServiceCatalog:
    """Read/write wrapper around ``services.json``."""

    def __init__(self, file_path: str | None = None) -> None:
        self._file_path = Path(file_path or Config.SERVICES_FILE)

    @property
    def file_path(self) -> Path:
        """Expose catalog file path for diagnostics."""
        return self._file_path

    def load(self) -> list[ServiceCatalogItem]:
        """Load all services from the catalog file."""
        with self._file_path.open(encoding="utf-8") as service_file:
            raw_items = json.load(service_file)

        items: list[ServiceCatalogItem] = []
        for item in raw_items:
            monitoring = item.get("monitoring")
            extras = {
                key: value
                for key, value in item.items()
                if key not in {"domain", "name", "group", "category", "monitoring"}
            }
            items.append(
                ServiceCatalogItem(
                    domain=item["domain"].strip(),
                    name=item["name"].strip(),
                    group=item["group"].strip(),
                    category=item["category"].strip(),
                    monitoring=monitoring if isinstance(monitoring, dict) else None,
                    extras=extras,
                )
            )
        return items

    def load_dicts(self) -> list[dict[str, Any]]:
        """Load all catalog rows as dictionaries."""
        return [item.as_dict() for item in self.load()]

    def add(self, item: ServiceCatalogItem) -> None:
        """Insert a new service.

        Raises:
            ValueError: If another entry already uses the same domain.
        """
        current = self.load()
        if any(existing.domain == item.domain for existing in current):
            raise ValueError(f"Service domain already exists: {item.domain}")
        current.append(item)
        self._save(current)

    def update_by_domain(
        self,
        domain: str,
        *,
        new_domain: str | None = None,
        name: str | None = None,
        group: str | None = None,
        category: str | None = None,
        monitoring: dict[str, Any] | None | object = _MONITORING_UNSET,
    ) -> ServiceCatalogItem | None:
        """Update one service by current domain.

        Args:
            domain: Existing service domain key.
            new_domain: Optional replacement domain key.
            name: Optional replacement display name.
            group: Optional replacement group label.
            category: Optional replacement category label.
            monitoring: Optional monitoring object patch. Pass ``None`` to clear.

        Returns:
            Updated service item when found, otherwise ``None``.

        Raises:
            ValueError: If ``new_domain`` collides with another service.
        """
        current = self.load()
        for index, existing in enumerate(current):
            if existing.domain != domain:
                continue

            resolved_domain = (new_domain or existing.domain).strip()
            if resolved_domain != existing.domain and any(
                other.domain == resolved_domain for other in current
            ):
                raise ValueError(f"Service domain already exists: {resolved_domain}")

            if monitoring is _MONITORING_UNSET:
                resolved_monitoring = existing.monitoring
            elif isinstance(monitoring, dict):
                if isinstance(existing.monitoring, dict):
                    resolved_monitoring = {**existing.monitoring, **monitoring}
                else:
                    resolved_monitoring = dict(monitoring)
            else:
                resolved_monitoring = None

            updated = ServiceCatalogItem(
                domain=resolved_domain,
                name=(name or existing.name).strip(),
                group=(group or existing.group).strip(),
                category=(category or existing.category).strip(),
                monitoring=resolved_monitoring,
                extras=existing.extras,
            )
            current[index] = updated
            self._save(current)
            return updated

        return None

    def remove_by_domain(self, domain: str) -> bool:
        """Delete one service by domain.

        Returns:
            ``True`` if a service was removed, otherwise ``False``.
        """
        current = self.load()
        remaining = [item for item in current if item.domain != domain]
        if len(remaining) == len(current):
            return False
        self._save(remaining)
        return True

    def has_domain(self, domain: str) -> bool:
        """Return ``True`` when the domain exists in the catalog."""
        return any(item.domain == domain for item in self.load())

    def _save(self, items: list[ServiceCatalogItem]) -> None:
        """Persist catalog items sorted by domain for deterministic diffs."""
        serialized = [item.as_dict() for item in sorted(items, key=lambda entry: entry.domain)]
        with self._file_path.open("w", encoding="utf-8") as service_file:
            json.dump(serialized, service_file, indent=2, ensure_ascii=False)
            service_file.write("\n")
