#!/usr/bin/env python3
from __future__ import annotations
import os, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; TESTS=ROOT/'tests'

def compile_sources():
    paths=[ROOT/'scripts/wbi_market.py',ROOT/'scripts/wbi_product.py',ROOT/'scripts/teleiosis_cycle.py',ROOT/'scripts/teleiosis_run.py']
    for package in ('wbi_market','wbi_product','wbi_cycle','wbi_engineering','wbi_run'): paths.extend(sorted((ROOT/'scripts'/package).glob('*.py')))
    paths.extend(sorted(TESTS.glob('test_teleiosis_v*.py')))
    for path in paths: compile(path.read_text(encoding='utf-8'),str(path),'exec')
    print(f'✓ v0.0.0.3 Python 语法检查：{len(paths)} 个文件')

def run_doctor(script):
    env=dict(os.environ); env['PYTHONDONTWRITEBYTECODE']='1'; env.setdefault('TERM','dumb'); result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),'doctor','--skill-root',str(ROOT)],cwd=ROOT,env=env,check=False)
    if result.returncode: raise SystemExit(result.returncode)

def main():
    sys.dont_write_bytecode=True; compile_sources(); run_doctor('wbi_market.py'); run_doctor('wbi_product.py')
    suite=unittest.defaultTestLoader.discover(str(TESTS),pattern='test_teleiosis_v*.py'); result=unittest.TextTestRunner(verbosity=2).run(suite); return 0 if result.wasSuccessful() else 1
if __name__=='__main__': raise SystemExit(main())
