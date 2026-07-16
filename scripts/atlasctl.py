#!/usr/bin/env python3
"""Compatible thin entry point for the Memory Atlas control CLI."""

from __future__ import annotations

import sys as _sys

from memory_atlas_cli.analyze import *
from memory_atlas_cli.apply import *
from memory_atlas_cli.build import *
from memory_atlas_cli.chatgpt_export_request import *
from memory_atlas_cli.chatgpt_export_human_auth import *
from memory_atlas_cli.chatgpt_export_state import *
from memory_atlas_cli.chatgpt_notification_connector import *
from memory_atlas_cli.constants import *
from memory_atlas_cli.dispatch import dispatch
from memory_atlas_cli.parser import *
from memory_atlas_cli.push import *
from memory_atlas_cli.runtime import *
from memory_atlas_cli.sync import *
from memory_atlas_cli.validate import *


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
        if exit_code != 0:
            emit_bootstrap_rejection(
                RuntimeErrorCode.ARGUMENT_INVALID,
                command=command_from_argv(argv),
                exit_code=exit_code,
                machine_stream=_sys.stderr,
            )
        raise
    try:
        return dispatch(args)
    except RuntimeConfigError:
        emit_bootstrap_rejection(
            RuntimeErrorCode.CONFIG_INVALID,
            command=args.command,
            machine_stream=_sys.stderr,
        )
        return 2


__all__ = tuple(name for name in globals() if not name.startswith("_"))


if __name__ == "__main__":
    raise SystemExit(main())
