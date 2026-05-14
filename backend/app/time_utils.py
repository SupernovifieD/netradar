"""Helpers for UTC storage and local display time."""

from __future__ import annotations

import os
from datetime import datetime, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

STORAGE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DISPLAY_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DISPLAY_TIME_FORMAT = "%H:%M:%S"


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def display_timezone() -> tzinfo:
    """Return the configured timezone for terminal/TUI display."""
    for name in (os.environ.get("NETRADAR_DISPLAY_TIMEZONE"), os.environ.get("TZ")):
        if not name or not name.strip():
            continue
        try:
            return ZoneInfo(name.strip())
        except ZoneInfoNotFoundError:
            continue

    return datetime.now().astimezone().tzinfo or timezone.utc


def to_display_time(value: datetime) -> datetime:
    """Convert a datetime to the configured display timezone."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(display_timezone())


def parse_utc_storage_datetime(date_value: str, time_value: str) -> datetime:
    """Parse raw-check date/time fields as UTC."""
    parsed = datetime.strptime(f"{date_value} {time_value}", STORAGE_DATETIME_FORMAT)
    return parsed.replace(tzinfo=timezone.utc)


def format_utc_storage_datetime(value: datetime) -> str:
    """Format a datetime for UTC database storage."""
    return value.astimezone(timezone.utc).strftime(STORAGE_DATETIME_FORMAT)


def format_datetime_for_display(value: datetime) -> str:
    """Format a datetime for terminal/TUI display."""
    return to_display_time(value).strftime(DISPLAY_DATETIME_FORMAT)


def format_time_for_display(value: datetime) -> str:
    """Format only local display time from a datetime."""
    return to_display_time(value).strftime(DISPLAY_TIME_FORMAT)


def format_storage_datetime_for_display(date_value: str, time_value: str) -> str:
    """Format raw-check UTC date/time fields for terminal/TUI display."""
    if not date_value or not time_value:
        return "n/a"
    try:
        return format_datetime_for_display(parse_utc_storage_datetime(date_value, time_value))
    except ValueError:
        return f"{date_value} {time_value}".strip() or "n/a"


def format_iso_utc_for_display(value: str) -> str:
    """Format an ISO UTC timestamp for terminal/TUI display."""
    if not value:
        return "n/a"

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value

    return format_datetime_for_display(parsed)
