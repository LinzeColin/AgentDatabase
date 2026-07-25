#!/usr/bin/env python3
"""Compatibility facade for the sibling persona-distiller-group registry.

Persona Distiller builds packages. The sibling group Skill is the only
canonical storage, verification, team-card, and routing root.
"""
from __future__ import annotations

import sys
from pathlib import Path

GROUP_SCRIPTS = Path(__file__).resolve().parents[2] / "persona-distiller-group" / "scripts"
if not GROUP_SCRIPTS.is_dir():
    raise RuntimeError(
        "persona-distiller-group is required beside persona-distiller; "
        f"expected {GROUP_SCRIPTS.parent}"
    )
if str(GROUP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(GROUP_SCRIPTS))

from registry_core import *  # noqa: F401,F403,E402
