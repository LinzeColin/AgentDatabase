#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


ALIASES = {
    "endpoint": ("MEMORY_ATLAS_R2_ENDPOINT", "R2_ENDPOINT", "CLOUDFLARE_R2_ENDPOINT", "AWS_ENDPOINT_URL_S3", "WRP_R2_ENDPOINT"),
    "access_key": ("MEMORY_ATLAS_R2_ACCESS_KEY_ID", "R2_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID", "WRP_R2_ACCESS_KEY_ID"),
    "secret_key": ("MEMORY_ATLAS_R2_SECRET_ACCESS_KEY", "R2_SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY", "WRP_R2_SECRET_ACCESS_KEY"),
    "bucket": ("MEMORY_ATLAS_R2_BUCKET", "R2_BUCKET", "BUCKET", "BUCKET_NAME", "WRP_R2_BUCKET"),
}


@dataclass(frozen=True)
class Candidate:
    source: Path
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str


class BootstrapError(RuntimeError):
    pass


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="strict").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def first(values: dict[str, str], aliases: tuple[str, ...]) -> str:
    return next((values[name].strip() for name in aliases if values.get(name, "").strip()), "")


def read_secret_file(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = path.expanduser().resolve(strict=True)
    if path.expanduser().is_symlink() or not resolved.is_file():
        raise BootstrapError("GitHub token 槽位必须是受保护的普通文件")
    if stat.S_IMODE(resolved.stat().st_mode) != 0o600:
        raise BootstrapError("GitHub token 槽位权限必须精确为 0600")
    value = resolved.read_text(encoding="utf-8", errors="strict").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,255}", value):
        raise BootstrapError("GitHub token 槽位为空或格式无效")
    return value


def discover_candidates(protected_root: Path) -> list[Candidate]:
    explicit = protected_root / "memory_atlas.env"
    paths: list[Path] = [explicit] if explicit.is_file() else []
    paths.extend(
        path for path in sorted(protected_root.glob("*.env"))
        if path != explicit and any(term in path.name.lower() for term in ("r2", "platform", "storage"))
    )
    candidates: list[Candidate] = []
    for path in paths:
        values = parse_env(path)
        endpoint = first(values, ALIASES["endpoint"])
        access = first(values, ALIASES["access_key"])
        secret = first(values, ALIASES["secret_key"])
        bucket = first(values, ALIASES["bucket"])
        if all((endpoint, access, secret, bucket)):
            candidates.append(Candidate(path, endpoint.rstrip("/"), access, secret, bucket))
    return candidates


