"""Service catalog persistence for the backend TUI.

This module is intentionally small and pure so the UI layer can rely on
clear, testable operations for loading and mutating ``services.json``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from config import Config


@dataclass(slots=True, frozen=True)
class ServiceCatalogItem:
    """One service entry stored in ``services.json``."""

    domain: str
    name: str
    group: str
    category: str

    def as_dict(self) -> dict[str, str]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "domain": self.domain,
            "name": self.name,
            "group": self.group,
            "category": self.category,
        }


class ServiceCatalog:
    """Read/write wrapper around ``services.json`` used by the TUI."""

    def __init__(self, file_path: str | None = None) -> None:
        self._file_path = Path(file_path or Config.SERVICES_FILE)

    @property
    def file_path(self) -> Path:
        """Expose the catalog file path for diagnostics."""
        return self._file_path

    def load(self) -> list[ServiceCatalogItem]:
        """Load all services from the catalog file."""
        with self._file_path.open(encoding="utf-8") as service_file:
            raw_items = json.load(service_file)

        items: list[ServiceCatalogItem] = []
        for item in raw_items:
            items.append(
                ServiceCatalogItem(
                    domain=item["domain"].strip(),
                    name=item["name"].strip(),
                    group=item["group"].strip(),
                    category=item["category"].strip(),
                )
            )
        return items

    def save(self, items: list[ServiceCatalogItem]) -> None:
        """Persist catalog items, sorted by domain for deterministic diffs."""
        serialized = [item.as_dict() for item in sorted(items, key=lambda entry: entry.domain)]
        with self._file_path.open("w", encoding="utf-8") as service_file:
            json.dump(serialized, service_file, indent=2, ensure_ascii=False)
            service_file.write("\n")

    def add(self, item: ServiceCatalogItem) -> None:
        """Insert a new service into the catalog.

        Raises:
            ValueError: If another entry already uses the same domain.
        """
        current = self.load()
        if any(existing.domain == item.domain for existing in current):
            raise ValueError(f"Service domain already exists: {item.domain}")
        current.append(item)
        self.save(current)

    def remove_by_domain(self, domain: str) -> bool:
        """Delete one service by domain.

        Returns:
            ``True`` if a service was removed, otherwise ``False``.
        """
        current = self.load()
        remaining = [item for item in current if item.domain != domain]
        if len(remaining) == len(current):
            return False

        self.save(remaining)
        return True
