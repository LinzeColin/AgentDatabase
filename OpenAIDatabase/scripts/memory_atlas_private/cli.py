from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .config import ConfigurationError, RuntimeConfig
from .object_store import R2ObjectStore
from .pipeline import CapturePipeline, RemoteReconcilePipeline
from .private_db import GhPrivateDatabase
from .restore import isolated_restore
from .fact_backup import backup_private_facts


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str))


def _config() -> RuntimeConfig:
    return RuntimeConfig.from_env()


def cmd_preflight(_: argparse.Namespace) -> None:
    config = _config()
    config.ensure_runtime_dirs()
    object_store = R2ObjectStore(config)
    private_db = GhPrivateDatabase(config.private_db_client)
    _print({
        "schema_version": "memory_atlas.preflight.v1",
        "r2": object_store.preflight(),
        "private_database": private_db.verify(),
        "bucket_creation_attempted": False,
        "source_registry": str(config.source_registry),
        "state": "PASS",
    })


def cmd_capture(_: argparse.Namespace) -> None:
    _print(CapturePipeline(_config()).run())


def cmd_reconcile(_: argparse.Namespace) -> None:
    _print(RemoteReconcilePipeline(_config()).run())


def cmd_status(_: argparse.Namespace) -> None:
    config = _config()
    path = config.web_data_dir / "memory_atlas_private_analytics.json"
    if not path.is_file():
        _print({"state": "UNKNOWN", "message_zh": "尚无私有分析快照。"})
        return
    _print(json.loads(path.read_text(encoding="utf-8")))


def cmd_restore(args: argparse.Namespace) -> None:
    config = _config()
    destination = args.destination.resolve()
    if destination == Path("/") or destination == Path.home().resolve():
        raise SystemExit("拒绝把根目录或用户目录作为隔离恢复目标")
    receipt = isolated_restore(
        manifest_path=args.manifest_path,
        destination=destination,
        object_store=R2ObjectStore(config),
        private_db=GhPrivateDatabase(config.private_db_client),
    )
    _print(receipt)



def cmd_backup_facts(_: argparse.Namespace) -> None:
    config = _config()
    from .pipeline import utc_now
    _print(backup_private_facts(
        config,
        GhPrivateDatabase(config.private_db_client),
        R2ObjectStore(config),
        generated_at=utc_now(),
    ))


def cmd_doctor(_: argparse.Namespace) -> None:
    config = _config()
    checks = {
        "python": sys.version.split()[0],
        "gh": shutil.which("gh"),
        "private_db_client": str(config.private_db_client),
        "source_registry": str(config.source_registry),
        "runtime_dir": str(config.runtime_dir),
        "web_data_dir": str(config.web_data_dir),
        "external_origin": config.external_origin,
        "r2_bucket_bound": bool(config.r2_bucket),
        "r2_primary_prefix": config.r2_primary_prefix,
        "r2_backup_prefix": config.r2_backup_prefix,
        "bucket_creation_allowed": False,
    }
    checks["state"] = "PASS" if checks["gh"] else "BLOCKED"
    _print(checks)
    if checks["state"] != "PASS":
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Memory Atlas v0.0.0.31 private data spine")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight").set_defaults(func=cmd_preflight)
    sub.add_parser("capture").set_defaults(func=cmd_capture)
    sub.add_parser("reconcile").set_defaults(func=cmd_reconcile)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("backup-facts").set_defaults(func=cmd_backup_facts)
    restore = sub.add_parser("restore-drill")
    restore.add_argument("--manifest-path", required=True)
    restore.add_argument("--destination", type=Path, required=True)
    restore.set_defaults(func=cmd_restore)
    sub.add_parser("doctor").set_defaults(func=cmd_doctor)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ConfigurationError as exc:
        _print({"state": "BLOCKED", "message_zh": str(exc)})
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
