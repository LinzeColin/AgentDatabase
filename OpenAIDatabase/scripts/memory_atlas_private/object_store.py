from __future__ import annotations

import json
import os
import random
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import RuntimeConfig
from .hashing import sha256_file
from .models import ObjectReceipt


class ObjectStoreError(RuntimeError):
    pass


class ObjectStore(Protocol):
    def preflight(self) -> dict[str, object]: ...
    def put_file(self, key: str, path: Path, expected_sha256: str) -> ObjectReceipt: ...
    def get_file(self, key: str, destination: Path) -> None: ...
    def exists_with_hash(self, key: str, expected_sha256: str) -> bool: ...


@dataclass
class LocalObjectStore:
    root: Path
    provider_version: str = "local-test-v1"

    def _target(self, key: str) -> Path:
        target = (self.root / key).resolve()
        target.relative_to(self.root.resolve())
        return target

    def preflight(self) -> dict[str, object]:
        self.root.mkdir(parents=True, exist_ok=True)
        sentinel = self._target("preflight/sentinel.json")
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        payload = b'{"memory_atlas":"preflight"}\n'
        sentinel.write_bytes(payload)
        observed = sentinel.read_bytes()
        sentinel.unlink()
        return {"state": "PASS", "readback_equal": observed == payload, "bucket_creation_attempted": False}

    def put_file(self, key: str, path: Path, expected_sha256: str) -> ObjectReceipt:
        if sha256_file(path) != expected_sha256:
            raise ObjectStoreError(f"源文件哈希与清单不一致：{path}")
        target = self._target(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        operation = "unchanged"
        if target.exists():
            current = sha256_file(target)
            if current != expected_sha256:
                operation = "repaired"
                temporary = target.with_suffix(target.suffix + ".partial")
                shutil.copyfile(path, temporary)
                temporary.replace(target)
        else:
            operation = "created"
            temporary = target.with_suffix(target.suffix + ".partial")
            shutil.copyfile(path, temporary)
            temporary.replace(target)
        readback = sha256_file(target)
        if readback != expected_sha256:
            raise ObjectStoreError(f"对象读回哈希不一致：{key}")
        return ObjectReceipt(
            sha256=expected_sha256,
            object_key=key,
            size_bytes=path.stat().st_size,
            operation=operation,
            readback_sha256=readback,
            readback_verified=True,
            provider_version=self.provider_version,
        )

    def get_file(self, key: str, destination: Path) -> None:
        source = self._target(key)
        if not source.is_file():
            raise ObjectStoreError(f"对象不存在：{key}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    def exists_with_hash(self, key: str, expected_sha256: str) -> bool:
        target = self._target(key)
        return target.is_file() and sha256_file(target) == expected_sha256


class R2ObjectStore:
    """Exact-scope Cloudflare R2 adapter using the mature boto3 S3 client.

    It never creates a bucket. Every newly created or repaired object is downloaded
    to a temporary file and hashed before the receipt can be positive.
    """

    def __init__(self, config: RuntimeConfig):
        try:
            import boto3
            from boto3.s3.transfer import TransferConfig
            from botocore.config import Config
        except ImportError as exc:
            raise ObjectStoreError("缺少 boto3；安装 requirements-memory-atlas-private.txt") from exc
        self.config = config
        self._transfer_config = TransferConfig(
            multipart_threshold=96 * 1024 * 1024,
            multipart_chunksize=32 * 1024 * 1024,
            max_concurrency=3,
            use_threads=True,
        )
        self.client = boto3.client(
            "s3",
            endpoint_url=config.r2_endpoint,
            aws_access_key_id=config.r2_access_key_id,
            aws_secret_access_key=config.r2_secret_access_key,
            region_name="auto",
            config=Config(
                retries={"max_attempts": 6, "mode": "adaptive"},
                connect_timeout=10,
                read_timeout=120,
                signature_version="s3v4",
            ),
        )

    def _full_key(self, key: str) -> str:
        clean = key.strip("/")
        if not clean or ".." in clean.split("/"):
            raise ObjectStoreError("对象 key 不安全")
        return self.config.r2_primary_prefix + clean

    def preflight(self) -> dict[str, object]:
        # Bucket creation is intentionally absent from this adapter.
        self.client.head_bucket(Bucket=self.config.r2_bucket)
        nonce = f"preflight/sentinel-{os.getpid()}-{random.randint(100000, 999999)}.json"
        key = self._full_key(nonce)
        payload = json.dumps({"schema_version": "memory_atlas.r2_preflight.v1"}, sort_keys=True).encode()
        try:
            self.client.put_object(
                Bucket=self.config.r2_bucket,
                Key=key,
                Body=payload,
                Metadata={"sha256": __import__("hashlib").sha256(payload).hexdigest()},
                ContentType="application/json",
            )
            observed = self.client.get_object(Bucket=self.config.r2_bucket, Key=key)["Body"].read()
            if observed != payload:
                raise ObjectStoreError("R2 preflight 逐字节读回不一致")
        finally:
            try:
                self.client.delete_object(Bucket=self.config.r2_bucket, Key=key)
            except Exception:
                pass
        return {
            "state": "PASS",
            "bucket": self.config.r2_bucket,
            "prefix": self.config.r2_primary_prefix,
            "readback_equal": True,
            "bucket_creation_attempted": False,
        }

    def _head(self, full_key: str) -> dict[str, object] | None:
        try:
            return self.client.head_object(Bucket=self.config.r2_bucket, Key=full_key)
        except Exception as exc:
            response = getattr(exc, "response", {})
            status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            code = response.get("Error", {}).get("Code")
            if status == 404 or code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise

    def _download_and_hash(self, full_key: str) -> str:
        with tempfile.NamedTemporaryFile(prefix="memory-atlas-r2-readback-", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            with temporary.open("wb") as output:
                self.client.download_fileobj(
                    self.config.r2_bucket,
                    full_key,
                    output,
                    Config=self._transfer_config,
                )
            return sha256_file(temporary)
        finally:
            temporary.unlink(missing_ok=True)

    def put_file(self, key: str, path: Path, expected_sha256: str) -> ObjectReceipt:
        observed_source = sha256_file(path)
        if observed_source != expected_sha256:
            raise ObjectStoreError(f"源文件哈希与清单不一致：{path}")
        full_key = self._full_key(key)
        head = self._head(full_key)
        operation = "unchanged"
        remote_meta_sha = str((head or {}).get("Metadata", {}).get("sha256", ""))
        if head is None or remote_meta_sha != expected_sha256:
            operation = "created" if head is None else "repaired"
            last_error: Exception | None = None
            for attempt in range(5):
                try:
                    with path.open("rb") as stream:
                        self.client.upload_fileobj(
                            stream,
                            self.config.r2_bucket,
                            full_key,
                            ExtraArgs={
                                "Metadata": {"sha256": expected_sha256},
                                "ContentType": "application/octet-stream",
                            },
                            Config=self._transfer_config,
                        )
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt == 4:
                        break
                    time.sleep(min(2 ** attempt, 8))
            if last_error:
                raise ObjectStoreError(f"R2 上传失败：{full_key}: {last_error}") from last_error
        readback = self._download_and_hash(full_key)
        if readback != expected_sha256:
            raise ObjectStoreError(f"R2 完整读回哈希不一致：{full_key}")
        return ObjectReceipt(
            sha256=expected_sha256,
            object_key=full_key,
            size_bytes=path.stat().st_size,
            operation=operation,
            readback_sha256=readback,
            readback_verified=True,
            provider_version="cloudflare-r2-s3-v1",
        )

    def get_file(self, key: str, destination: Path) -> None:
        full_key = key if key.startswith(self.config.r2_primary_prefix) else self._full_key(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            self.client.download_fileobj(
                self.config.r2_bucket,
                full_key,
                output,
                Config=self._transfer_config,
            )

    def exists_with_hash(self, key: str, expected_sha256: str) -> bool:
        full_key = key if key.startswith(self.config.r2_primary_prefix) else self._full_key(key)
        head = self._head(full_key)
        if not head or head.get("Metadata", {}).get("sha256") != expected_sha256:
            return False
        return self._download_and_hash(full_key) == expected_sha256
