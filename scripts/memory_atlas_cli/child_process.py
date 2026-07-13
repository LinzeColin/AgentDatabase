"""Shared child-process execution for Memory Atlas CLI command modules."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO


StdoutTransform = Callable[[str, int], str]


def run_child_command(
    command: Sequence[str],
    *,
    cwd: Path,
    stdout_stream: TextIO | None = None,
    stderr_stream: TextIO | None = None,
    stdout_transform: StdoutTransform | None = None,
) -> int:
    """Run one child and preserve its streams and exit code by default."""

    result = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        output = stdout_transform(result.stdout, result.returncode) if stdout_transform else result.stdout
    except Exception:
        if result.stderr:
            (stderr_stream if stderr_stream is not None else sys.stderr).write(result.stderr)
        raise
    if output:
        (stdout_stream if stdout_stream is not None else sys.stdout).write(output)
    if result.stderr:
        (stderr_stream if stderr_stream is not None else sys.stderr).write(result.stderr)
    return result.returncode


__all__ = (
    "StdoutTransform",
    "run_child_command",
)
