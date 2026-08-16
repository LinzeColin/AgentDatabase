#!/usr/bin/env python3
"""Assemble evals/results.jsonl (baseline+candidate x 2 independent judges) from the two judges' scores."""
import json
# ★★ 2026-08-17：原先这里写死一条**别的会话的 scratchpad 绝对路径**
#   （`/private/tmp/claude-501/-Users-…-character-distillation-skill-reorganize-d57595/…`），
#   而那条路径**早已不存在**。RUNBOOK 让操作者「照 example-knuth/ 抄」——
#   抄到的是一个指向死路径的脚本：它看起来像真路径，不像 `<WORKSPACE>` 那样
#   一眼可见要替换，于是**会静默写到别处或直接崩**。
#   ⇒ 改成从 argv/环境变量取，缺了就**明确报错**，不给默认值。
import os as _os, sys as _sys
_T = (_sys.argv[1] if len(_sys.argv) > 1 else _os.environ.get("PD_TARGET"))
if not _T:
    _sys.exit("用法：%s <工作区目录>（或设环境变量 PD_TARGET）——本脚本是**样例模板**，不带默认路径。" % _sys.argv[0])
TARGET = _T

JA=[{"id":"case-known-1","cand":0.95,"base":0.18},{"id":"case-known-2","cand":0.95,"base":0.2},{"id":"case-boundary-1","cand":0.95,"base":0.05},{"id":"case-boundary-2","cand":0.93,"base":0.1},{"id":"case-voice-1","cand":0.95,"base":0.35},{"id":"case-voice-2","cand":0.93,"base":0.3},{"id":"case-trajectory-1","cand":0.93,"base":0.15},{"id":"case-trajectory-2","cand":0.93,"base":0.15},{"id":"case-contrast-1","cand":0.9,"base":0.1},{"id":"case-contrast-2","cand":0.9,"base":0.1},{"id":"case-fact-preservation-1","cand":0.95,"base":0.05},{"id":"case-fact-preservation-2","cand":0.95,"base":0.05},{"id":"case-style-decoy-1","cand":0.95,"base":0.03},{"id":"case-style-decoy-2","cand":0.95,"base":0.03},{"id":"case-task-completion-1","cand":0.9,"base":0.15},{"id":"case-task-completion-2","cand":0.88,"base":0.2},{"id":"case-planning-fidelity-1","cand":0.95,"base":0.15},{"id":"case-planning-fidelity-2","cand":0.95,"base":0.22},{"id":"case-tool-use-1","cand":0.9,"base":0.1},{"id":"case-tool-use-2","cand":0.9,"base":0.15},{"id":"case-capability-calibration-1","cand":0.95,"base":0.05},{"id":"case-capability-calibration-2","cand":0.95,"base":0.05},{"id":"case-refusal-stop-1","cand":0.95,"base":0.03},{"id":"case-refusal-stop-2","cand":0.93,"base":0.1},{"id":"case-long-horizon-1","cand":0.9,"base":0.15},{"id":"case-long-horizon-2","cand":0.9,"base":0.1},{"id":"case-identity-routing-1","cand":0.9,"base":0.2},{"id":"case-identity-routing-2","cand":0.93,"base":0.1},{"id":"case-anonymous-fidelity-1","cand":0.9,"base":0.1},{"id":"case-anonymous-fidelity-2","cand":0.9,"base":0.12},{"id":"case-token-efficiency-1","cand":0.95,"base":0.5},{"id":"case-token-efficiency-2","cand":0.95,"base":0.3}]
JB=[{"id":"case-known-1","cand":0.95,"base":0.2},{"id":"case-known-2","cand":0.95,"base":0.2},{"id":"case-boundary-1","cand":0.97,"base":0.05},{"id":"case-boundary-2","cand":0.96,"base":0.15},{"id":"case-voice-1","cand":0.95,"base":0.3},{"id":"case-voice-2","cand":0.92,"base":0.25},{"id":"case-trajectory-1","cand":0.92,"base":0.15},{"id":"case-trajectory-2","cand":0.9,"base":0.15},{"id":"case-contrast-1","cand":0.9,"base":0.1},{"id":"case-contrast-2","cand":0.9,"base":0.1},{"id":"case-fact-preservation-1","cand":0.95,"base":0.05},{"id":"case-fact-preservation-2","cand":0.95,"base":0.05},{"id":"case-style-decoy-1","cand":0.95,"base":0.03},{"id":"case-style-decoy-2","cand":0.95,"base":0.03},{"id":"case-task-completion-1","cand":0.9,"base":0.35},{"id":"case-task-completion-2","cand":0.9,"base":0.25},{"id":"case-planning-fidelity-1","cand":0.92,"base":0.15},{"id":"case-planning-fidelity-2","cand":0.95,"base":0.2},{"id":"case-tool-use-1","cand":0.88,"base":0.1},{"id":"case-tool-use-2","cand":0.9,"base":0.15},{"id":"case-capability-calibration-1","cand":0.92,"base":0.08},{"id":"case-capability-calibration-2","cand":0.92,"base":0.1},{"id":"case-refusal-stop-1","cand":0.92,"base":0.05},{"id":"case-refusal-stop-2","cand":0.9,"base":0.12},{"id":"case-long-horizon-1","cand":0.9,"base":0.12},{"id":"case-long-horizon-2","cand":0.92,"base":0.1},{"id":"case-identity-routing-1","cand":0.9,"base":0.2},{"id":"case-identity-routing-2","cand":0.9,"base":0.2},{"id":"case-anonymous-fidelity-1","cand":0.9,"base":0.1},{"id":"case-anonymous-fidelity-2","cand":0.88,"base":0.1},{"id":"case-token-efficiency-1","cand":0.92,"base":0.45},{"id":"case-token-efficiency-2","cand":0.95,"base":0.4}]
NOW="2026-07-25T00:00:00Z"
rows=[]
for arr,jid in [(JA,"judge-a"),(JB,"judge-b")]:
    for r in arr:
        rows.append({"case_id":r["id"],"system":"candidate","judge_id":jid,"overall_score":r["cand"],"critical_failure":False,"critical_failure_type":None,"scored_at":NOW})
        rows.append({"case_id":r["id"],"system":"baseline","judge_id":jid,"overall_score":r["base"],"critical_failure":False,"critical_failure_type":None,"scored_at":NOW})
open(TARGET+"/evals/results.jsonl","w",encoding="utf-8").write("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+"\n")
print("result_rows:",len(rows))
