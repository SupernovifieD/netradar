"""Rich render helpers and color formatters for the backend TUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from rich.text import Text

from app.tui.stats import BucketSummary, SeriesPoint

SPARK_CHARS = "▁▂▃▄▅▆▇█"

BUCKET_COLOR_HEX = {
    "green": "#2ecc71",
    "darkgreen": "#1e8c4e",
    "orange": "#e67e22",
    "blue": "#3498db",
    "darkblue": "#1f5f8b",
    "red": "#e74c3c",
    "grey": "#666666",
}


@dataclass(slots=True, frozen=True)
class SeriesStats:
    """Summary statistics for a numeric time series."""

    minimum: float
    maximum: float
    average: float


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: str, style: str | None = None) -> Text:
    return Text(value, style=style)


def style_status(value: str) -> Text:
    """Return styled status text."""
    if value == "UP":
        return _text("UP", "bold #2ecc71")
    if value == "DOWN":
        return _text("DOWN", "bold #e74c3c")
    return _text("NO DATA", "#9f9f9f")


def style_dns(value: str) -> Text:
    """Return styled DNS result text."""
    if value == "OK":
        return _text("OK", "#2ecc71")
    if value == "FAIL":
        return _text("FAIL", "#e74c3c")
    return _text("NO DATA", "#9f9f9f")


def style_tcp(value: str) -> Text:
    """Return styled TCP/HTTP result text."""
    if value == "HTTPS":
        return _text("HTTPS", "#2ecc71")
    if value == "HTTP":
        return _text("HTTP", "#f1c40f")
    if value == "FAIL":
        return _text("FAIL", "#e74c3c")
    return _text("NO DATA", "#9f9f9f")


def style_probe_reason(value: str) -> Text:
    """Return styled probe-reason text."""
    if value in {"OK"}:
        return _text(value, "#2ecc71")
    if value in {"FORBIDDEN", "RATE_LIMITED"}:
        return _text(value, "#f1c40f")
    if value in {"DNS_FAIL", "TCP_FAIL", "CHECK_EXCEPTION"}:
        return _text(value, "#e74c3c")
    if value in {"NO_DATA"}:
        return _text(value, "#9f9f9f")
    return _text(value or "UNKNOWN", "#a6a6a6")


def style_http_status_code(value: int | None) -> Text:
    """Return styled HTTP status-code text."""
    if value is None:
        return _text("-", "#9f9f9f")
    if 200 <= value < 300:
        return _text(str(value), "#2ecc71")
    if value in {403, 429}:
        return _text(str(value), "#f1c40f")
    if 400 <= value < 600:
        return _text(str(value), "#e74c3c")
    return _text(str(value), "#a6a6a6")


def style_backoff_seconds(value: int) -> Text:
    """Return styled backoff seconds text."""
    if value <= 0:
        return _text("0s", "#2ecc71")
    if value <= 180:
        return _text(f"{value}s", "#f1c40f")
    return _text(f"{value}s", "#e67e22")


def style_latency(value: str) -> Text:
    """Return styled latency text with thresholds."""
    parsed = _parse_float(value)
    if parsed is None:
        return _text("n/a", "#9f9f9f")

    if parsed < 40:
        style = "#2ecc71"
    elif parsed < 100:
        style = "#f1c40f"
    else:
        style = "#e74c3c"

    return _text(f"{parsed:.1f}", style)


def style_packet_loss(value: str) -> Text:
    """Return styled packet-loss percentage text."""
    parsed = _parse_float(value)
    if parsed is None:
        return _text("n/a", "#9f9f9f")

    if parsed <= 0:
        style = "#2ecc71"
    elif parsed <= 5:
        style = "#f1c40f"
    else:
        style = "#e74c3c"

    return _text(f"{parsed:.0f}%", style)


def style_timestamp(value: str) -> Text:
    """Return styled timestamp text."""
    if value == "n/a":
        return _text("n/a", "#9f9f9f")
    return _text(value, "#a6a6a6")


def _bucket_token_to_style(color_token: str) -> str:
    return BUCKET_COLOR_HEX.get(color_token, "#666666")


def _ordered_buckets(buckets: list[BucketSummary], *, newest_on_right: bool) -> list[BucketSummary]:
    """Return buckets in visual left-to-right order."""
    if newest_on_right:
        return buckets
    return list(reversed(buckets))


def _position_to_bucket_index(position: int, *, width: int, bucket_count: int) -> int:
    """Map a rendered horizontal position to a source bucket index."""
    if bucket_count <= 1 or width <= 1:
        return 0

    ratio = position / (width - 1)
    return int(round(ratio * (bucket_count - 1)))


def build_bucket_bar(
    buckets: list[BucketSummary],
    *,
    width: int | None = None,
    newest_on_right: bool = False,
) -> Text:
    """Render a bucket bar that can stretch edge-to-edge of its container."""
    if not buckets:
        return _text("No bucket data", "#9f9f9f")

    ordered_buckets = _ordered_buckets(buckets, newest_on_right=newest_on_right)
    target_width = max(1, width or len(ordered_buckets))

    output = Text()
    for position in range(target_width):
        bucket_index = _position_to_bucket_index(
            position,
            width=target_width,
            bucket_count=len(ordered_buckets),
        )
        output.append("█", style=_bucket_token_to_style(ordered_buckets[bucket_index].color))
    return output


def build_bucket_markers(
    buckets: list[BucketSummary],
    *,
    width: int,
    newest_on_right: bool = False,
    marker_every_buckets: int = 2,
) -> Text:
    """Render timeline marker labels aligned with the bucket ribbon width."""
    if not buckets or width <= 0:
        return Text()

    ordered_buckets = _ordered_buckets(buckets, newest_on_right=newest_on_right)
    bucket_count = len(ordered_buckets)

    boundary_labels: list[tuple[int, str]] = []
    marker_step = max(1, marker_every_buckets)
    for boundary_index in range(0, bucket_count + 1, marker_step):
        if boundary_index == bucket_count:
            label = ordered_buckets[-1].end.strftime("%H:%M")
        else:
            label = ordered_buckets[boundary_index].start.strftime("%H:%M")
        boundary_labels.append((boundary_index, label))

    if boundary_labels[-1][0] != bucket_count:
        boundary_labels.append((bucket_count, ordered_buckets[-1].end.strftime("%H:%M")))

    chars = [" "] * width
    last_written = -1

    for boundary_index, label in boundary_labels:
        if width == 1 or bucket_count == 0:
            position = 0
        else:
            position = int(round((boundary_index / bucket_count) * (width - 1)))

        label_length = len(label)
        start = max(0, min(width - label_length, position - (label_length // 2)))

        if start <= last_written:
            start = last_written + 1

        if start + label_length > width:
            start = width - label_length

        if start < 0 or start <= last_written:
            continue

        for char_index, char in enumerate(label):
            chars[start + char_index] = char
        last_written = start + label_length - 1

    return Text("".join(chars), style="#a8a8a8")


def _resample_values(values: list[float], width: int) -> list[float]:
    """Resample values to a fixed width using nearest-point interpolation."""
    if width <= 0:
        return []
    if not values:
        return []
    if len(values) == width:
        return values
    if len(values) == 1:
        return [values[0]] * width
    if width == 1:
        return [values[-1]]

    output: list[float] = []
    source_max_index = len(values) - 1
    target_max_index = width - 1
    for target_index in range(width):
        ratio = target_index / target_max_index
        source_index = int(round(ratio * source_max_index))
        output.append(values[source_index])
    return output


def build_sparkline(points: list[SeriesPoint], *, width: int = 120) -> str:
    """Render a unicode sparkline for a numeric series."""
    if not points:
        return ""

    values = [point.value for point in points]
    values = _resample_values(values, width)

    min_value = min(values)
    max_value = max(values)
    if max_value == min_value:
        return SPARK_CHARS[0] * len(values)

    span = max_value - min_value
    output_chars: list[str] = []

    for value in values:
        normalized = (value - min_value) / span
        char_index = int(round(normalized * (len(SPARK_CHARS) - 1)))
        output_chars.append(SPARK_CHARS[char_index])

    return "".join(output_chars)


def compute_series_stats(points: list[SeriesPoint]) -> SeriesStats | None:
    """Compute min/max/average for a series."""
    if not points:
        return None

    values = [point.value for point in points]
    return SeriesStats(
        minimum=min(values),
        maximum=max(values),
        average=sum(values) / len(values),
    )


def style_metric_value(value: float, *, kind: str) -> Text:
    """Colorize a numeric metric based on kind-specific thresholds."""
    if kind == "latency":
        if value < 40:
            style = "#2ecc71"
        elif value < 100:
            style = "#f1c40f"
        else:
            style = "#e74c3c"
    else:  # jitter
        if value < 5:
            style = "#2ecc71"
        elif value < 20:
            style = "#f1c40f"
        else:
            style = "#e74c3c"

    return _text(f"{value:.2f}", style)


def format_updated_at(now: datetime) -> str:
    """Return uniform timestamp text for footer/status messages."""
    return now.strftime("%Y-%m-%d %H:%M:%S")