def validate_candidate(candidate: Candidate, primary_prefix: str) -> dict[str, object]:
    try:
        import boto3
        from botocore.config import Config
    except ImportError as exc:
        raise BootstrapError("缺少 boto3；先安装任务包锁定依赖") from exc
    parsed = urlparse(candidate.endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        return {"state": "FAIL", "source": candidate.source.name, "reason": "endpoint_not_https"}
    client = boto3.client(
        "s3",
        endpoint_url=candidate.endpoint,
        aws_access_key_id=candidate.access_key,
        aws_secret_access_key=candidate.secret_key,
        region_name="auto",
        config=Config(retries={"max_attempts": 3, "mode": "standard"}, signature_version="s3v4"),
    )
    key = primary_prefix.strip("/") + "/preflight/bootstrap-sentinel.json"
    payload = b'{"memory_atlas":"bootstrap"}\n'
    try:
        client.head_bucket(Bucket=candidate.bucket)
        client.put_object(Bucket=candidate.bucket, Key=key, Body=payload, Metadata={"purpose": "memory-atlas-preflight"})
        observed = client.get_object(Bucket=candidate.bucket, Key=key)["Body"].read()
        if observed != payload:
            return {"state": "FAIL", "source": candidate.source.name, "reason": "readback_mismatch"}
    except Exception as exc:
        response = getattr(exc, "response", {})
        error = response.get("Error", {}) if isinstance(response, dict) else {}
        metadata = response.get("ResponseMetadata", {}) if isinstance(response, dict) else {}
        return {
            "state": "FAIL",
            "source": candidate.source.name,
            "reason": exc.__class__.__name__,
            "error_code": str(error.get("Code", "unknown"))[:80],
            "http_status": metadata.get("HTTPStatusCode"),
        }
    finally:
        try:
            client.delete_object(Bucket=candidate.bucket, Key=key)
        except Exception:
            pass
    return {"state": "PASS", "source": candidate.source.name, "bucket": candidate.bucket}


def write_output(
    candidate: Candidate,
    output: Path,
    primary_prefix: str,
    backup_prefix: str,
    external_origin: str,
    github_token: str = "",
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    github_line = f"GH_TOKEN={github_token}\n" if github_token else ""
    content = (
        f"MEMORY_ATLAS_R2_ENDPOINT={candidate.endpoint}\n"
        f"MEMORY_ATLAS_R2_ACCESS_KEY_ID={candidate.access_key}\n"
        f"MEMORY_ATLAS_R2_SECRET_ACCESS_KEY={candidate.secret_key}\n"
        f"MEMORY_ATLAS_R2_BUCKET={candidate.bucket}\n"
        f"MEMORY_ATLAS_R2_PRIMARY_PREFIX={primary_prefix.strip('/')}/\n"
        f"MEMORY_ATLAS_R2_BACKUP_PREFIX={backup_prefix.strip('/')}/\n"
        f"{github_line}"
        "MEMORY_ATLAS_PRIVATE_DB_CLIENT=/srv/linze/apps/agentdatabase/current/OpenAIDatabase/scripts/private_db_client.py\n"
        "MEMORY_ATLAS_SOURCE_REGISTRY=/srv/linze/apps/agentdatabase/current/ops/memory-atlas/source-registry.json\n"
        "MEMORY_ATLAS_RUNTIME_DIR=/srv/linze/state/memory-atlas\n"
        "MEMORY_ATLAS_WORK_DIR=/srv/linze/work/memory-atlas\n"
        "MEMORY_ATLAS_WEB_DATA_DIR=/srv/linze/apps/memory-atlas/shared/data\n"
        "MEMORY_ATLAS_PUBLIC_SNAPSHOT=/srv/linze/apps/memory-atlas/shared/public-baseline/memory_atlas.json\n"
        "MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS=/srv/linze/state/memory-atlas/evidence-adapters\n"
        "MEMORY_ATLAS_FAILURE_ASSET_REGISTRY=/srv/linze/secrets/memory-atlas-failure-assets.json\n"
        "MEMORY_ATLAS_STATUS_PROJECTION_TARGET=/srv/linze/apps/status/data/memory_atlas_status_projection.json\n"
        f"MEMORY_ATLAS_EXTERNAL_ORIGIN={external_origin.rstrip('/')}\n"
        "MEMORY_ATLAS_SOURCE_HOST_ID=mac-codex-source\n"
    )
    temporary = output.with_suffix(output.suffix + ".partial")
    temporary.write_text(content, encoding="utf-8")
    os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
    temporary.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve one exact existing R2 scope from owner-protected files")
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--primary-prefix", default="primary-objects/memory-atlas")
    parser.add_argument("--backup-prefix", default="backups/private-database/memory-atlas")
    parser.add_argument("--external-origin", default="https://memoryatlas.linzezhang.com")
    parser.add_argument("--github-token-file", type=Path)
    args = parser.parse_args()
    protected_root = args.protected_root.expanduser().resolve()
    if not protected_root.is_dir():
        raise SystemExit("受保护目录不存在")
    github_token = read_secret_file(args.github_token_file)
    candidates = discover_candidates(protected_root)
    results = [(candidate, validate_candidate(candidate, args.primary_prefix)) for candidate in candidates]
    passed = [(candidate, result) for candidate, result in results if result["state"] == "PASS"]
    if len(passed) != 1:
        safe_results = [result for _, result in results]
        print(json.dumps({
            "state": "BLOCKED",
            "message_zh": "必须从受保护环境唯一确定一个可写、可读回的既有 R2 Bucket；脚本不会建桶或猜测。",
            "candidate_results": safe_results,
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    candidate, result = passed[0]
    write_output(
        candidate,
        args.output.expanduser(),
        args.primary_prefix,
        args.backup_prefix,
        args.external_origin,
        github_token,
    )
    print(json.dumps({
        "state": "PASS",
        "source_file": candidate.source.name,
        "bucket": result["bucket"],
        "output": str(args.output.expanduser()),
        "output_mode": "0600",
        "bucket_created": False,
        "github_token_bound": bool(github_token),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
