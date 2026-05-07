"""Application entrypoint for the NetRadar backend TUI."""

from __future__ import annotations

from textual.app import App

from app.tui.screens import ServiceDashboardScreen


class NetRadarTUI(App[None]):
    """Top-level Textual application for backend monitoring operations."""

    TITLE = "NetRadar Backend TUI"
    SUB_TITLE = "Service status, history buckets, and catalog management"

    CSS = """
    Screen {
        padding: 1 2;
    }

    #dashboard-help {
        margin-bottom: 1;
        color: #8a8a8a;
    }

    #search-input {
        margin-bottom: 1;
    }

    #services-table {
        height: 1fr;
        margin-bottom: 1;
    }

    #services-status {
        height: auto;
        color: #9f9f9f;
        margin-bottom: 1;
    }

    #detail-scroll {
        height: 1fr;
        padding: 0 0 1 0;
    }

    #detail-meta,
    #detail-buckets,
    #detail-latency,
    #detail-jitter {
        margin-bottom: 1;
        border: solid #333333;
        padding: 1;
    }

    .detail-hint {
        color: #888888;
    }

    AddServiceModal,
    DeleteServiceModal {
        align: center middle;
    }

    AddServiceModal > * ,
    DeleteServiceModal > * {
        width: 70;
        max-width: 80;
    }

    .dialog-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .dialog-actions {
        height: auto;
        margin-top: 1;
        margin-bottom: 1;
    }

    .dialog-actions Button {
        margin-right: 1;
    }

    .dialog-error {
        color: #e74c3c;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(ServiceDashboardScreen(refresh_seconds=15 * 60))


def run_tui() -> None:
    """Run the NetRadar backend TUI."""
    NetRadarTUI().run()
