"""Domain-level error types for shared NetRadar operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CoreError(Exception):
    """Structured operation error with stable code and status mapping."""

    code: str
    message: str
    details: dict[str, Any] | None = None
    http_status: int = 400
    exit_code: int = 3

    def __str__(self) -> str:
        return self.message
