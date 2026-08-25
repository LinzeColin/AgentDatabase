#!/usr/bin/env python3
"""Compatibility entry for Teleiosis v0.0.0.3.

The v0.0.0.2 staged-SHA macro-cycle is retained under
``teleiosis_cycle_v2_legacy.py`` and ``wbi_cycle`` only for regression evidence.
Every public invocation now delegates to the v0.0.0.3 full non-routed
T->C->S->C->P->C controller, where C is the candidate revision itself.
"""
from __future__ import annotations

from teleiosis_run import main

if __name__ == "__main__":
    raise SystemExit(main())
