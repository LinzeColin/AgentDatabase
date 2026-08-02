from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .arena import execute_command_adapter, freeze_spec, score_arena
from .doctor import doctor
from .regression import validate_corpus
from .review import validate_reviews
from .semantic import reconcile
from .skill_audit import validate_three_passes
from .taskpack import fresh_builder_simulation, validate_taskpack
from .verifier_handoff import build_handoff, validate_handoff
from .common import PACKAGE_ROOT, VERSION, TeleiosisError, redact, write_json_stdout
from .installer import install, rollback
from .integrity import verify_release
from .packaging import audit_zip, build_deterministic_zip, generate_manifest
from .workflow import contract, create_handoff, init_run, status_run, submit_stage, validate_run


class JsonParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise TeleiosisError("ARGUMENT_ERROR", "命令参数不合法。", {"reason": message})


def _parser() -> JsonParser:
    parser = JsonParser(prog="teleiosis", add_help=True)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check")
    verify = sub.add_parser("verify-self")
    verify.add_argument("--strict", action="store_true")
    test = sub.add_parser("self-test")
    test.add_argument("--timeout", type=int, default=600)
    sub.add_parser("contract")
    sub.add_parser("doctor")
    sub.add_parser("skill-audit")
    sub.add_parser("review")
    sub.add_parser("regression")

    semantic = sub.add_parser("semantic-reconcile")
    semantic.add_argument("--repository", type=Path, required=True)
    semantic.add_argument("--spec", type=Path, required=True)
    semantic.add_argument("--output", type=Path)

    taskpack = sub.add_parser("taskpack")
    taskpack_sub = taskpack.add_subparsers(dest="taskpack_command", required=True)
    taskpack_sub.add_parser("validate")
    taskpack_sub.add_parser("fresh-builder")

    verifier_handoff = sub.add_parser("verifier-handoff")
    verifier_sub = verifier_handoff.add_subparsers(dest="verifier_handoff_command", required=True)
    verifier_build = verifier_sub.add_parser("build")
    verifier_build.add_argument("--output", type=Path, required=True)
    verifier_validate = verifier_sub.add_parser("validate")
    verifier_validate.add_argument("--zip", type=Path, required=True)

    init = sub.add_parser("init")
    init.add_argument("--subject", type=Path, required=True)
    init.add_argument("--workspace", type=Path, required=True)
    init.add_argument("--run-id")

    nxt = sub.add_parser("next")
    nxt.add_argument("--workspace", type=Path, required=True)
    nxt.add_argument("--result", type=Path, required=True)

    status = sub.add_parser("status")
    status.add_argument("--workspace", type=Path, required=True)

    validate = sub.add_parser("validate-run")
    validate.add_argument("--workspace", type=Path, required=True)
    validate.add_argument("--require-complete", action="store_true")

    handoff = sub.add_parser("handoff")
    handoff.add_argument("--workspace", type=Path, required=True)
    handoff.add_argument("--output", type=Path, required=True)

    capabilities = sub.add_parser("capabilities")
    capabilities.add_argument("--module", choices=["T", "S", "P", "A"], required=True)

    arena = sub.add_parser("arena")
    arena_sub = arena.add_subparsers(dest="arena_command", required=True)
    freeze = arena_sub.add_parser("freeze")
    freeze.add_argument("--spec", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    freeze.add_argument("--frozen-at")
    score = arena_sub.add_parser("score")
    score.add_argument("--spec", type=Path, required=True)
    score.add_argument("--observations", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--markdown", type=Path)
    execute = arena_sub.add_parser("execute")
    execute.add_argument("--spec", type=Path, required=True)
    execute.add_argument("--participant", required=True)
    execute.add_argument("--input", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--receipt", type=Path, required=True)

    install_parser = sub.add_parser("install")
    install_parser.add_argument("--skills-root", type=Path)
    install_parser.add_argument("--project", action="store_true")
    install_parser.add_argument("--dry-run", action="store_true")

    rollback_parser = sub.add_parser("rollback-install")
    rollback_parser.add_argument("--receipt", type=Path, required=True)

    package = sub.add_parser("package")
    package.add_argument("--output", type=Path, required=True)
    audit = sub.add_parser("audit-zip")
    audit.add_argument("--zip", type=Path, required=True)
    return parser


def _run_self_tests(timeout: int) -> Dict[str, Any]:
    if timeout < 1 or timeout > 3600:
        raise TeleiosisError("TEST_TIMEOUT", "self-test timeout 必须在 1—3600 秒。")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-m", "unittest", "discover", "-s", str(PACKAGE_ROOT / "tests"), "-p", "test_*.py", "-v"]
    try:
        completed = subprocess.run(command, cwd=str(PACKAGE_ROOT), env=env, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise TeleiosisError("SELF_TEST_TIMEOUT", "自测超时。", {"timeout": timeout})
    stdout = completed.stdout[-65536:]
    stderr = completed.stderr[-65536:]
    if completed.returncode != 0:
        raise TeleiosisError("SELF_TEST_FAILED", "自测失败。", {"returncode": completed.returncode, "stdout_tail": stdout, "stderr_tail": stderr})
    return {"status": "PASS", "command": command, "returncode": completed.returncode, "stdout_tail": stdout, "stderr_tail": stderr}


def _capability_path(module: str) -> Path:
    mapping = {
        "T": "modules/raw_teleiosis/CAPABILITIES.json",
        "S": "modules/skill_market_lab/CAPABILITIES.json",
        "P": "modules/product_reality_lab/CAPABILITIES.json",
        "A": "modules/arena_lab/CAPABILITIES.json",
    }
    return PACKAGE_ROOT / mapping[module]


def dispatch(args: argparse.Namespace) -> Dict[str, Any]:
    command = args.command
    if command in {"check", "verify-self"}:
        result = verify_release(PACKAGE_ROOT, strict=True if command == "check" else bool(args.strict))
        if command == "check":
            result["install_command"] = "python3 START_HERE.py install"
            result["message_zh"] = "当前包完整，可直接安装。"
        return result
    if command == "self-test":
        return _run_self_tests(args.timeout)
    if command == "contract":
        return contract()
    if command == "doctor":
        return doctor(PACKAGE_ROOT)
    if command == "skill-audit":
        return validate_three_passes(PACKAGE_ROOT)
    if command == "review":
        return validate_reviews(PACKAGE_ROOT)
    if command == "regression":
        return validate_corpus(PACKAGE_ROOT / "fixtures/regression/teleiosis-v5-regression.jsonl")
    if command == "semantic-reconcile":
        return reconcile(args.repository, args.spec, args.output)
    if command == "taskpack":
        if args.taskpack_command == "validate":
            return validate_taskpack(PACKAGE_ROOT)
        if args.taskpack_command == "fresh-builder":
            return fresh_builder_simulation(PACKAGE_ROOT)
    if command == "verifier-handoff":
        if args.verifier_handoff_command == "build":
            return build_handoff(args.output, PACKAGE_ROOT)
        if args.verifier_handoff_command == "validate":
            return validate_handoff(args.zip)
    if command == "init":
        return init_run(args.subject, args.workspace, args.run_id)
    if command == "next":
        return submit_stage(args.workspace, args.result)
    if command == "status":
        return status_run(args.workspace)
    if command == "validate-run":
        return validate_run(args.workspace, require_complete=args.require_complete)
    if command == "handoff":
        return create_handoff(args.workspace, args.output)
    if command == "capabilities":
        return json.loads(_capability_path(args.module).read_text(encoding="utf-8"))
    if command == "arena":
        if args.arena_command == "freeze":
            return freeze_spec(args.spec, args.output, args.frozen_at)
        if args.arena_command == "score":
            return score_arena(args.spec, args.observations, args.output, args.markdown)
        if args.arena_command == "execute":
            return execute_command_adapter(args.spec, args.participant, args.input, args.output, args.receipt)
    if command == "install":
        return install(skills_root=args.skills_root, project=args.project, dry_run=args.dry_run, source=PACKAGE_ROOT)
    if command == "rollback-install":
        return rollback(args.receipt)
    if command == "package":
        generate_manifest(PACKAGE_ROOT)
        verify_release(PACKAGE_ROOT, strict=True)
        return build_deterministic_zip(PACKAGE_ROOT, args.output)
    if command == "audit-zip":
        return audit_zip(args.zip)
    raise TeleiosisError("COMMAND_UNKNOWN", "未知命令。", {"command": command})


def main(argv: Optional[List[str]] = None) -> int:
    try:
        parser = _parser()
        args = parser.parse_args(argv)
        result = dispatch(args)
        write_json_stdout({"ok": True, "version": VERSION, "result": result})
        return 0
    except TeleiosisError as exc:
        write_json_stdout({"ok": False, "version": VERSION, **exc.as_dict()})
        return 2
    except KeyboardInterrupt:
        write_json_stdout({"ok": False, "version": VERSION, "status": "ERROR", "error": {"code": "INTERRUPTED", "message": "用户中断。", "details": {}}})
        return 130
    except Exception as exc:
        # Never emit traceback or unredacted environment in machine mode.
        write_json_stdout({"ok": False, "version": VERSION, "status": "ERROR", "error": {"code": "INTERNAL_ERROR", "message": "内部错误。", "details": {"type": type(exc).__name__, "message": str(exc)}}})
        return 3
