#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
root=Path(__file__).resolve().parent.parent
required=[root/'SKILL.md',root/'MANIFEST.json',root/'references/contract.md',root/'scripts/export.py']
missing=[str(p) for p in required if not p.is_file()]
if missing: raise SystemExit('缺少 Skill 文件：\n'+'\n'.join(missing))
text=(root/'SKILL.md').read_text(encoding='utf-8')
if not text.startswith('---\n') or not re.search(r'^name:\s*weread-portable-notes\s*$',text,re.M): raise SystemExit('SKILL.md frontmatter 无效')
manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
if manifest.get('name')!='weread-portable-notes' or manifest.get('version')!='0.0.0.1' or manifest.get('taskpackVersion')!='v0.0.0.1.3': raise SystemExit('Skill 清单版本无效')
patterns=[re.compile(r'wrk-[A-Za-z0-9_-]{20,}'),re.compile(r'sk-[A-Za-z0-9]{20,}'),re.compile(r'github_pat_[A-Za-z0-9_]{20,}')]
for p in root.rglob('*'):
    if p.is_file():
        value=p.read_text(encoding='utf-8',errors='ignore')
        for pattern in patterns:
            if pattern.search(value): raise SystemExit(f'发现疑似凭证：{p}')
print('微信读书个人笔记 Skill 安装验证通过：0.0.0.1 / v0.0.0.1.3')
