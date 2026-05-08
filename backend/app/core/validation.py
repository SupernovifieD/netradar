"""Validation helpers shared across API and CLI layers."""

from __future__ import annotations

from datetime import datetime

from app.core.errors import CoreError


def validate_day(day_value: str, *, field_name: str = "day") -> str:
    """Validate ``YYYY-MM-DD`` day string and return normalized value."""
    try:
        parsed = datetime.strptime(day_value, "%Y-%m-%d")
    except ValueError as exc:
        raise CoreError(
            code="INVALID_DAY_FORMAT",
            message=f"{field_name} must be in YYYY-MM-DD format",
            details={"field": field_name, "value": day_value},
            http_status=400,
            exit_code=3,
        ) from exc
    return parsed.strftime("%Y-%m-%d")


def validate_positive_int(value: int, *, field_name: str) -> int:
    """Validate that an integer is positive."""
    if value <= 0:
        raise CoreError(
            code="INVALID_POSITIVE_INT",
            message=f"{field_name} must be a positive integer",
            details={"field": field_name, "value": value},
            http_status=400,
            exit_code=3,
        )
    return value


def validate_non_negative_int(value: int, *, field_name: str) -> int:
    """Validate that an integer is zero or positive."""
    if value < 0:
        raise CoreError(
            code="INVALID_NON_NEGATIVE_INT",
            message=f"{field_name} must be zero or a positive integer",
            details={"field": field_name, "value": value},
            http_status=400,
            exit_code=3,
        )
    return value
