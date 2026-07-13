"""Command dispatch for the Memory Atlas CLI."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from .analyze import run_analyze
from .apply import run_apply, run_proposals
from .build import (
    run_build_atlas,
    run_chatgpt_deep_explore,
    run_generate_personalization_prompt,
)
from .push import run_push
from .sync import run_profile, run_sync
from .validate import run_audit


RUNNERS: dict[str, Callable[[argparse.Namespace], int]] = {
    "run": run_profile,
    "sync": run_sync,
    "build-atlas": run_build_atlas,
    "analyze": run_analyze,
    "audit": run_audit,
    "push": run_push,
    "generate-personalization-prompt": run_generate_personalization_prompt,
    "chatgpt-deep-explore": run_chatgpt_deep_explore,
    "deep-explore": run_chatgpt_deep_explore,
    "proposals": run_proposals,
    "apply": run_apply,
}


def dispatch(args: argparse.Namespace) -> int:
    runner = RUNNERS.get(args.command)
    if runner is None:
        raise AssertionError(f"unhandled command: {args.command}")
    return runner(args)
