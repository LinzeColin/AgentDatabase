#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile 缺席时两件判据回退到不同档 —— 本测钉住「至少要说出来」。"""
import json, pathlib, subprocess, sys, tempfile, shutil
import subprocess as _sp
_r = _sp.run(["git", "-C", str(pathlib.Path(__file__).resolve().parent),
              "rev-parse", "--show-toplevel"], capture_output=True, text=True)
REPO = pathlib.Path(_r.stdout.strip()) if _r.returncode == 0 else pathlib.Path(".").resolve()
PD = REPO / "CodexSkills/registry/codex/persona-distiller"
QC = PD / "scripts/quality_check.py"
sys.path.insert(0, str(PD / "scripts"))
from common import PROFILE_THRESHOLDS

bad = []
def chk(lbl, ok):
    print(("  ✓ " if ok else "  ✗ ") + lbl)
    if not ok: bad.append(lbl)

# ① 两个默认值确实不同 —— 这是本测存在的理由
src_qc = (PD / "scripts/quality_check.py").read_text(encoding="utf-8")
src_cf = (PD / "scripts/check_corpus_feasibility.py").read_text(encoding="utf-8")
chk("★★★ quality_check 缺 profile 回退 **standard**",
    "meta.get('profile')" in src_qc and "or 'standard'" in src_qc)
chk("★★★ check_corpus_feasibility 缺 profile 回退 **quick**",
    "profile = 'quick'" in src_cf)
chk("★★★ 两档的 min_sources 确实不同（%d vs %d）"
    % (PROFILE_THRESHOLDS['standard']['min_sources'], PROFILE_THRESHOLDS['quick']['min_sources']),
    PROFILE_THRESHOLDS['standard']['min_sources'] != PROFILE_THRESHOLDS['quick']['min_sources'])

sys.path.insert(0, str(REPO / "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline"))
from workspace_roots import iter_workspaces, CORPORA
by = {w.name: w for w in iter_workspaces(CORPORA)}

def fallback_note(ws):
    r = subprocess.run([sys.executable, str(QC), str(ws), "--phase", "research"],
                       capture_output=True, text=True, timeout=900)
    o = r.stdout + r.stderr
    d = json.loads(o[o.find("{"):]) if "{" in o else {}
    return d.get("metrics", {}).get("profile_fallback"), d.get("profile")

n, p = fallback_note(by["winston-churchill"])
chk("★★★ 缺 profile 的工作区 → **印出回退提示**（churchill）", bool(n) and p == "standard")
chk("★★★ 提示里要同时点出**两个档的门槛**（否则读者看不出差多少）",
    bool(n) and "24" in n and "8" in n and "quick" in n)
n2, p2 = fallback_note(by["robert-koch"])
chk("★★ 反对照：**meta 里写了 profile 的不许印回退提示**（koch=deep）",
    n2 is None and p2 == "deep")
print("\n自测 %d/%d" % (6 - len(bad), 6))
sys.exit(1 if bad else 0)
