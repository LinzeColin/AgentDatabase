"""The GitHub private repository as the primary event authority.

R2 held the canonical union until 2026-08-04, when the bucket approached its
storage cap and the memory-atlas primary tree moved to
`LinzeColin/Private-Database`. The reconcile then failed every run: it verified
a source manifest against R2 bytes that no longer existed and refused to read
anything else.

These tests pin the migration's contract. The thing they exist to prevent is a
reconcile that keeps running by trusting a name — a cached file, a release tag,
an asset that downloaded without error — instead of the digest. Every path that
produces events here must have hashed them first.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest

from OpenAIDatabase.scripts.memory_atlas_private.canonical_source import (
    CanonicalResolution,
    CanonicalSourceError,
    GitHubCanonicalSource,
    resolve_canonical,
)

REPO = Path(__file__).resolve().parents[2]
EVENTS = b'{"event_id":"evt_1","activity":"verification_repair"}\n{"event_id":"evt_2","activity":"deployed"}\n'
DIGEST = hashlib.sha256(EVENTS).hexdigest()

RELEASES = [
    {"tagName": "memory-atlas-canonical-20260801", "publishedAt": "2026-08-01T00:00:00Z", "isDraft": False},
    {"tagName": "memory-atlas-canonical-20260804", "publishedAt": "2026-08-04T08:02:40Z", "isDraft": False},
    {"tagName": "memory-atlas-canonical-20260806", "publishedAt": "2026-08-06T00:00:00Z", "isDraft": True},
    {"tagName": "ovh-logs-20260804", "publishedAt": "2026-08-04T06:21:45Z", "isDraft": False},
]


def _manifest(**overrides) -> dict:
    value = {
        "schema_version": "memory_atlas.canonical_events_manifest.v1",
        "object": "primary-objects/memory-atlas/private-agentdatabase/normalized/canonical/events.jsonl",
        "sha256": DIGEST,
        "bytes": len(EVENTS),
        "unique_events": 2,
        "supersedes": ["primary-objects/memory-atlas/private-agentdatabase/normalized/marun_old/events.jsonl"],
    }
    value.update(overrides)
    return value


def _fake_gh(tmp_path: Path, *, manifest: dict | None = None, events: bytes = EVENTS) -> Path:
    """A `gh` that answers from disk, so no test ever reaches the network."""
    payload = tmp_path / "gh-fixture"
    payload.mkdir(exist_ok=True)
    (payload / "releases.json").write_text(json.dumps(RELEASES), encoding="utf-8")
    (payload / "MANIFEST.json").write_text(
        json.dumps(_manifest() if manifest is None else manifest), encoding="utf-8"
    )
    (payload / "events.jsonl").write_bytes(events)
    script = tmp_path / "gh"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import shutil, sys\n"
        f"root = {str(payload)!r}\n"
        "args = sys.argv[1:]\n"
        "if args[:2] == ['release', 'list']:\n"
        "    sys.stdout.write(open(root + '/releases.json').read()); raise SystemExit(0)\n"
        "if args[:2] == ['release', 'download']:\n"
        "    pattern = args[args.index('--pattern') + 1]\n"
        "    output = args[args.index('--output') + 1]\n"
        "    shutil.copyfile(root + '/' + pattern, output); raise SystemExit(0)\n"
        "sys.stderr.write('unsupported: ' + ' '.join(args)); raise SystemExit(1)\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


def _source(tmp_path: Path, **kwargs) -> GitHubCanonicalSource:
    return GitHubCanonicalSource(
        repo="LinzeColin/Private-Database",
        gh_path=str(_fake_gh(tmp_path, **kwargs)),
        cache_dir=tmp_path / "cache",
    )


def test_the_newest_published_canonical_release_wins(tmp_path: Path) -> None:
    release = _source(tmp_path).latest_tag()
    # Not the draft that sorts latest, and not the unrelated log archive.
    assert release == {"tag": "memory-atlas-canonical-20260804", "published_at": "2026-08-04T08:02:40Z"}


def test_manifest_carries_the_release_it_came_from(tmp_path: Path) -> None:
    manifest = _source(tmp_path).manifest()
    assert manifest["release_tag"] == "memory-atlas-canonical-20260804"
    assert manifest["sha256"] == DIGEST and manifest["unique_events"] == 2


@pytest.mark.parametrize(
    "broken",
    [
        {"schema_version": "memory_atlas.something_else.v1"},
        {"sha256": ""},
        {"unique_events": None},
    ],
)
def test_a_manifest_that_does_not_describe_the_object_is_refused(tmp_path: Path, broken: dict) -> None:
    with pytest.raises(CanonicalSourceError):
        _source(tmp_path, manifest=_manifest(**broken)).manifest()


def test_events_are_accepted_only_when_the_digest_matches(tmp_path: Path) -> None:
    source = _source(tmp_path)
    destination = tmp_path / "events.jsonl"
    receipt = source.fetch_events(source.manifest(), destination)
    assert receipt["state"] == "READY" and receipt["cache"] == "MISS"
    assert destination.read_bytes() == EVENTS


def test_a_substituted_asset_is_a_hard_error_and_leaves_no_file(tmp_path: Path) -> None:
    """The failure mode that matters: a download that succeeds but is not the
    object. Accepting it would publish a smaller event stream as the truth."""
    source = _source(tmp_path, events=EVENTS + b'{"event_id":"evt_3"}\n')
    destination = tmp_path / "events.jsonl"
    with pytest.raises(CanonicalSourceError, match="canonical_asset_mismatch"):
        source.fetch_events(source.manifest(), destination)
    assert not destination.exists()


def test_the_cache_is_re_hashed_not_trusted_by_name(tmp_path: Path) -> None:
    source = _source(tmp_path)
    manifest = source.manifest()
    first = tmp_path / "first.jsonl"
    assert source.fetch_events(manifest, first)["cache"] == "MISS"
    second = tmp_path / "second.jsonl"
    assert source.fetch_events(manifest, second)["cache"] == "HIT"
    assert second.read_bytes() == EVENTS

    # Corrupt the cache under its correct-looking name. The next read must
    # notice and re-download rather than serve the wrong bytes.
    cached = tmp_path / "cache" / f"{DIGEST}.jsonl"
    cached.unlink()
    cached.write_bytes(b'{"event_id":"evt_wrong"}\n')
    third = tmp_path / "third.jsonl"
    assert source.fetch_events(manifest, third)["cache"] == "MISS"
    assert third.read_bytes() == EVENTS


def test_only_one_canonical_digest_is_kept_on_disk(tmp_path: Path) -> None:
    # The asset is 389 MB and the origin runs at 81% disk; an unbounded cache
    # fills the volume and takes the deployment down with it.
    source = _source(tmp_path)
    source.fetch_events(source.manifest(), tmp_path / "a.jsonl")
    (tmp_path / "cache" / f"{'d' * 64}.jsonl").write_bytes(b"stale\n")
    source.fetch_events(source.manifest(), tmp_path / "b.jsonl")
    assert [path.name for path in sorted((tmp_path / "cache").glob("*.jsonl"))] == [f"{DIGEST}.jsonl"]


class _DrainedR2:
    """R2 after the migration: reachable, and holding none of it."""

    def exists_with_hash(self, key: str, expected_sha256: str) -> bool:
        return False

    def get_file(self, key: str, destination: Path) -> None:
        raise RuntimeError("404")


class _HealthyR2(_DrainedR2):
    def __init__(self, key: str, digest: str, payload: bytes):
        self.key, self.digest, self.payload = key, digest, payload

    def exists_with_hash(self, key: str, expected_sha256: str) -> bool:
        return key == self.key and expected_sha256 == self.digest

    def get_file(self, key: str, destination: Path) -> None:
        destination.write_bytes(self.payload)


def _r2_manifest(available: bool):
    def loader(object_store, work_dir):
        if not available:
            return {"available": False, "canonical_object": None, "sha256": None, "superseded": set()}
        return {
            "available": True,
            "canonical_object": "primary-objects/memory-atlas/x/canonical/events.jsonl",
            "sha256": DIGEST,
            "unique_events": 2,
            "superseded": {"primary-objects/memory-atlas/x/normalized/marun_old/events.jsonl"},
        }

    return loader


def test_r2_is_used_when_it_still_holds_the_bytes(tmp_path: Path) -> None:
    # Preference, not assumption: the cheap local side wins only by verifying.
    store = _HealthyR2("primary-objects/memory-atlas/x/canonical/events.jsonl", DIGEST, EVENTS)
    resolution = resolve_canonical(
        object_store=store, github=_source(tmp_path), work_dir=tmp_path,
        r2_manifest_loader=_r2_manifest(True),
    )
    assert resolution.available and resolution.provider == "r2"
    destination = tmp_path / "events.jsonl"
    assert resolution.fetch(destination)["provider"] == "r2"
    assert destination.read_bytes() == EVENTS


def test_a_drained_bucket_falls_through_to_the_github_primary(tmp_path: Path) -> None:
    """The exact production state on 2026-08-04: R2 answers for nothing and the
    private repository holds the union."""
    resolution = resolve_canonical(
        object_store=_DrainedR2(), github=_source(tmp_path), work_dir=tmp_path,
        r2_manifest_loader=_r2_manifest(False),
    )
    assert resolution.available and resolution.provider == "github_private_release"
    assert resolution.unique_events == 2
    assert resolution.release_tag == "memory-atlas-canonical-20260804"
    assert resolution.fetch(tmp_path / "events.jsonl")["provider"] == "github_private_release"


def test_r2_naming_an_object_it_no_longer_holds_does_not_win(tmp_path: Path) -> None:
    # The R2 manifest survived a partial drain; the object it names did not.
    resolution = resolve_canonical(
        object_store=_DrainedR2(), github=_source(tmp_path), work_dir=tmp_path,
        r2_manifest_loader=_r2_manifest(True),
    )
    assert resolution.provider == "github_private_release"


def test_no_canonical_release_is_unavailable_with_a_reason_not_a_crash(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    source = _source(empty)
    (empty / "gh-fixture" / "releases.json").write_text(json.dumps(RELEASES[3:]), encoding="utf-8")
    resolution = resolve_canonical(
        object_store=_DrainedR2(), github=source, work_dir=tmp_path, r2_manifest_loader=_r2_manifest(False),
    )
    assert not resolution.available
    assert resolution.reason == "no_canonical_release_published"
    assert resolution.to_fact()["state"] == "UNAVAILABLE"


def test_an_unavailable_resolution_covers_nothing_and_refuses_to_fetch(tmp_path: Path) -> None:
    resolution = CanonicalResolution(available=False, reason="gh_unavailable")
    assert not resolution.covers("anything")
    with pytest.raises(CanonicalSourceError, match="canonical_source_unavailable"):
        resolution.fetch(tmp_path / "x.jsonl")


def test_covers_answers_for_the_union_and_everything_it_replaced(tmp_path: Path) -> None:
    resolution = resolve_canonical(
        object_store=_DrainedR2(), github=_source(tmp_path), work_dir=tmp_path,
        r2_manifest_loader=_r2_manifest(False),
    )
    assert resolution.covers("primary-objects/memory-atlas/private-agentdatabase/normalized/marun_old/events.jsonl")
    assert resolution.covers(resolution.canonical_object)
    assert not resolution.covers("primary-objects/memory-atlas/never-existed/events.jsonl")


def test_a_broken_r2_loader_does_not_take_the_run_down(tmp_path: Path) -> None:
    def explode(object_store, work_dir):
        raise RuntimeError("R2 credentials revoked")

    resolution = resolve_canonical(
        object_store=_DrainedR2(), github=_source(tmp_path), work_dir=tmp_path, r2_manifest_loader=explode,
    )
    assert resolution.available and resolution.provider == "github_private_release"


def test_the_reconcile_never_lets_an_r2_error_escape() -> None:
    source = (REPO / "OpenAIDatabase" / "scripts" / "memory_atlas_private" / "pipeline.py").read_text(encoding="utf-8")
    assert "def _r2_holds(self, key: str, digest: str) -> bool:" in source
    assert "if key and digest and self._r2_holds(key, digest):" in source
    # The fetch must go through the resolution, never straight at the bucket.
    assert "canonical_receipt = canonical.fetch(temporary)" in source


def test_the_registry_records_why_the_primary_moved() -> None:
    registry = json.loads((REPO / "ops" / "memory-atlas" / "source-registry.json").read_text(encoding="utf-8"))
    primary = registry["primary_data_authority"]
    assert primary["state"] == "GITHUB_PRIVATE_REPOSITORY"
    assert primary["migrated_at"] == "2026-08-04"
    assert "收费" in primary["reason_zh"]
    # Task 1: neither Cloudflare nor OVH may carry the data pressure.
    assert "不承担数据存量" in primary["cloudflare_role_zh"]
    assert "不承担数据存量" in primary["ovh_role_zh"]


def test_gh_is_located_without_inheriting_a_shell_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from OpenAIDatabase.scripts.memory_atlas_private import canonical_source

    monkeypatch.setenv("MEMORY_ATLAS_GH_PATH", str(tmp_path / "absent"))
    with pytest.raises(CanonicalSourceError, match="gh_unavailable"):
        canonical_source._resolve_gh()
    script = _fake_gh(tmp_path)
    monkeypatch.setenv("MEMORY_ATLAS_GH_PATH", str(script))
    assert canonical_source._resolve_gh() == str(script)
    assert os.access(canonical_source._resolve_gh(), os.X_OK)
