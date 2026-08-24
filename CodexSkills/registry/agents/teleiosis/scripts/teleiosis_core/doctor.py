from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Any, Dict

from .common import PACKAGE_ROOT, VERSION, TeleiosisError, canonical_json_hash
from .integrity import verify_release
from .regression import validate_corpus
from .skill_audit import validate_three_passes
from .review import validate_reviews
from .taskpack import fresh_builder_simulation, validate_taskpack


def doctor(root: Path = PACKAGE_ROOT) -> Dict[str, Any]:
    if sys.version_info < (3, 9):
        raise TeleiosisError("PYTHON_TOO_OLD", "Teleiosis 需要 Python 3.9 或更高版本。", {"actual": platform.python_version()})
    checks: Dict[str, Any] = {
        "release": verify_release(root, strict=True),
        "taskpack": validate_taskpack(root),
        "skill_audit": validate_three_passes(root),
        "reviews": validate_reviews(root),
        "fresh_builder": fresh_builder_simulation(root),
        "regression": validate_corpus(root / "fixtures/regression/teleiosis-v5-regression.jsonl"),
    }
    result = {
        "schema_version": "teleiosis.doctor.v5",
        "status": "PASS",
        "version": VERSION,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "checks": checks,
        "next_command": "python3 START_HERE.py install",
        "message_zh": "包已通过完整本地体检，可直接安装；正式 PASS 仍由外部独立 Verifier 决定。",
    }
    result["doctor_hash"] = canonical_json_hash(result)
    return result
