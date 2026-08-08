"""Where the all-time event stream lives after the GitHub migration.

Until 2026-08-04 the canonical union of every normalized event lived in R2 and
the GitHub private repository held a cold copy. The bucket then approached its
storage cap — a real billing risk — so the memory-atlas primary tree moved to
the private repository and R2 was drained.

Nothing here assumes which side holds the bytes. It reads the release manifest,
downloads the asset, hashes it, and only a hash equal to the manifest's makes
the source usable: a truncated or substituted download is a hard error, never a
quietly smaller event stream. The 389 MB asset is cached by digest so a
fifteen-minute timer re-verifies rather than re-downloads.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .hashing import sha256_file
from .private_release import GithubReleaseClient

CANONICAL_TAG_PREFIX = "memory-atlas-canonical-"
MANIFEST_ASSET = "MANIFEST.json"
EVENTS_ASSET = "events.jsonl"
MANIFEST_SCHEMA = "memory_atlas.canonical_events_manifest.v1"
CANONICAL_RELEASE_RETENTION = 2


class CanonicalSourceError(RuntimeError):
    """Fail-closed error; never carries repository content or a token."""


def _resolve_gh() -> str:
    configured = os.environ.get("MEMORY_ATLAS_GH_PATH", "").strip()
    candidates = [configured] if configured else ["/usr/bin/gh", "/opt/homebrew/bin/gh", "/usr/local/bin/gh"]
    for raw in candidates:
        candidate = Path(raw).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise CanonicalSourceError("gh_unavailable")


@dataclass
class GitHubCanonicalSource:
    """Read the canonical event stream out of the private repository's releases."""

    repo: str = "LinzeColin/Private-Database"
    tag_prefix: str = CANONICAL_TAG_PREFIX
    gh_path: str | None = None
    timeout_seconds: int = 1800
    cache_dir: Path | None = None

    def _gh(self, args: list[str], *, timeout: int | None = None) -> str:
        command = [self.gh_path or _resolve_gh(), *args]
        try:
            completed = subprocess.run(
                command, text=True, capture_output=True, timeout=timeout or self.timeout_seconds
            )
        except subprocess.TimeoutExpired as exc:
            raise CanonicalSourceError(f"gh_timeout: {' '.join(args[:2])}") from exc
        if completed.returncode != 0:
            # stderr can name a repository and a tag; both are already known
            # here. It never carries the token, which gh reads from the env.
            raise CanonicalSourceError(
                f"gh_failed: {' '.join(args[:2])}: {(completed.stderr or completed.stdout).strip()[:300]}"
            )
        return completed.stdout

    def latest_tag(self) -> dict[str, Any] | None:
        """Newest published release whose tag carries the canonical prefix."""
        raw = self._gh(
            ["release", "list", "--repo", self.repo, "--limit", "60", "--json", "tagName,publishedAt,isDraft"],
            timeout=120,
        )
        try:
            rows = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CanonicalSourceError("gh_release_list_unparseable") from exc
        candidates = [
            row
            for row in rows
            if isinstance(row, Mapping)
            and not row.get("isDraft")
            and str(row.get("tagName", "")).startswith(self.tag_prefix)
        ]
        if not candidates:
            return None
        newest = max(candidates, key=lambda row: str(row.get("publishedAt", "")))
        return {"tag": str(newest["tagName"]), "published_at": str(newest.get("publishedAt", ""))}

    def release_assets(self, tag: str) -> list[dict[str, Any]] | None:
        """Assets on a release right now — None when the release is gone.

        A record saying a backup was made is not evidence the backup still
        exists. This is what turns the first into the second.
        """
        try:
            raw = self._gh(
                ["release", "view", tag, "--repo", self.repo, "--json", "assets,tagName"], timeout=120
            )
        except CanonicalSourceError:
            return None
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return None
        assets = value.get("assets")
        return [row for row in assets if isinstance(row, Mapping)] if isinstance(assets, list) else []

    def _download(self, tag: str, asset: str, destination: Path, *, timeout: int | None = None) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._gh(
            ["release", "download", tag, "--repo", self.repo, "--pattern", asset,
             "--output", str(destination), "--clobber"],
            timeout=timeout,
        )
        if not destination.is_file():
            raise CanonicalSourceError(f"asset_missing_after_download: {asset}")

    def manifest(self) -> dict[str, Any] | None:
        """The canonical manifest, or None when no canonical release exists."""
        release = self.latest_tag()
        if release is None:
            return None
        with tempfile.TemporaryDirectory(prefix="memory-atlas-canon-") as work:
            target = Path(work) / MANIFEST_ASSET
            self._download(release["tag"], MANIFEST_ASSET, target, timeout=180)
            try:
                value = json.loads(target.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CanonicalSourceError("canonical_manifest_unparseable") from exc
        if not isinstance(value, Mapping) or value.get("schema_version") != MANIFEST_SCHEMA:
            raise CanonicalSourceError("canonical_manifest_schema_mismatch")
        for key in ("object", "sha256", "bytes", "unique_events"):
            if value.get(key) in (None, ""):
                raise CanonicalSourceError(f"canonical_manifest_incomplete: {key}")
        out = dict(value)
        out["release_tag"] = release["tag"]
        out["release_published_at"] = release["published_at"]
        return out

    def fetch_events(self, manifest: Mapping[str, Any], destination: Path) -> dict[str, Any]:
        """Download `events.jsonl` and prove it is the object the manifest names.

        A cached copy under the same digest is re-hashed rather than trusted by
        name, so a corrupted cache is caught on the run that reads it, not on the
        run that wrote it.
        """
        expected = str(manifest["sha256"])
        expected_bytes = int(manifest["bytes"])
        cached = self._cached(expected)
        if cached is not None:
            _link_or_copy(cached, destination)
            return {
                "state": "READY", "provider": "github_private_release", "cache": "HIT",
                "sha256": expected, "bytes": expected_bytes,
                "release_tag": manifest.get("release_tag"),
            }
        self._download(str(manifest["release_tag"]), EVENTS_ASSET, destination)
        observed_bytes = destination.stat().st_size
        observed = sha256_file(destination)
        if observed != expected or observed_bytes != expected_bytes:
            destination.unlink(missing_ok=True)
            raise CanonicalSourceError(
                f"canonical_asset_mismatch: bytes {observed_bytes}/{expected_bytes}"
            )
        self._store_cache(destination, expected)
        return {
            "state": "READY", "provider": "github_private_release", "cache": "MISS",
            "sha256": expected, "bytes": expected_bytes,
            "release_tag": manifest.get("release_tag"),
        }

    def _cached(self, digest: str) -> Path | None:
        if self.cache_dir is None:
            return None
        candidate = self.cache_dir / f"{digest}.jsonl"
        if not candidate.is_file():
            return None
        if sha256_file(candidate) == digest:
            # Pruning belongs on this path too. When a new canonical release is
            # published the old digest stops being read but keeps its 389 MB,
            # and every subsequent run is a cache hit that never cleans up.
            self._prune_cache(keep=candidate.name)
            return candidate
        candidate.unlink(missing_ok=True)
        return None

    def _prune_cache(self, *, keep: str) -> None:
        """One digest at a time: the asset is 389 MB and the origin runs full."""
        if self.cache_dir is None:
            return
        try:
            for stale in self.cache_dir.glob("*.jsonl"):
                if stale.name != keep:
                    stale.unlink(missing_ok=True)
        except OSError:
            pass

    def _store_cache(self, source: Path, digest: str) -> None:
        if self.cache_dir is None:
            return
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            target = self.cache_dir / f"{digest}.jsonl"
            _link_or_copy(source, target)
            self._prune_cache(keep=target.name)
        except OSError:
            # A cache that cannot be written must not fail the run; the next run
            # pays the download again, which is slow but correct.
            pass


def _merge_event_files(current: Path, previous: Path) -> dict[str, int]:
    """Rewrite ``current`` as the event-id union of current then previous.

    The current batch wins for duplicate ids.  Invalid or id-less rows are not
    silently counted as recoverable events.
    """

    merged = current.with_suffix(current.suffix + ".merged")
    seen: set[str] = set()
    current_events = 0
    previous_only = 0
    with merged.open("w", encoding="utf-8", newline="\n") as output:
        for path, is_current in ((current, True), (previous, False)):
            with path.open("r", encoding="utf-8") as source:
                for line in source:
                    if not line.strip():
                        continue
                    try:
                        event_id = str(json.loads(line).get("event_id") or "")
                    except json.JSONDecodeError:
                        continue
                    if not event_id or event_id in seen:
                        continue
                    seen.add(event_id)
                    current_events += int(is_current)
                    previous_only += int(not is_current)
                    output.write(line if line.endswith("\n") else line + "\n")
    merged.replace(current)
    return {
        "current_events": current_events,
        "previous_only_events": previous_only,
        "unique_events": len(seen),
    }


def _count_unique_events(path: Path) -> int:
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            try:
                event_id = str(json.loads(line).get("event_id") or "")
            except json.JSONDecodeError:
                continue
            if event_id:
                seen.add(event_id)
    return len(seen)


@dataclass
class GitHubCanonicalPublisher:
    """Publish the current all-time event union without touching R2.

    A published release is accepted only after both assets are downloaded again
    and the event bytes match the declared digest.  The previous published
    release remains available until the new one passes and is published.
    """

    repo: str = "LinzeColin/Private-Database"
    source: GitHubCanonicalSource | None = None
    release_client: Any = None
    retention_count: int = CANONICAL_RELEASE_RETENTION

    def __post_init__(self) -> None:
        if self.source is None:
            self.source = GitHubCanonicalSource(repo=self.repo)
        if self.release_client is None:
            self.release_client = GithubReleaseClient(self.repo, _resolve_gh())

    def run(
        self,
        *,
        delta_path: Path,
        normalized_object_key: str,
        canonical_object_key: str,
        run_id: str,
        created_at: str,
        work_root: Path,
    ) -> dict[str, Any]:
        release_root = work_root / "github-canonical-release"
        release_root.mkdir(parents=True, exist_ok=False)
        result: dict[str, Any] | None = None
        try:
            self.release_client.assert_private_repository()
            events_path = release_root / EVENTS_ASSET
            shutil.copyfile(delta_path, events_path)
            previous_manifest = self.source.manifest() if self.source is not None else None
            supersedes: set[str] = {normalized_object_key}
            merge = {
                "current_events": _count_unique_events(events_path),
                "previous_only_events": 0,
                "unique_events": _count_unique_events(events_path),
            }
            if previous_manifest is not None:
                previous_events = release_root / "previous-events.jsonl"
                assert self.source is not None
                self.source.fetch_events(previous_manifest, previous_events)
                merge = _merge_event_files(events_path, previous_events)
                supersedes.update(
                    str(item)
                    for item in previous_manifest.get("supersedes", [])
                    if isinstance(item, str)
                )
                previous_object = str(previous_manifest.get("object") or "")
                if previous_object:
                    supersedes.add(previous_object)
                previous_events.unlink(missing_ok=True)

            digest = sha256_file(events_path)
            manifest = {
                "schema_version": MANIFEST_SCHEMA,
                "object": canonical_object_key,
                "sha256": digest,
                "bytes": events_path.stat().st_size,
                "unique_events": merge["unique_events"],
                "supersedes": sorted(supersedes),
                "source_run_id": run_id,
                "created_at": created_at,
                "storage_mode": "GITHUB_PRIVATE_RELEASE_ZERO_CHARGE",
            }
            manifest_path = release_root / MANIFEST_ASSET
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            timestamp = re.sub(r"[^0-9]", "", created_at)[:14]
            tag = f"{CANONICAL_TAG_PREFIX}{timestamp}-{run_id[-12:]}"
            self.release_client.create_draft(tag, f"Memory Atlas canonical events {timestamp}")
            self.release_client.upload(tag, [events_path, manifest_path])
            remote_dir = release_root / "remote-readback"
            remote_dir.mkdir()
            self.release_client.download(tag, remote_dir)
            remote_manifest = json.loads((remote_dir / MANIFEST_ASSET).read_text(encoding="utf-8"))
            remote_events = remote_dir / EVENTS_ASSET
            if remote_manifest != manifest or sha256_file(remote_events) != digest:
                raise CanonicalSourceError("canonical_publish_remote_readback_mismatch")
            release = self.release_client.view(tag)
            asset_names = {
                str(row.get("name") or "")
                for row in release.get("assets", [])
                if isinstance(row, Mapping)
            }
            if release.get("isDraft") is not True or asset_names != {MANIFEST_ASSET, EVENTS_ASSET}:
                raise CanonicalSourceError("canonical_publish_draft_assets_invalid")
            self.release_client.publish(tag)
            published = self.release_client.view(tag)
            if published.get("isDraft") is not False:
                raise CanonicalSourceError("canonical_publish_failed")
            deleted = self.release_client.enforce_retention(
                CANONICAL_TAG_PREFIX, self.retention_count
            )
            result = {
                "schema_version": "memory_atlas.github_canonical_backup.v1",
                "state": "PASS",
                "provider": "github_private_release",
                "object": canonical_object_key,
                "sha256": digest,
                "bytes": events_path.stat().st_size,
                "unique_events": merge["unique_events"],
                "release_tag": tag,
                "release_url": str(published.get("url") or ""),
                "remote_readback_verified": True,
                "supersedes": sorted(supersedes),
                "merge": merge,
                "retention_deleted_count": len(deleted),
                "billable_cloud_storage_requests": 0,
            }
        finally:
            shutil.rmtree(release_root, ignore_errors=False)
        if result is None:
            raise CanonicalSourceError("canonical_publish_incomplete")
        result["local_cleanup"] = {
            "state": "PASS" if not release_root.exists() else "FAIL",
            "remaining_paths": 0 if not release_root.exists() else 1,
        }
        return result


def _link_or_copy(source: Path, destination: Path) -> None:
    import shutil

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


@dataclass
class CanonicalResolution:
    """Which side holds the canonical union this run, and what proves it."""

    available: bool
    provider: str | None = None
    canonical_object: str | None = None
    sha256: str | None = None
    bytes: int | None = None
    unique_events: int | None = None
    release_tag: str | None = None
    release_published_at: str | None = None
    superseded: set[str] = field(default_factory=set)
    reason: str | None = None
    _fetch: Any = None

    def fetch(self, destination: Path) -> dict[str, Any]:
        if not self.available or self._fetch is None:
            raise CanonicalSourceError("canonical_source_unavailable")
        return self._fetch(destination)

    def covers(self, object_key: str) -> bool:
        """True when the canonical union provably contains that object's events."""
        return self.available and (object_key in self.superseded or object_key == self.canonical_object)

    def to_fact(self) -> dict[str, Any]:
        return {
            "state": "READY" if self.available else "UNAVAILABLE",
            "provider": self.provider,
            "canonical_object": self.canonical_object,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "unique_events": self.unique_events,
            "release_tag": self.release_tag,
            "release_published_at": self.release_published_at,
            "superseded_count": len(self.superseded),
            "reason": self.reason,
        }


@dataclass
class BackupCoverage:
    """Are this run's source bytes still archived in the private repository?

    R2 held a content-addressed store of every source file. The migration moved
    it to the encrypted per-run backup releases, which are 698 MB of ciphertext
    in eight shards — decrypting them every fifteen minutes to re-prove the
    bytes is not a real option. What is available, and what this checks, is the
    evidence written when the backup was made: the capture host restored the
    archive in isolation and every hash matched. That is a strictly weaker claim
    than a live byte read, so it is reported under its own state and never
    counted as a verified read-back.
    """

    state: str  # COVERED | INSUFFICIENT | ABSENT
    covered_object_count: int = 0
    manifest_object_count: int = 0
    restored_files: int = 0
    release_tag: str | None = None
    asset_count: int = 0
    expected_parts: int = 0
    reason: str | None = None

    @property
    def covered(self) -> bool:
        return self.state == "COVERED"

    def to_fact(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "covered_object_count": self.covered_object_count,
            "manifest_object_count": self.manifest_object_count,
            "restored_files": self.restored_files,
            "release_tag": self.release_tag,
            "asset_count": self.asset_count,
            "expected_parts": self.expected_parts,
            "verification_class": "ARCHIVE_RESTORE_PROOF_AT_BACKUP_TIME_NOT_LIVE_BYTE_READ",
            "reason": self.reason,
        }


def verify_backup_coverage(
    github: GitHubCanonicalSource | None,
    backup_record: Mapping[str, Any] | None,
    *,
    run_id: str,
    manifest_object_count: int,
    canonical_covered: int,
) -> BackupCoverage:
    """Coverage only when the record is this run's, passed, and still exists.

    The count has to add up. "A backup exists" must never excuse an arbitrary
    number of objects that vanished — that is the failure this whole path is
    supposed to be able to detect.
    """
    if not isinstance(backup_record, Mapping):
        return BackupCoverage(state="ABSENT", manifest_object_count=manifest_object_count,
                              reason="no_backup_record_in_manifest")
    if str(backup_record.get("backup_id") or "") != run_id:
        return BackupCoverage(state="ABSENT", manifest_object_count=manifest_object_count,
                              reason="backup_record_belongs_to_another_run")
    if str(backup_record.get("state") or "") != "PASS":
        return BackupCoverage(state="ABSENT", manifest_object_count=manifest_object_count,
                              reason=f"backup_state_{backup_record.get('state')}")
    restore = backup_record.get("isolated_restore")
    restore = restore if isinstance(restore, Mapping) else {}
    if str(restore.get("state") or "") != "PASS" or restore.get("all_hashes_match") is not True:
        return BackupCoverage(state="ABSENT", manifest_object_count=manifest_object_count,
                              reason="isolated_restore_did_not_prove_the_hashes")
    if backup_record.get("remote_readback_verified") is not True:
        return BackupCoverage(state="ABSENT", manifest_object_count=manifest_object_count,
                              reason="remote_readback_not_verified")

    restored_files = int(restore.get("restored_files") or 0)
    expected_parts = int(backup_record.get("ciphertext_part_count") or 0)
    tag = str(backup_record.get("release_tag") or "")
    coverage = BackupCoverage(
        state="INSUFFICIENT", manifest_object_count=manifest_object_count,
        restored_files=restored_files, release_tag=tag or None, expected_parts=expected_parts,
    )
    # The archive holds source files; the normalized event object is covered by
    # the canonical union instead. Together they must account for the manifest.
    coverage.covered_object_count = restored_files + canonical_covered
    if coverage.covered_object_count < manifest_object_count:
        coverage.reason = "archive_does_not_account_for_every_manifest_object"
        return coverage
    if not tag:
        coverage.reason = "backup_record_names_no_release"
        return coverage
    if github is None:
        coverage.reason = "no_github_client_to_confirm_the_release"
        return coverage

    assets = github.release_assets(tag)
    if assets is None:
        coverage.state = "ABSENT"
        coverage.reason = "backup_release_no_longer_exists"
        return coverage
    coverage.asset_count = len(assets)
    if expected_parts and coverage.asset_count < expected_parts:
        coverage.reason = "backup_release_is_missing_shards"
        return coverage
    coverage.state = "COVERED"
    return coverage


def resolve_canonical(
    *,
    object_store: Any,
    github: GitHubCanonicalSource | None,
    work_dir: Path,
    r2_manifest_loader: Any = None,
) -> CanonicalResolution:
    """Measure both sides and return the one that actually verifies.

    R2 first only because it is cheaper when it happens to hold the bytes. After
    the migration it holds none of them, and the GitHub release is the primary —
    but that is discovered by looking, not declared here.
    """
    r2_state: dict[str, Any] | None = None
    if r2_manifest_loader is not None and object_store is not None:
        try:
            r2_state = r2_manifest_loader(object_store, work_dir)
        except Exception:
            r2_state = None
    if r2_state and r2_state.get("available"):
        canonical_object = str(r2_state["canonical_object"])
        digest = str(r2_state["sha256"])
        try:
            present = object_store.exists_with_hash(canonical_object, digest)
        except Exception:
            present = False
        if present:
            def _fetch_r2(destination: Path) -> dict[str, Any]:
                object_store.get_file(canonical_object, destination)
                observed = sha256_file(destination)
                if observed != digest:
                    destination.unlink(missing_ok=True)
                    raise CanonicalSourceError("canonical_asset_mismatch: r2")
                return {"state": "READY", "provider": "r2", "cache": "MISS",
                        "sha256": digest, "bytes": destination.stat().st_size}

            return CanonicalResolution(
                available=True, provider="r2", canonical_object=canonical_object, sha256=digest,
                unique_events=r2_state.get("unique_events"),
                superseded=set(r2_state.get("superseded") or set()), _fetch=_fetch_r2,
            )

    if github is None:
        return CanonicalResolution(available=False, reason="no_canonical_provider_configured")
    try:
        manifest = github.manifest()
    except CanonicalSourceError as exc:
        return CanonicalResolution(available=False, reason=str(exc)[:200])
    if manifest is None:
        return CanonicalResolution(available=False, reason="no_canonical_release_published")

    def _fetch_github(destination: Path) -> dict[str, Any]:
        return github.fetch_events(manifest, destination)

    return CanonicalResolution(
        available=True,
        provider="github_private_release",
        canonical_object=str(manifest["object"]),
        sha256=str(manifest["sha256"]),
        bytes=int(manifest["bytes"]),
        unique_events=int(manifest["unique_events"]),
        release_tag=str(manifest.get("release_tag") or ""),
        release_published_at=str(manifest.get("release_published_at") or ""),
        superseded={str(row) for row in manifest.get("supersedes", []) if isinstance(row, str)},
        _fetch=_fetch_github,
    )
