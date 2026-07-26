from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile
from typing import Any, Dict, Optional

from .io import utc_now, write_json


def _command(name: str) -> Dict[str, Any]:
    path = shutil.which(name)
    return {"available": bool(path), "path": path}


def _probe_filesystem(base: Path) -> Dict[str, Any]:
    base.mkdir(parents=True, exist_ok=True)
    result: Dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="teleiosis-doctor-", dir=str(base)) as td:
        root = Path(td)
        first = root / "first.txt"
        second = root / "second.txt"
        first.write_text("a", encoding="utf-8")
        second.write_text("b", encoding="utf-8")
        os.replace(str(second), str(first))
        result["atomic_replace"] = first.read_text(encoding="utf-8") == "b" and not second.exists()
        case_a = root / "CaseProbe"
        case_b = root / "caseprobe"
        case_a.write_text("A", encoding="utf-8")
        result["case_sensitive"] = not case_b.exists()
        link = root / "link"
        try:
            link.symlink_to(first)
            result["symlink_supported"] = link.is_symlink()
        except (OSError, NotImplementedError):
            result["symlink_supported"] = False
        lock_ok = False
        try:
            with first.open("r+b") as handle:
                if os.name == "nt":  # pragma: no cover - Windows only
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                lock_ok = True
        except (OSError, ImportError):
            lock_ok = False
        result["advisory_lock"] = lock_ok
        try:
            with first.open("ab") as handle:
                handle.write(b"x")
                handle.flush()
                os.fsync(handle.fileno())
            result["file_fsync"] = True
        except OSError:
            result["file_fsync"] = False
    return result


def run_environment_doctor(
    workspace: Path,
    output_path: Optional[Path] = None,
    review_contract: Optional[Path] = None,
    persona_index: Optional[Path] = None,
) -> Dict[str, Any]:
    workspace = workspace.resolve()
    filesystem = _probe_filesystem(workspace)
    python_ok = sys.version_info >= (3, 9)
    commands = {name: _command(name) for name in ("git", "zip", "unzip")}
    modules = {
        "cryptography": bool(importlib.util.find_spec("cryptography")),
        "jsonschema": bool(importlib.util.find_spec("jsonschema")),
    }
    hard_failures = []
    if not python_ok:
        hard_failures.append("Python 3.9+ required")
    if not commands["git"]["available"]:
        hard_failures.append("Git is required")
    for key in ("atomic_replace", "advisory_lock", "file_fsync"):
        if not filesystem.get(key):
            hard_failures.append("filesystem capability missing: %s" % key)

    review_available = bool(review_contract and review_contract.is_file())
    personas_available = bool(persona_index and persona_index.is_file())
    formal_blockers = []
    if not review_available:
        formal_blockers.append("external review attestation contract not supplied")
    if not modules["cryptography"]:
        formal_blockers.append("cryptography module unavailable for Ed25519 attestation verification")
    if not personas_available:
        formal_blockers.append("persona-distiller-group team index not supplied")

    result = {
        "schema_version": "1.0",
        "status": "PASS" if not hard_failures else "BLOCKED",
        "generated_at": utc_now(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "python_39_plus": python_ok,
        },
        "commands": commands,
        "python_modules": modules,
        "filesystem": filesystem,
        "capabilities": {
            "network": "NOT_PROBED",
            "github_token_present": bool(os.environ.get("GITHUB_TOKEN")),
            "external_review_contract_present": review_available,
            "persona_team_index_present": personas_available,
            "secret_values_exposed": False,
        },
        "readiness": {
            "engineering": "READY" if not hard_failures else "BLOCKED",
            "formal": "READY_FOR_EXTERNAL_EXECUTION" if not hard_failures and not formal_blockers else "BLOCKED",
        },
        "hard_failures": hard_failures,
        "formal_blockers": formal_blockers,
        "recommendations": [
            "Run engineering mode when formal capabilities are absent; do not downgrade the formal contract.",
            "Keep workspaces outside installed Skill directories and use external hash anchors.",
        ],
    }
    if output_path:
        write_json(output_path, result)
    return result
