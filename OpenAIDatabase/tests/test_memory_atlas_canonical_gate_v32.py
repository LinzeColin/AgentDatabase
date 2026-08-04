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


def _declared_checks(mode: str) -> set[str]:
    """Read the checks the script declares, rather than executing it.

    The gate runs the suite that tests the gate, so executing `full` from here
    forked gates until the run had to be killed. The invariant is about what the
    modes declare, and that is readable without running anything.
    """
    import re

    text = GATE.read_text(encoding="utf-8")
    shared, _, full_only = text.partition('if [[ "$mode" == "full" ]]; then')
    scope = shared if mode == "quick" else shared + full_only
    return set(re.findall(r"run_check (\w+)", scope))


def test_quick_mode_declares_itself_non_authoritative(tmp_path: Path) -> None:
    import os

    output = tmp_path / "quick.json"
    # This asserts the standalone contract, so the nested-run guard the outer
    # gate sets must not be inherited.
    env = {k: v for k, v in os.environ.items() if k != "MEMORY_ATLAS_GATE_RUNNING"}
    subprocess.run([str(GATE), str(REPO), "quick", str(output)], check=True, capture_output=True, env=env)
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["mode"] == "quick"
    assert report["authoritative"] is False


def test_full_mode_is_the_authority_and_is_a_strict_superset() -> None:
    quick, full = _declared_checks("quick"), _declared_checks("full")
    assert quick < full, (quick, full)
    assert {"backend_suite", "frontend_build", "ci_workflow_present"} <= full
    assert '"authoritative":%s' in GATE.read_text(encoding="utf-8")


def test_a_nested_gate_cannot_fork_forever() -> None:
    gate = GATE.read_text(encoding="utf-8")
    assert "MEMORY_ATLAS_GATE_RUNNING" in gate
    assert "NESTED_SKIPPED" in gate
    assert "export MEMORY_ATLAS_GATE_RUNNING=1" in gate


def test_an_invalid_mode_is_refused() -> None:
    import os

    env = {k: v for k, v in os.environ.items() if k != "MEMORY_ATLAS_GATE_RUNNING"}
    result = subprocess.run([str(GATE), str(REPO), "sorta"], capture_output=True, env=env)
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
    import sys
    import sysconfig

    stdlib = Path(sysconfig.get_paths()["stdlib"]).resolve()
    # sys.stdlib_module_names is authoritative but 3.10+; the Owner's machine is
    # 3.9. The path fallback must exclude site-packages explicitly: on CI it
    # lives *inside* the stdlib directory, so a parent check alone classified
    # every installed package as stdlib and the checker silently passed there.
    # Deliberately not called `names`: the loop below rebinds that, and the
    # closure then read the import list instead of the stdlib set.
    stdlib_names = getattr(sys, "stdlib_module_names", None)

    def is_stdlib(root: str) -> bool:
        if stdlib_names is not None:
            return root in stdlib_names
        try:
            spec = importlib.util.find_spec(root)
        except (ImportError, ValueError):
            return False
        if spec is None:
            return False
        if spec.origin in (None, "built-in", "frozen"):
            return True
        try:
            origin = Path(spec.origin).resolve()
        except OSError:
            return False
        if any(part in {"site-packages", "dist-packages"} for part in origin.parts):
            return False
        return stdlib in origin.parents

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


def test_the_full_gate_covers_what_ci_runs() -> None:
    """A commit reached main with the full gate green and CI red, because the
    gate did not run validate:whole-project. A gate that is a sample of CI
    rather than a superset of it is not a gate."""
    gate = GATE.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for script in ("lint", "validate:preservation", "validate:v31", "validate:v31:incremental",
                   "validate:v31:typescript", "build", "validate:whole-project"):
        assert script in workflow, f"CI no longer runs {script}"
        assert script in gate, f"the gate does not account for {script}"
    # validate:whole-project needs live deployment evidence, so it runs on CI
    # only. The gate must say so rather than silently omit it.
    assert "validate:whole-project belongs here in principle" in gate
    assert "npm run validate:whole-project" in workflow


def test_the_gate_runs_every_test_the_ownership_contract_lists() -> None:
    """The gate listed backend test files by hand and drifted: two v0.0.0.32
    suites existed for hours without it ever running them, so it reported green
    while they were red. The list comes from the ownership contract now."""
    gate = GATE.read_text(encoding="utf-8")
    assert "verification_policy.json" in gate
    assert "execution_tiers" in gate and "integration" in gate and "test_files" in gate
    # No hand-maintained list of individual v31/v32 suites may remain.
    assert "tests/test_memory_atlas_live_snapshot_api_v32.py" not in gate
    # bash 3.2 has no mapfile; using it made the gate exit 127 and run a
    # truncated suite on the Owner's machine. Check for use, not the word — the
    # comment explaining this lives in the script.
    executable = [line for line in gate.splitlines() if not line.lstrip().startswith("#")]
    assert not [line for line in executable if "mapfile" in line], "mapfile is bash 4+"
    # Every Memory Atlas suite the contract owns must be reachable by the gate.
    import json as _json

    policy = _json.loads(
        (REPO / "OpenAIDatabase" / "config" / "quality" / "verification_policy.json").read_text(encoding="utf-8")
    )
    owned = [
        name for name in policy["execution_tiers"]["integration"]["test_files"]
        if "memory_atlas" in name and (REPO / "OpenAIDatabase" / name).is_file()
    ]
    assert len(owned) >= 5, owned
    for name in ("tests/test_memory_atlas_codex_activity_adapter_v32.py",
                 "tests/test_memory_atlas_canonical_gate_v32.py"):
        assert name in owned, f"{name} is not owned by the integration tier"
    # Exclusions must be named with a reason, and only these two qualify: they
    # assert against a live deployment. Everything else the contract owns runs.
    import re as _re

    block = _re.search(r"CI_ONLY = \{(.*?)\}", gate, _re.S)
    assert block, "the gate must declare its exclusions explicitly"
    excluded = set(_re.findall(r"'([^']+)'", block.group(1)))
    assert excluded == {
        "tests/test_memory_atlas_acceptance_audit.py",
        "tests/test_memory_atlas_goal_completion.py",
    }, excluded
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "validate:whole-project" in workflow, "CI must still run the excluded suites"
