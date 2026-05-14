"""Textual screen definitions for the NetRadar backend TUI."""

from __future__ import annotations

from time import monotonic

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from app.services.monitor import monitor
from app.time_utils import format_iso_utc_for_display, format_storage_datetime_for_display, utc_now
from app.tui.catalog import ServiceCatalog, ServiceCatalogItem
from app.tui.render import (
    build_bucket_bar,
    build_bucket_markers,
    build_sparkline,
    compute_series_stats,
    format_updated_at,
    style_backoff_seconds,
    style_dns,
    style_http_status_code,
    style_latency,
    style_metric_value,
    style_packet_loss,
    style_probe_reason,
    style_status,
    style_tcp,
    style_timestamp,
)
from app.tui.stats import (
    ServiceLatestStats,
    build_half_hour_buckets,
    build_latency_and_jitter,
    fetch_latest_stats,
    fetch_recent_checks,
)


def _row_key_to_domain(row_key: object) -> str:
    """Normalize Textual row key objects into string domain keys."""
    return str(getattr(row_key, "value", row_key))


class AddServiceModal(ModalScreen[ServiceCatalogItem | None]):
    """Modal form for creating a new service entry."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="add-service-panel"):
            yield Static("Add Service", classes="dialog-title")
            yield Static("Fill all fields exactly as they should appear in services.json")
            yield Input(placeholder="Domain (e.g. example.com)", id="domain")
            yield Input(placeholder="Display name", id="name")
            yield Input(placeholder="Group (e.g. International Service)", id="group")
            yield Input(placeholder="Category (e.g. General Services)", id="category")

            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="save")

            yield Static("", id="form-error", classes="dialog-error")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return

        domain = self.query_one("#domain", Input).value.strip()
        name = self.query_one("#name", Input).value.strip()
        group = self.query_one("#group", Input).value.strip()
        category = self.query_one("#category", Input).value.strip()

        if not all([domain, name, group, category]):
            self.query_one("#form-error", Static).update("All fields are required.")
            return

        if " " in domain:
            self.query_one("#form-error", Static).update("Domain must not contain whitespace.")
            return

        self.dismiss(
            ServiceCatalogItem(
                domain=domain,
                name=name,
                group=group,
                category=category,
            )
        )


class DeleteServiceModal(ModalScreen[bool]):
    """Destructive confirmation modal for deleting service entries."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, service: ServiceCatalogItem) -> None:
        super().__init__()
        self._service = service

    def compose(self) -> ComposeResult:
        yield Static("Delete Service", classes="dialog-title")
        yield Static(
            f"You are about to delete '{self._service.name}' ({self._service.domain}) from services.json."
        )
        yield Static("This action is irreversible. Type DELETE to confirm.")
        yield Input(placeholder="Type DELETE", id="confirm")

        with Horizontal(classes="dialog-actions"):
            yield Button("Cancel", id="cancel")
            yield Button("Delete", id="delete")

        yield Static("", id="delete-error", classes="dialog-error")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(False)
            return

        confirmation = self.query_one("#confirm", Input).value.strip()
        if confirmation != "DELETE":
            self.query_one("#delete-error", Static).update("Confirmation text does not match DELETE.")
            return

        self.dismiss(True)


