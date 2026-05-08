"""CLI-specific error types and exit code constants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_VALIDATION = 3
EXIT_EMPTY = 4
EXIT_LOCAL_RUNTIME = 5
EXIT_API_ERROR = 6
EXIT_TRANSPORT = 7
EXIT_UNSUPPORTED_MODE = 8
EXIT_UNEXPECTED = 10


@dataclass(slots=True)
class CLIError(Exception):
    """Structured CLI error for deterministic machine output and exit mapping."""

    code: str
    message: str
    exit_code: int
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message
