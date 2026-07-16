"""Command dispatch for the Memory Atlas CLI."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import TextIO

from .analyze import run_analyze
from .apply import run_apply, run_proposals
from .build import (
    run_build_atlas,
    run_chatgpt_deep_explore,
    run_generate_personalization_prompt,
)
from .chatgpt_export_state import (
    run_chatgpt_export_state,
    run_stateful_chatgpt_export_request,
)
from .push import run_push
from .runtime import RuntimeConfig, execute_with_runtime
from .sync import run_profile, run_sync
from .validate import run_audit


RUNNERS: dict[str, Callable[[argparse.Namespace], int]] = {
    "run": run_profile,
    "sync": run_sync,
    "request-chatgpt-export": run_stateful_chatgpt_export_request,
    "chatgpt-export-state": run_chatgpt_export_state,
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


def dispatch(
    args: argparse.Namespace,
    *,
    runtime_config: RuntimeConfig | None = None,
    machine_stream: TextIO | None = None,
    env: Mapping[str, str] | None = None,
    clock: Callable[[], datetime] | None = None,
    monotonic: Callable[[], float] | None = None,
    run_id_factory: Callable[[], str] | None = None,
) -> int:
    runner = RUNNERS.get(args.command)
    if runner is None:
        raise AssertionError(f"unhandled command: {args.command}")
    return execute_with_runtime(
        args,
        runner,
        config=runtime_config,
        machine_stream=machine_stream,
        env=env,
        clock=clock,
        monotonic=monotonic,
        run_id_factory=run_id_factory,
    )
