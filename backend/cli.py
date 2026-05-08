#!/usr/bin/env python3
"""NetRadar CLI entrypoint."""

from __future__ import annotations

import sys

from app.cli import run_cli


def main() -> None:
    """Execute CLI and exit with its code."""
    raise SystemExit(run_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()