class ServiceDetailScreen(Screen):
    """Detail screen for one service with buckets and 6h graphs."""

    AUTO_REFRESH_SECONDS = 60

    BINDINGS = [
        Binding("b", "back", "Back"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, service: ServiceCatalogItem) -> None:
        super().__init__()
        self._service = service
        self._refresh_timer: Timer | None = None
        self._last_refresh_monotonic: float | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with VerticalScroll(id="detail-scroll"):
            yield Static("", id="detail-meta")
            yield Static("", id="detail-buckets")
            yield Static("", id="detail-latency")
            yield Static("", id="detail-jitter")
            yield Static("Press b or Esc to go back. Press q to quit. Press r to refresh.", classes="detail-hint")

        yield Footer()

    def on_mount(self) -> None:
        self._refresh()
        self._refresh_timer = self.set_interval(self.AUTO_REFRESH_SECONDS, self._auto_refresh_tick)

    def on_unmount(self) -> None:
        if self._refresh_timer is not None:
            self._refresh_timer.stop()
            self._refresh_timer = None

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self._refresh()

    def action_quit(self) -> None:
        self.app.exit()

    def _auto_refresh_tick(self) -> None:
        """Refresh on timer only after the full interval has elapsed."""
        if self._last_refresh_monotonic is not None:
            elapsed = monotonic() - self._last_refresh_monotonic
            if elapsed < float(self.AUTO_REFRESH_SECONDS):
                return
        self._refresh()

    def _refresh(self) -> None:
        self._last_refresh_monotonic = monotonic()
        rows = fetch_recent_checks(self._service.domain, limit=10_000)
        runtime_rows = monitor.get_runtime_snapshot().get("services", [])
        runtime_by_domain = {
            row.get("domain"): row
            for row in runtime_rows
            if isinstance(row, dict) and row.get("domain")
        }
        runtime = runtime_by_domain.get(self._service.domain, {})

        meta_widget = self.query_one("#detail-meta", Static)
        buckets_widget = self.query_one("#detail-buckets", Static)
        latency_widget = self.query_one("#detail-latency", Static)
        jitter_widget = self.query_one("#detail-jitter", Static)

        meta_text = Text()
        meta_text.append(f"Service: {self._service.name}\n", style="bold")
        meta_text.append(f"Domain: {self._service.domain}\n")
        meta_text.append(f"Group: {self._service.group}\n")
        meta_text.append(f"Category: {self._service.category}\n")

        if rows:
            latest = rows[0]
            meta_text.append("Latest Status: ")
            meta_text.append_text(style_status(latest.get("status", "NO_DATA")))
            meta_text.append(" | DNS: ")
            meta_text.append_text(style_dns(latest.get("dns", "NO_DATA")))
            meta_text.append(" | TCP: ")
            meta_text.append_text(style_tcp(latest.get("tcp", "NO_DATA")))
            meta_text.append(" | Latency: ")
            meta_text.append_text(style_latency(latest.get("latency", "na")))
            meta_text.append(" ms | Loss: ")
            meta_text.append_text(style_packet_loss(latest.get("packet_loss", "na")))
            meta_text.append(" | Reason: ")
            meta_text.append_text(style_probe_reason(str(latest.get("probe_reason") or "UNKNOWN")))
            meta_text.append(" | HTTP: ")
            meta_text.append_text(style_http_status_code(latest.get("http_status_code")))
            meta_text.append(" | Last Seen: ")
            meta_text.append_text(
                style_timestamp(
                    format_storage_datetime_for_display(
                        str(latest.get("date") or ""),
                        str(latest.get("time") or ""),
                    )
                )
            )
            next_due_raw = str(runtime.get("next_due_at_utc") or "").strip()
            next_due = format_iso_utc_for_display(next_due_raw) if next_due_raw else "n/a"
            meta_text.append("\nNext Check: ")
            meta_text.append_text(style_timestamp(next_due))
            meta_text.append(" | Backoff: ")
            meta_text.append_text(style_backoff_seconds(int(runtime.get("current_backoff_seconds") or 0)))
        else:
            meta_text.append("No checks are available yet for this service.", style="#9f9f9f")

        meta_widget.update(meta_text)

        buckets = build_half_hour_buckets(rows, bucket_count=12)
        bucket_width = self._content_width(buckets_widget)
        bucket_text = Text()
        bucket_text.append("6h window (30-minute slots, newest on the right)\n", style="bold")
        bucket_text.append_text(
            build_bucket_bar(
                buckets,
                width=bucket_width,
                newest_on_right=True,
            )
        )
        bucket_text.append("\n")
        bucket_text.append_text(
            build_bucket_markers(
                buckets,
                width=bucket_width,
                newest_on_right=True,
                marker_every_buckets=2,
            )
        )
        buckets_widget.update(bucket_text)

        latency_points, jitter_points = build_latency_and_jitter(rows, window_hours=6)
        latency_graph_width = self._content_width(latency_widget)
        jitter_graph_width = self._content_width(jitter_widget)

        latency_text = Text("Latency Graph (last 6 hours)\n", style="bold")
        if latency_points:
            latency_text.append(
                build_sparkline(latency_points, width=latency_graph_width),
                style="#4ea3ff",
            )
            stats = compute_series_stats(latency_points)
            if stats is not None:
                latency_text.append("\nmin:")
                latency_text.append_text(style_metric_value(stats.minimum, kind="latency"))
                latency_text.append(" ms  avg:")
                latency_text.append_text(style_metric_value(stats.average, kind="latency"))
                latency_text.append(" ms  max:")
                latency_text.append_text(style_metric_value(stats.maximum, kind="latency"))
                latency_text.append(" ms")
        else:
            latency_text.append("No latency data in the last 6 hours.", style="#9f9f9f")

        latency_widget.update(latency_text)

        jitter_text = Text("Jitter Graph (last 6 hours)\n", style="bold")
        if jitter_points:
            jitter_text.append(
                build_sparkline(jitter_points, width=jitter_graph_width),
                style="#ffd166",
            )
            stats = compute_series_stats(jitter_points)
            if stats is not None:
                jitter_text.append("\nmin:")
                jitter_text.append_text(style_metric_value(stats.minimum, kind="jitter"))
                jitter_text.append(" ms  avg:")
                jitter_text.append_text(style_metric_value(stats.average, kind="jitter"))
                jitter_text.append(" ms  max:")
                jitter_text.append_text(style_metric_value(stats.maximum, kind="jitter"))
                jitter_text.append(" ms")
        else:
            jitter_text.append("Not enough samples to compute jitter in the last 6 hours.", style="#9f9f9f")

        jitter_widget.update(jitter_text)

    @staticmethod
    def _content_width(widget: Static, *, minimum: int = 24) -> int:
        """Compute an approximate drawable width inside a bordered/padded box."""
        return max(minimum, widget.size.width - 4)


class ServiceDashboardScreen(Screen):
    """Main dashboard screen that lists services and latest stats."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("/", "focus_search", "Search"),
        Binding("escape", "cancel_search", "Cancel Search"),
        Binding("a", "add_service", "Add"),
        Binding("d", "delete_service", "Delete"),
    ]

    def __init__(self, *, refresh_seconds: int = 900) -> None:
        super().__init__()
        self._catalog = ServiceCatalog()
        self._search_query = ""
        self._stats: list[ServiceLatestStats] = []
        self._current_domain: str | None = None
        self._refresh_seconds = refresh_seconds

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            "Enter: open service details | /: search | Esc: clear search | a: add service | d: delete service | r: refresh",
            id="dashboard-help",
        )
        yield Input(placeholder="Search by name or domain...", id="search-input")

        table = DataTable(id="services-table", zebra_stripes=True)
        table.add_columns(
            "Name",
            "Domain",
            "Status",
            "Reason",
            "HTTP",
            "DNS",
            "TCP",
            "Latency",
            "Loss",
            "Backoff",
            "Next Due",
            "Last Seen",
        )
        yield table

        yield Static("", id="services-status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#services-table", DataTable)
        table.cursor_type = "row"
        table.focus()
        self._refresh()
        self.set_interval(self._refresh_seconds, self._refresh)

    def action_quit(self) -> None:
        self.app.exit()

    def action_refresh(self) -> None:
        self._refresh()

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_cancel_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        if search_input.value:
            search_input.value = ""
        self._search_query = ""
        visible_count = self._render_table()
        self.query_one("#services-table", DataTable).focus()

        if visible_count > 0:
            self._set_status(f"Search cleared. Showing {visible_count} services.")

    def action_add_service(self) -> None:
        self.app.push_screen(AddServiceModal(), self._after_add_service)

    def action_delete_service(self) -> None:
        if not self._current_domain:
            self._set_status("No service selected for deletion.")
            return

        try:
            service = next(item for item in self._catalog.load() if item.domain == self._current_domain)
        except StopIteration:
            self._set_status("Selected service no longer exists in services.json.")
            self._refresh()
            return

        self.app.push_screen(DeleteServiceModal(service), lambda confirmed: self._after_delete_service(service, confirmed))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search-input":
            return

        self._search_query = event.value.strip().lower()
        visible_count = self._render_table()
        if visible_count > 0:
            scope = self._search_query or "*"
            self._set_status(f"Search '{scope}': {visible_count} services shown.")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self._current_domain = _row_key_to_domain(event.row_key)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        domain = _row_key_to_domain(event.row_key)
        try:
            service = next(item for item in self._catalog.load() if item.domain == domain)
        except StopIteration:
            self._set_status("Service not found in services catalog.")
            self._refresh()
            return

        self.app.push_screen(ServiceDetailScreen(service))

    def _refresh(self) -> None:
        try:
            catalog_items = self._catalog.load()
        except Exception as exc:
            self._set_status(f"Failed to load services catalog: {exc}")
            return

        runtime_rows = monitor.get_runtime_snapshot().get("services", [])
        runtime_by_domain = {
            row.get("domain"): row
            for row in runtime_rows
            if isinstance(row, dict) and row.get("domain")
        }
        self._stats = fetch_latest_stats(catalog_items, runtime_by_domain=runtime_by_domain)
        visible_count = self._render_table()

        total = len(self._stats)
        updated_at = format_updated_at(utc_now())
        if visible_count > 0:
            self._set_status(
                f"Loaded {total} services. Showing {visible_count}. "
                f"Auto-refresh every {self._refresh_seconds // 60} minutes. Updated {updated_at}"
            )

    def _render_table(self) -> int:
        table = self.query_one("#services-table", DataTable)
        table.clear(columns=False)

        query = self._search_query
        visible_count = 0
        visible_domains: list[str] = []

        for stats in self._stats:
            service = stats.service
            text = f"{service.name} {service.domain}".lower()
            if query and query not in text:
                continue

            visible_count += 1
            visible_domains.append(service.domain)
            next_due = format_iso_utc_for_display(stats.next_due_at_utc) if stats.next_due_at_utc else "n/a"
            table.add_row(
                service.name,
                service.domain,
                style_status(stats.status),
                style_probe_reason(stats.probe_reason),
                style_http_status_code(stats.http_status_code),
                style_dns(stats.dns),
                style_tcp(stats.tcp),
                style_latency(stats.latency),
                style_packet_loss(stats.packet_loss),
                style_backoff_seconds(stats.current_backoff_seconds),
                style_timestamp(next_due),
                style_timestamp(stats.last_seen),
                key=service.domain,
            )

        if visible_count == 0:
            self._current_domain = None
            self._set_status("No services match the current search query.")
            return 0

        if self._current_domain not in visible_domains:
            self._current_domain = visible_domains[0]

        return visible_count

    def _after_add_service(self, added: ServiceCatalogItem | None) -> None:
        if added is None:
            self._set_status("Add service cancelled.")
            return

        try:
            self._catalog.add(added)
        except ValueError as exc:
            self._set_status(str(exc))
            return
        except Exception as exc:
            self._set_status(f"Failed to add service: {exc}")
            return

        self._set_status(f"Service added: {added.domain}")
        self._refresh()

    def _after_delete_service(self, service: ServiceCatalogItem, confirmed: bool) -> None:
        if not confirmed:
            self._set_status("Delete operation cancelled.")
            return

        try:
            removed = self._catalog.remove_by_domain(service.domain)
        except Exception as exc:
            self._set_status(f"Failed to delete service: {exc}")
            return

        if not removed:
            self._set_status("Service not found. It may have already been removed.")
            return

        self._current_domain = None
        self._set_status(f"Service deleted: {service.domain}")
        self._refresh()

    def _set_status(self, message: str) -> None:
        self.query_one("#services-status", Static).update(message)
