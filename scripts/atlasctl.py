#!/usr/bin/env python3
"""Compatible thin entry point for the Memory Atlas control CLI."""

from __future__ import annotations

from memory_atlas_cli.analyze import *
from memory_atlas_cli.apply import *
from memory_atlas_cli.build import *
from memory_atlas_cli.constants import *
from memory_atlas_cli.dispatch import dispatch
from memory_atlas_cli.parser import *
from memory_atlas_cli.push import *
from memory_atlas_cli.sync import *
from memory_atlas_cli.validate import *


def main(argv: list[str] | None = None) -> int:
    return dispatch(parse_args(argv))


__all__ = tuple(name for name in globals() if not name.startswith("_"))


if __name__ == "__main__":
    raise SystemExit(main())
