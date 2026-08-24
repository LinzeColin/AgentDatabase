#!/usr/bin/env python3
"""Compatibility entrypoint: v0.0.0.2 test command now delegates to the v0.0.0.3 integrated suite."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('run_v3_integrated_tests.py')),run_name='__main__')
