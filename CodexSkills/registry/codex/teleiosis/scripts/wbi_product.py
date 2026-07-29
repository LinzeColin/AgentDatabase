#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path: sys.path.insert(0,str(SCRIPT_DIR))
from wbi_product.common import ProductRealityError, read_json, write_json
from wbi_product.contracts import REQUIRED_CAPABILITIES, validate_product_reality_run
from wbi_product.gate import evaluate_product_reality

SKILL_ROOT=SCRIPT_DIR.parent

def emit(value): print(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True))

def doctor(root:Path):
    required=[
      root/'VERSION', root/'SKILL.md', root/'README.md', root/'scripts/teleiosis_cycle.py',
      root/'scripts/wbi_product.py', root/'scripts/wbi_product/gate.py',
      root/'assets/product/templates/product_reality_run.example.json',
      root/'references/product/ARCHITECTURE.md', root/'references/FULL_RUN_CONTRACT.md',
      root/'schemas/shared/CandidateIdentity.schema.json',
    ]
    errors=[f"缺少 {p.relative_to(root)}" for p in required if not p.is_file()]
    version=(root/'VERSION').read_text(encoding='utf-8').strip() if (root/'VERSION').is_file() else None
    if version != 'v0.0.0.3': errors.append(f"VERSION 必须为 v0.0.0.3，实际 {version}")
    skill=(root/'SKILL.md').read_text(encoding='utf-8') if (root/'SKILL.md').is_file() else ''
    for marker in ('T1 -> C1 -> S1 -> C2 -> P1 -> C3','FULL_NO_ROUTING','Product Reality Lab'):
        if marker not in skill: errors.append(f"SKILL.md 缺少合同标记: {marker}")
    return {'valid':not errors,'errors':errors,'version':version,'capability_count':len(REQUIRED_CAPABILITIES)}

def main():
    ap=argparse.ArgumentParser(description='Teleiosis v0.0.0.3 Product Reality Lab 内嵌证据引擎')
    sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('validate'); p.add_argument('--input',required=True); p.add_argument('--output')
    p=sub.add_parser('gate'); p.add_argument('--input',required=True); p.add_argument('--output',required=True); p.add_argument('--allow-no-field',action='store_true')
    p=sub.add_parser('doctor'); p.add_argument('--skill-root',default=str(SKILL_ROOT))
    p=sub.add_parser('capabilities'); p.add_argument('--output')
    args=ap.parse_args()
    try:
        if args.command=='validate':
            value=read_json(Path(args.input)); errors=validate_product_reality_run(value); result={'valid':not errors,'errors':errors}
            if args.output: write_json(Path(args.output),result)
            emit(result); return 0 if not errors else 2
        if args.command=='gate':
            result=evaluate_product_reality(read_json(Path(args.input)),require_field=not args.allow_no_field); write_json(Path(args.output),result); emit(result); return 0 if result['state']!='BLOCKED' else 2
        if args.command=='doctor':
            result=doctor(Path(args.skill_root).resolve()); emit(result); return 0 if result['valid'] else 2
        result={'schema_version':'teleiosis.product_capabilities.v1','scope_mode':'FULL_NO_ROUTING','capabilities':sorted(REQUIRED_CAPABILITIES)}
        if args.output: write_json(Path(args.output),result)
        emit(result); return 0
    except ProductRealityError as exc:
        emit({'state':'BLOCKED','error':str(exc)}); return 2
if __name__=='__main__': raise SystemExit(main())
