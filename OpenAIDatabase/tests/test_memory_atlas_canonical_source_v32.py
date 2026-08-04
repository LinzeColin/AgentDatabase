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


# --- The content-addressed source store, after the migration -----------------
#
# R2 held 2,363 objects of source bytes under sha256/. They moved to the
# encrypted per-run backup releases. The reconcile still verifies the manifest,
# so it has to be able to say which of "still in R2", "inside the canonical
# union" and "inside this run's archive" accounts for each object — and to fail
# when none of them does.

from OpenAIDatabase.scripts.memory_atlas_private.canonical_source import (  # noqa: E402
    BackupCoverage,
    verify_backup_coverage,
)

RUN = "marun_5bd5fa6104b034eaf65bdee3"


def _backup(**overrides) -> dict:
    value = {
        "schema_version": "memory_atlas.encrypted_archive_manifest.v1",
        "backup_id": RUN,
        "state": "PASS",
        "release_tag": "memory-atlas-auto-backup-20260803170227-34eaf65bdee3",
        "ciphertext_part_count": 8,
        "remote_readback_verified": True,
        "isolated_restore": {"state": "PASS", "all_hashes_match": True, "restored_files": 2301},
    }
    value.update(overrides)
    return value


class _Releases:
    """A gh client that answers only about backup releases."""

    def __init__(self, assets: int | None = 8):
        self.assets = assets
        self.asked: list[str] = []

    def release_assets(self, tag: str):
        self.asked.append(tag)
        return None if self.assets is None else [{"name": f"part{i}.age"} for i in range(self.assets)]


def test_a_passing_backup_that_still_exists_covers_the_source_store() -> None:
    github = _Releases()
    coverage = verify_backup_coverage(
        github, _backup(), run_id=RUN, manifest_object_count=2302, canonical_covered=1
    )
    assert coverage.state == "COVERED" and coverage.covered
    assert coverage.covered_object_count == 2302 and coverage.restored_files == 2301
    assert github.asked == ["memory-atlas-auto-backup-20260803170227-34eaf65bdee3"]
    # It is an archive-restore proof, not a live byte read, and says so.
    assert coverage.to_fact()["verification_class"].startswith("ARCHIVE_RESTORE_PROOF")


def test_a_backup_whose_release_was_deleted_is_absent_not_covered() -> None:
    """A record saying a backup was made is not evidence it still exists."""
    coverage = verify_backup_coverage(
        _Releases(assets=None), _backup(), run_id=RUN, manifest_object_count=2302, canonical_covered=1
    )
    assert coverage.state == "ABSENT" and coverage.reason == "backup_release_no_longer_exists"


def test_a_release_missing_shards_does_not_cover() -> None:
    coverage = verify_backup_coverage(
        _Releases(assets=5), _backup(), run_id=RUN, manifest_object_count=2302, canonical_covered=1
    )
    assert not coverage.covered and coverage.reason == "backup_release_is_missing_shards"


def test_coverage_requires_the_count_to_add_up() -> None:
    """The failure this rule exists to catch: "a backup exists" excusing an
    arbitrary number of objects that vanished."""
    coverage = verify_backup_coverage(
        _Releases(), _backup(), run_id=RUN, manifest_object_count=9000, canonical_covered=1
    )
    assert not coverage.covered
    assert coverage.reason == "archive_does_not_account_for_every_manifest_object"
    assert coverage.covered_object_count == 2302 and coverage.manifest_object_count == 9000


@pytest.mark.parametrize(
    "broken,reason",
    [
        ({"backup_id": "marun_someone_else"}, "backup_record_belongs_to_another_run"),
        ({"state": "FAILED"}, "backup_state_FAILED"),
        ({"remote_readback_verified": False}, "remote_readback_not_verified"),
        ({"isolated_restore": {"state": "PASS", "all_hashes_match": False, "restored_files": 2301}},
         "isolated_restore_did_not_prove_the_hashes"),
        ({"isolated_restore": {"state": "FAILED", "all_hashes_match": True, "restored_files": 2301}},
         "isolated_restore_did_not_prove_the_hashes"),
    ],
)
def test_a_backup_that_did_not_prove_itself_never_covers(broken: dict, reason: str) -> None:
    coverage = verify_backup_coverage(
        _Releases(), _backup(**broken), run_id=RUN, manifest_object_count=2302, canonical_covered=1
    )
    assert coverage.state == "ABSENT" and coverage.reason == reason


def test_no_backup_record_at_all_is_absent() -> None:
    for value in (None, "not-a-mapping", []):
        coverage = verify_backup_coverage(
            _Releases(), value, run_id=RUN, manifest_object_count=2302, canonical_covered=1
        )
        assert coverage.state == "ABSENT"


def test_an_uncovered_object_still_fails_the_reconcile() -> None:
    source = (REPO / "OpenAIDatabase" / "scripts" / "memory_atlas_private" / "pipeline.py").read_text(encoding="utf-8")
    # Migration may only absorb the missing list when coverage was proven.
    assert "if missing and backup_coverage.covered:" in source
    assert "migrated, missing = missing, []" in source
    assert 'error_code="OBJECT_READBACK_MISMATCH"' in source
    # And the published run fact has to name where the bytes went.
    assert '"storage_migration"' in source
    assert '"primary": "GITHUB_PRIVATE_REPOSITORY"' in source


