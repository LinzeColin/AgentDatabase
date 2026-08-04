"""v0.0.0.32 T07 — one canonical gate, and the hook is never the authority.

The thing worth pinning is the *shape* of the code flow, not that a shell script
exits zero: a hook that could certify a release would be a second source of truth
on a machine nobody audits, and a parallel timer would be a second schedule
nobody reconciles.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "ops" / "memory-atlas" / "canonical_gate.sh"
HOOK = REPO / ".githooks" / "pre-push"
WORKFLOW = REPO / ".github" / "workflows" / "memory-atlas-v31.yml"
LIVE_PROBE = REPO / "ops" / "memory-atlas" / "post-promote-live-probe.sh"
POST_PROMOTE = REPO / "ops" / "memory-atlas" / "post-promote-probe.sh"


def test_there_is_exactly_one_canonical_gate_script() -> None:
    found = sorted(p.relative_to(REPO).as_posix() for p in REPO.glob("**/canonical_gate.sh") if ".git/" not in str(p))
    assert found == ["ops/memory-atlas/canonical_gate.sh"], found


def test_the_hook_calls_only_the_quick_gate() -> None:
    text = HOOK.read_text(encoding="utf-8")
    invocations = [
        line.strip()
        for line in text.splitlines()
        if "canonical_gate.sh" in line and not line.lstrip().startswith("#")
    ]
    assert invocations, text
    for line in invocations:
        assert " quick" in line, line
        assert " full" not in line, "the hook must never invoke the authoritative gate"
    assert HOOK.stat().st_mode & 0o111, "hook must be executable"


def test_the_hook_is_skippable_and_reversible() -> None:
    text = HOOK.read_text(encoding="utf-8")
    assert "MEMORY_ATLAS_SKIP_GATE" in text
    assert "git config --unset core.hooksPath" in text


def test_quick_mode_declares_itself_non_authoritative(tmp_path: Path) -> None:
    output = tmp_path / "quick.json"
    subprocess.run([str(GATE), str(REPO), "quick", str(output)], check=True, capture_output=True)
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["mode"] == "quick"
    assert report["authoritative"] is False


def test_full_mode_is_the_authority_and_is_a_strict_superset(tmp_path: Path) -> None:
    quick = tmp_path / "quick.json"
    full = tmp_path / "full.json"
    subprocess.run([str(GATE), str(REPO), "quick", str(quick)], check=True, capture_output=True)
    subprocess.run([str(GATE), str(REPO), "full", str(full)], check=True, capture_output=True)
    quick_checks = {row["check"] for row in json.loads(quick.read_text(encoding="utf-8"))["checks"]}
    full_report = json.loads(full.read_text(encoding="utf-8"))
    full_checks = {row["check"] for row in full_report["checks"]}
    assert full_report["authoritative"] is True
    assert quick_checks < full_checks, "full must run strictly more than quick"
    assert {"backend_suite", "frontend_build", "ci_workflow_present"} <= full_checks


def test_an_invalid_mode_is_refused() -> None:
    result = subprocess.run([str(GATE), str(REPO), "sorta"], capture_output=True)
    assert result.returncode == 64


def test_ci_runs_the_full_gate_not_the_quick_one() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "canonical_gate.sh" in text
    assert "canonical_gate.sh . full" in text or 'canonical_gate.sh "$PWD" full' in text
    assert "canonical_gate.sh . quick" not in text


def test_no_parallel_timer_was_added() -> None:
    # The reconcile timer already compensates for missed events; a second
    # schedule would be a second answer to "when is the data current".
    units = sorted(p.name for p in (REPO / "ops" / "memory-atlas" / "systemd").glob("*.timer"))
    assert units == [
        "memory-atlas-action-worker.timer",
        "memory-atlas-reconcile.timer",
        "memory-atlas-selfheal.timer",
    ], units


def test_reconcile_compensation_window_is_at_most_fifteen_minutes() -> None:
    timer = (REPO / "ops" / "memory-atlas" / "systemd" / "memory-atlas-reconcile.timer").read_text(encoding="utf-8")
    interval = next(
        line.split("=", 1)[1].strip()
        for line in timer.splitlines()
        if line.startswith("OnUnitActiveSec=")
    )
    assert interval.endswith("min"), interval
    assert int(interval[:-3]) <= 15, interval


def test_post_promote_calls_the_live_probe_and_fails_on_it() -> None:
    text = POST_PROMOTE.read_text(encoding="utf-8")
    assert "post-promote-live-probe.sh" in text
    assert "LIVE_SNAPSHOT_PROBE_FAIL" in text
    assert "exit 6" in text


def test_live_probe_refuses_to_pass_without_an_access_token(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(LIVE_PROBE), "https://example.invalid", "REL", "DEP", str(tmp_path)],
        capture_output=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin"},
    )
    assert result.returncode == 3
    receipt = json.loads((tmp_path / "API_RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["state"] == "NOT_RUN"


@pytest.mark.parametrize(
    "needle",
    ["no-store", "header/body mismatch", "unexpected release_id", "unexpected deployment_revision", "privacy contract"],
)
def test_live_probe_checks_every_identity_and_contract_field(needle: str) -> None:
    assert needle in LIVE_PROBE.read_text(encoding="utf-8")


def test_deploy_refuses_an_unidentified_tree() -> None:
    # A release whose id does not name a real commit cannot be rolled back to,
    # audited, or matched against the running artifact.
    text = (REPO / "ops" / "memory-atlas" / "deploy-blue-green.sh").read_text(encoding="utf-8")
    assert "refusing to deploy an unidentified tree" in text
    assert '[[ "$release_commit" =~ ^[0-9a-f]{40}$ ]]' in text
    assert 'release_id="$(date -u +%Y%m%dT%H%M%SZ)-${release_commit:0:12}"' in text
    assert "git rev-parse HEAD" in text, "a real checkout must still be the default source of identity"


# Import name -> distribution name, for the cases where they differ. Kept
# explicit and tiny: a wrong entry here would silently excuse a real gap.
IMPORT_TO_DISTRIBUTION = {"jwt": "pyjwt"}


def _undeclared_third_party_imports(declared: set[str]) -> set[str]:
    import ast
    import importlib.util
    import sysconfig

    stdlib = Path(sysconfig.get_paths()["stdlib"]).resolve()

    def is_stdlib(root: str) -> bool:
        try:
            spec = importlib.util.find_spec(root)
        except (ImportError, ValueError):
            return False
        if spec is None:
            return False
        if spec.origin in (None, "built-in", "frozen"):
            return True
        try:
            return stdlib in Path(spec.origin).resolve().parents
        except OSError:
            return False

    package_dir = REPO / "OpenAIDatabase" / "scripts" / "memory_atlas_private"
    local = {path.stem for path in package_dir.glob("*.py")}
    undeclared: set[str] = set()
    for path in sorted(package_dir.glob("*.py")):
        if path.name.startswith("test_"):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for name in names:
                root = name.split(".")[0]
                if root in local or is_stdlib(root):
                    continue
                distribution = IMPORT_TO_DISTRIBUTION.get(root.lower(), root.lower())
                if distribution not in declared:
                    undeclared.add(f"{path.name}: {root}")
    return undeclared


def _declared_requirements() -> set[str]:
    text = (
        REPO / "OpenAIDatabase" / "scripts" / "memory_atlas_private" / "requirements-memory-atlas-private.txt"
    ).read_text(encoding="utf-8")
    return {
        line.split("==")[0].split("[")[0].strip().lower()
        for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    }


def test_every_third_party_import_in_the_serving_path_is_declared() -> None:
    """The production deploy died on `ModuleNotFoundError: jsonschema`.

    `live_snapshot_store` imports it at module load and `api_server` imports
    that, so the private API could not start — and nothing before the deploy
    noticed, because CI installed jsonschema in a separate step that the
    requirements file never mentioned.
    """
    assert _undeclared_third_party_imports(_declared_requirements()) == set()


def test_the_dependency_checker_catches_the_dependency_that_broke_the_deploy() -> None:
    without = _declared_requirements() - {"jsonschema"}
    assert any("jsonschema" in row for row in _undeclared_third_party_imports(without))


def test_promotion_recreates_the_container_and_proves_what_is_served() -> None:
    """The web container bind-mounts $APP_ROOT/current/dist and Docker resolves
    that symlink to an inode at start. Without --force-recreate the container
    keeps serving the release it started on: every promotion between
    2026-08-03T20:16 and 2026-08-04T01 was correct at the origin and invisible
    in the browser."""
    deploy = (REPO / "ops" / "memory-atlas" / "deploy-blue-green.sh").read_text(encoding="utf-8")
    assert "--force-recreate" in deploy
    probe = POST_PROMOTE.read_text(encoding="utf-8")
    assert "SERVED_ARTIFACT_IS_NOT_THE_PROMOTED_RELEASE" in probe
    assert "exit 7" in probe


def test_promotion_prunes_everything_rollback_cannot_reach() -> None:
    """Four promotions in one evening filled a 38 GB disk and the fifth died
    mid-rsync: each agent release is a ~770 MB copy and nothing pruned them.
    Blue-green can only ever roll back to previous, so anything older is dead
    weight."""
    deploy = (REPO / "ops" / "memory-atlas" / "deploy-blue-green.sh").read_text(encoding="utf-8")
    assert "prune_superseded_releases" in deploy
    assert 'prune_superseded_releases "$AGENT_ROOT"' in deploy
    assert 'prune_superseded_releases "$APP_ROOT"' in deploy
    # current and previous are the rollback contract; they must be exempt.
    assert '[[ "$name" == "$keep_current" || "$name" == "$keep_previous" ]] && continue' in deploy
    # Pruning must happen before the release is copied, or it frees space too late.
    assert deploy.index("prune_superseded_releases \"$APP_ROOT\"") < deploy.index('cp -a MemoryAtlas/dist')
