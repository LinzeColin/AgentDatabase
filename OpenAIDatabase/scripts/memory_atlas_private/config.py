from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


class ConfigurationError(ValueError):
    pass


def _required(env: dict[str, str], key: str) -> str:
    value = env.get(key, "").strip()
    if not value:
        raise ConfigurationError(f"缺少必需环境变量：{key}")
    return value


def _safe_prefix(value: str, *, key: str) -> str:
    normalized = value.strip().strip("/")
    if not normalized or normalized in {".", ".."}:
        raise ConfigurationError(f"{key} 必须是非空、专用对象前缀")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ConfigurationError(f"{key} 包含不安全路径段")
    return normalized + "/"


def _https_endpoint(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ConfigurationError("MEMORY_ATLAS_R2_ENDPOINT 必须是完整 HTTPS endpoint")
    return value.rstrip("/")


@dataclass(frozen=True)
class RuntimeConfig:
    r2_endpoint: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket: str
    r2_primary_prefix: str
    r2_backup_prefix: str
    private_db_client: Path
    runtime_dir: Path
    work_dir: Path
    web_data_dir: Path
    source_registry: Path
    public_atlas_snapshot: Path | None
    external_origin: str
    source_host_id: str
    failure_asset_registry: Path | None = None
    status_projection_target: Path | None = None
    github_repo: str = "LinzeColin/Private-Database"
    private_area: str = "Private-AgentDatabase"
    private_release_backup_enabled: bool = False
    private_release_policy: Path | None = None
    public_release_policy: Path | None = None

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "RuntimeConfig":
        values = dict(os.environ if env is None else env)
        bucket = _required(values, "MEMORY_ATLAS_R2_BUCKET")
        if "/" in bucket or bucket in {"memory-atlas-private", "default"}:
            raise ConfigurationError(
                "MEMORY_ATLAS_R2_BUCKET 必须来自受保护环境的精确既有 Bucket；"
                "禁止使用候选默认名或自动创建新 Bucket"
            )
        private_prefix = _safe_prefix(
            _required(values, "MEMORY_ATLAS_R2_PRIMARY_PREFIX"),
            key="MEMORY_ATLAS_R2_PRIMARY_PREFIX",
        )
        backup_prefix = _safe_prefix(
            _required(values, "MEMORY_ATLAS_R2_BACKUP_PREFIX"),
            key="MEMORY_ATLAS_R2_BACKUP_PREFIX",
        )
        if private_prefix == backup_prefix:
            raise ConfigurationError("primary-objects 与 backups/private-database 必须使用不同前缀")
        if not private_prefix.startswith("primary-objects/"):
            raise ConfigurationError("对象字节前缀必须位于 primary-objects/")
        if not backup_prefix.startswith("backups/private-database/"):
            raise ConfigurationError("Private-Database 快照前缀必须位于 backups/private-database/")
        client = Path(_required(values, "MEMORY_ATLAS_PRIVATE_DB_CLIENT")).expanduser()
        registry = Path(_required(values, "MEMORY_ATLAS_SOURCE_REGISTRY")).expanduser()
        if not client.is_file():
            raise ConfigurationError(f"Private-Database client 不存在：{client}")
        if not registry.is_file():
            raise ConfigurationError(f"来源注册表不存在：{registry}")
        try:
            payload = json.loads(registry.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError(f"来源注册表不可解析：{exc}") from exc
        if payload.get("schema_version") != "memory_atlas.source_registry.v1":
            raise ConfigurationError("来源注册表 schema_version 不匹配")
        origin = _required(values, "MEMORY_ATLAS_EXTERNAL_ORIGIN").rstrip("/")
        parsed_origin = urlparse(origin)
        if parsed_origin.scheme != "https" or not parsed_origin.netloc:
            raise ConfigurationError("MEMORY_ATLAS_EXTERNAL_ORIGIN 必须是生产 HTTPS origin")
        public_snapshot_raw = values.get("MEMORY_ATLAS_PUBLIC_SNAPSHOT", "").strip()
        public_snapshot = Path(public_snapshot_raw).expanduser() if public_snapshot_raw else None
        failure_registry_raw = values.get("MEMORY_ATLAS_FAILURE_ASSET_REGISTRY", "").strip()
        failure_registry = Path(failure_registry_raw).expanduser() if failure_registry_raw else None
        if failure_registry is not None:
            if failure_registry.is_symlink() or not failure_registry.is_file():
                raise ConfigurationError(
                    "MEMORY_ATLAS_FAILURE_ASSET_REGISTRY 必须是既有受保护普通文件"
                )
        status_target_raw = values.get("MEMORY_ATLAS_STATUS_PROJECTION_TARGET", "").strip()
        status_target = Path(status_target_raw).expanduser() if status_target_raw else None
        if status_target is not None:
            if not status_target.is_absolute():
                raise ConfigurationError("MEMORY_ATLAS_STATUS_PROJECTION_TARGET 必须是绝对路径")
            if (
                status_target.is_symlink()
                or status_target.parent.is_symlink()
                or not status_target.parent.is_dir()
            ):
                raise ConfigurationError(
                    "MEMORY_ATLAS_STATUS_PROJECTION_TARGET 必须位于既有非符号链接目录"
                )
        private_release_enabled = values.get(
            "MEMORY_ATLAS_PRIVATE_RELEASE_BACKUP_ENABLED", ""
        ).strip().lower() in {"1", "true", "yes"}
        private_release_policy_raw = values.get(
            "MEMORY_ATLAS_PRIVATE_RELEASE_POLICY", ""
        ).strip()
        public_release_policy_raw = values.get(
            "MEMORY_ATLAS_PUBLIC_RELEASE_POLICY", ""
        ).strip()
        private_release_policy = (
            Path(private_release_policy_raw).expanduser().resolve()
            if private_release_policy_raw
            else None
        )
        public_release_policy = (
            Path(public_release_policy_raw).expanduser().resolve()
            if public_release_policy_raw
            else None
        )
        if private_release_enabled and (
            private_release_policy is None
            or public_release_policy is None
            or not private_release_policy.is_file()
            or not public_release_policy.is_file()
        ):
            raise ConfigurationError("GitHub 私有 Release 备份策略文件缺失")
        return cls(
            r2_endpoint=_https_endpoint(_required(values, "MEMORY_ATLAS_R2_ENDPOINT")),
            r2_access_key_id=_required(values, "MEMORY_ATLAS_R2_ACCESS_KEY_ID"),
            r2_secret_access_key=_required(values, "MEMORY_ATLAS_R2_SECRET_ACCESS_KEY"),
            r2_bucket=bucket,
            r2_primary_prefix=private_prefix,
            r2_backup_prefix=backup_prefix,
            private_db_client=client.resolve(),
            runtime_dir=Path(_required(values, "MEMORY_ATLAS_RUNTIME_DIR")).expanduser().resolve(),
            work_dir=Path(_required(values, "MEMORY_ATLAS_WORK_DIR")).expanduser().resolve(),
            web_data_dir=Path(_required(values, "MEMORY_ATLAS_WEB_DATA_DIR")).expanduser().resolve(),
            source_registry=registry.resolve(),
            public_atlas_snapshot=public_snapshot.resolve() if public_snapshot else None,
            external_origin=origin,
            source_host_id=_required(values, "MEMORY_ATLAS_SOURCE_HOST_ID"),
            failure_asset_registry=failure_registry.resolve() if failure_registry else None,
            status_projection_target=status_target.resolve() if status_target else None,
            private_release_backup_enabled=private_release_enabled,
            private_release_policy=private_release_policy,
            public_release_policy=public_release_policy,
        )

    def ensure_runtime_dirs(self) -> None:
        for directory in (self.runtime_dir, self.work_dir, self.web_data_dir):
            directory.mkdir(parents=True, exist_ok=True)
            if directory.is_symlink():
                raise ConfigurationError(f"运行目录不能是符号链接：{directory}")