def test_backup_coverage_defaults_to_not_covering() -> None:
    assert not BackupCoverage(state="INSUFFICIENT").covered
    assert not BackupCoverage(state="ABSENT").covered


def test_the_deploy_computes_the_artifact_digest_it_publishes() -> None:
    """`MEMORY_ATLAS_ARTIFACT_DIGEST` was only ever read from the environment and
    nothing set it, so every promotion wrote an empty value and every published
    snapshot carried `artifact_digest: null` — the release oracle had nothing to
    bind the served bundle to."""
    deploy = (REPO / "ops" / "memory-atlas" / "deploy-blue-green.sh").read_text(encoding="utf-8")
    assert 'if [[ -z "$artifact_digest" && -d "$release/dist" ]]; then' in deploy
    # Over the promoted bundle, deterministically, not over the source tree.
    assert 'cd "$release/dist" && find . -type f -print0 | LC_ALL=C sort -z' in deploy
    assert 'MEMORY_ATLAS_ARTIFACT_DIGEST=%s' in deploy


def test_release_identity_is_written_before_anything_reads_it() -> None:
    """The promotion restarted the reconcile and then wrote the identity file, so
    the run it triggered read the previous release and the published snapshot
    named a release one promotion behind — every time, permanently."""
    deploy = (REPO / "ops" / "memory-atlas" / "deploy-blue-green.sh").read_text(encoding="utf-8")
    identity = deploy.index('> "$APP_ROOT/shared/release-identity.env"')
    for consumer in (
        "sudo systemctl restart memory-atlas-api.service",
        "sudo systemctl restart --no-block memory-atlas-reconcile.service",
        "sudo systemctl restart memory-atlas-action-worker.service",
    ):
        assert identity < deploy.index(consumer), consumer


def test_the_chinese_audit_runs_against_the_data_production_serves() -> None:
    """The audit reported PASS on the build-time snapshot while production
    rendered 88 raw tokens across three views: the ten views read an atlas the
    origin regenerates, and the failure-compound and behaviour-economy views
    read a live API that does not exist locally at all."""
    auditor = (REPO / "MemoryAtlas" / "scripts" / "audit_chinese_ui_v32.mjs").read_text(encoding="utf-8")
    assert "const [url, output, liveAtlas, liveSnapshot, liveStatus]" in auditor
    for route in ("**/memory_atlas.json", "**/api/v31/live-snapshot", "**/api/v31/status**"):
        assert route in auditor, route
    # A narrower pass may not read as a full one.
    assert "live_data: { atlas: liveAtlas ?? null, snapshot: liveSnapshot ?? null, status: liveStatus ?? null }" in auditor

    gate = (REPO / "ops" / "memory-atlas" / "canonical_gate.sh").read_text(encoding="utf-8")
    assert 'live_dir=$(mktemp -d' in gate
    assert '"${live_args[@]}"' in gate
    # Pulled at run time, never committed: the private analytics snapshot is
    # exactly what the privacy contract keeps out of the repository.
    assert not (REPO / "MemoryAtlas" / "fixtures" / "live").exists()


def test_verbatim_records_are_skipped_for_a_stated_reason() -> None:
    """The sealed incident ledger's titles carry a source contract and a digest.
    Rewriting them to Chinese would falsify an archived record."""
    auditor = (REPO / "MemoryAtlas" / "scripts" / "audit_chinese_ui_v32.mjs").read_text(encoding="utf-8")
    assert 'const VERBATIM_RECORD_CONTEXTS = ["[data-record-verbatim]"];' in auditor
    assert "verbatim_records: VERBATIM_RECORD_CONTEXTS" in auditor
    view = (REPO / "MemoryAtlas" / "src" / "features" / "v31" / "FailureCompoundView.tsx").read_text(encoding="utf-8")
    assert 'data-record-verbatim="true"' in view
    # The interface around the record still has to be Chinese.
    assert 'humanizeMachineText(String(row.category ?? "未知"))' in view
    assert 'humanizeMachineText(String(row.status ?? "未知"))' in view


def test_ci_installs_the_browser_before_the_gate_that_needs_it() -> None:
    """The gate now drives a real browser. CI installed chromium in a later job,
    so the gate failed with a Playwright install banner reported as a
    Chinese-UI finding — an environment fact dressed up as a language defect."""
    workflow = (REPO / ".github" / "workflows" / "memory-atlas-v31.yml").read_text(encoding="utf-8")
    install = workflow.index("npx playwright install --with-deps chromium")
    gate = workflow.index("./ops/memory-atlas/canonical_gate.sh . full")
    assert install < gate, "chromium must be installed before the canonical gate runs"

    auditor = (REPO / "MemoryAtlas" / "scripts" / "audit_chinese_ui_v32.mjs").read_text(encoding="utf-8")
    assert "BROWSER_UNAVAILABLE" in auditor
    assert "process.exit(3)" in auditor
