"""Application entrypoint for the NetRadar backend TUI."""

from __future__ import annotations

from textual.app import App

from app.tui.screens import ServiceDashboardScreen
from config import Config


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

    #add-service-panel {
        width: 56;
        max-width: 60;
        height: auto;
        background: #000000;
        border: solid #2a2a2a;
        padding: 1 2;
    }

    DeleteServiceModal > * {
        width: 70;
        max-width: 80;
    }

    #add-service-panel Input,
    #add-service-panel Button,
    #add-service-panel Static {
        background: #000000;
    }

    .dialog-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .dialog-actions {
        height: auto;
        width: 100%;
        align: center middle;
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
        self.push_screen(ServiceDashboardScreen(refresh_seconds=Config.TUI_DASHBOARD_REFRESH_SECONDS))


def run_tui() -> None:
    """Run the NetRadar backend TUI."""
    NetRadarTUI().run()
