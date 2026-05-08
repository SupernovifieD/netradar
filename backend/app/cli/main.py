"""Main entrypoint implementation for NetRadar CLI."""

from __future__ import annotations

import sys
import traceback
from argparse import Namespace
from typing import Sequence

from app.cli.errors import (
    CLIError,
    EXIT_UNEXPECTED,
)
from app.cli.output import (
    build_error_envelope,
    build_success_envelope,
    dumps_json,
    render_human,
)
from app.cli.parser import build_parser
from app.cli.runner import execute_command
from app.cli.transport import ApiTransport, LocalTransport


def run_cli(argv: Sequence[str] | None = None) -> int:
    """Run CLI command and return process exit code."""
    parser = build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        return int(exc.code)

    command_id = str(getattr(args, "command_id", "unknown"))
    mode = args.mode

    try:
        transport = _create_transport(args)
        data, meta = execute_command(args, transport)

        envelope = build_success_envelope(
            command=command_id,
            mode=mode,
            data=data,
            meta=meta,
        )

        if args.json_output:
            print(dumps_json(envelope))
        else:
            print(render_human(command_id, data, meta))

        return 0
    except CLIError as exc:
        envelope = build_error_envelope(
            command=command_id,
            mode=mode,
            error_code=exc.code,
            message=exc.message,
            details=exc.details,
            meta={},
        )

        if args.json_output:
            print(dumps_json(envelope), file=sys.stderr)
        else:
            print(f"Error [{exc.code}]: {exc.message}", file=sys.stderr)

        if args.debug:
            traceback.print_exc(file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive top-level boundary
        envelope = build_error_envelope(
            command=command_id,
            mode=mode,
            error_code="UNEXPECTED_ERROR",
            message=str(exc),
            details=None,
            meta={},
        )
        if args.json_output:
            print(dumps_json(envelope), file=sys.stderr)
        else:
            print(f"Unexpected error: {exc}", file=sys.stderr)
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        return EXIT_UNEXPECTED


def _create_transport(args: Namespace):
    if args.mode == "local":
        return LocalTransport()
    return ApiTransport(base_url=args.api_base_url, timeout_sec=args.timeout_sec)
