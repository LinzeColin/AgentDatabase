#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from wbi_cycle.core import (  # noqa: E402
    CycleError,
    commit_mutation,
    initialize_workspace,
    load_state,
    record_subrun,
    tree_sha256,
    validate_workspace,
    workspace_lock,
)


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def cmd_digest(args):
    emit({"path": str(Path(args.path).resolve()), "tree_sha256": tree_sha256(Path(args.path))})


def cmd_init(args):
    workspace = Path(args.workspace)
    with workspace_lock(workspace):
        value = initialize_workspace(
            workspace,
            args.subject_name,
            args.subject_version,
            args.subject_digest,
            force=args.force,
        )
    emit(value)


def cmd_record(args):
    workspace = Path(args.workspace)
    with workspace_lock(workspace):
        value = record_subrun(
            workspace,
            stage=args.stage,
            round_number=args.round,
            subject_digest=args.subject_digest,
            evidence_digest=args.evidence_digest,
            outcome=args.outcome,
            staged_candidate_digest=args.staged_candidate_digest,
            notes=args.notes,
        )
    emit(value)


def cmd_commit(args):
    workspace = Path(args.workspace)
    with workspace_lock(workspace):
        value = commit_mutation(workspace, args.stage, Path(args.artifact))
    emit(value)


def cmd_validate(args):
    value = validate_workspace(Path(args.workspace), require_complete=args.require_complete)
    emit(value)
    if not value["valid"]:
        raise CycleError("宏循环验证失败")


def cmd_status(args):
    workspace = Path(args.workspace)
    emit({"state": load_state(workspace), "validation": validate_workspace(workspace)})


def build_parser():
    parser = argparse.ArgumentParser(
        prog="teleiosis_cycle.py",
        description="Teleiosis v0.0.0.2：固定五段调用、每次连续三轮、批准哈希后原子提交。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    item = sub.add_parser("digest", help="计算候选目录规范树哈希")
    item.add_argument("--path", required=True)
    item.set_defaults(func=cmd_digest)

    item = sub.add_parser("init", help="初始化一轮 Teleiosis 宏循环")
    item.add_argument("--workspace", required=True)
    item.add_argument("--subject-name", required=True)
    item.add_argument("--subject-version", required=True)
    item.add_argument("--subject-digest", required=True)
    item.add_argument("--force", action="store_true")
    item.set_defaults(func=cmd_init)

    item = sub.add_parser("record-subrun", help="按唯一顺序记录一次连续子轮")
    item.add_argument("--workspace", required=True)
    item.add_argument("--stage", choices=["T1", "M1", "T2", "M2", "T3"], required=True)
    item.add_argument("--round", type=int, choices=[1, 2, 3], required=True)
    item.add_argument("--subject-digest", required=True)
    item.add_argument("--evidence-digest", required=True)
    item.add_argument("--outcome", required=True)
    item.add_argument("--staged-candidate-digest")
    item.add_argument("--notes", default="")
    item.set_defaults(func=cmd_record)

    item = sub.add_parser("commit-mutation", help="原子提交第三轮已批准的 Candidate；禁止再改内容")
    item.add_argument("--workspace", required=True)
    item.add_argument("--stage", choices=["T1", "M1", "T2", "M2", "T3"], required=True)
    item.add_argument("--artifact", required=True)
    item.set_defaults(func=cmd_commit)

    item = sub.add_parser("validate", help="复验事件哈希链、调用顺序和三轮合同")
    item.add_argument("--workspace", required=True)
    item.add_argument("--require-complete", action="store_true")
    item.set_defaults(func=cmd_validate)

    item = sub.add_parser("status", help="查看状态及账本投影")
    item.add_argument("--workspace", required=True)
    item.set_defaults(func=cmd_status)
    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
        return 0
    except CycleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ERROR: 用户中断；不将部分运行标记为完成。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
