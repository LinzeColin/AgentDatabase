#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disclosures must survive all the way to the artifact the host executes.

Why this file exists
--------------------
Three disclosures were added to this skill on 2026-08-17 -- no-domain-signal,
telemetry location, divergence detectability -- and each was verified on the
script that produces it. All three then failed to appear in
`execution-contract.json`, which is the file the host agent actually runs
against. Verified single commands; never verified the chain.

That gap was not cosmetic. `user_output_contract.show` already instructs the
host to surface "material disagreements". Handed `documented_divergences: []`
with no denominator beside it, the honest thing for the host to write is "the
experts agreed" -- asserting something that was never measured. The pseudo-
consensus the Owner flagged was being manufactured at that exact line.

So this test runs the **real user entry point** (`run_team_pipeline.py`) end to
end and asserts on the *final* artifacts, not on intermediate ones. It checks
both directions: a task with a domain signal must NOT carry a caveat, and a
task without one must.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"

# A task whose vocabulary the roster covers, and one it does not.
WITH_SIGNAL = "Our CI pipeline is flaky and the API keeps timing out."
WITHOUT_SIGNAL = "Plan the choreography and lighting cues for the ballet."

# (artifact, dotted path) that must exist on every run.
REQUIRED = [
    ("route-plan.json", "routing_observability.domain_signal_present"),
    ("route-plan.json", "routing_observability.ranking_driver"),
    ("route-plan.json", "routing_observability.telemetry_path"),
    ("route-plan.json", "routing_observability.telemetry_file_present"),
    ("team-dossier.json", "divergence_detectability.members_carrying_divergence_map"),
    ("team-dossier.json", "divergence_detectability.note"),
    # The three below are the ones that were missing: same facts, but in the
    # file the host executes.
    ("execution-contract.json", "divergence_detectability.note"),
    ("execution-contract.json", "selection_caveats"),
    ("execution-contract.json", "user_output_contract.phrasing_rules"),
    # ★★ 第二轮补的。上午修完前三条我宣称「这一类收干净了」，随后对合同里每一条
    #    「不得／只允许」做系统扫描，在**并列的兄弟链**上又找到这两条：
    #    `separation_protocol`（六条隔离规则，只能由宿主执行）同样只活在 route-plan；
    #    `team_composition`（Swarm 不得用重复意见凑人数的分母）此前**根本不存在**。
    #    「这一类收干净了」说之前先数出口个数 —— 我说过，又错了一次。
    ("execution-contract.json", "separation_protocol"),
    ("execution-contract.json", "team_composition.largest_family_share"),
]


def dig(doc, dotted):
    cur = doc
    for key in dotted.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return None, False
        cur = cur[key]
    return cur, True


def run_pipeline(task, workdir):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "run_team_pipeline.py"),
         "--task", task, "--registry-root", str(ROOT), "--workdir", str(workdir)],
        capture_output=True, text=True)


def main() -> int:
    bad = []
    with tempfile.TemporaryDirectory() as td:
        wd = pathlib.Path(td) / "with"
        wd.mkdir()
        out = run_pipeline(WITH_SIGNAL, wd)
        if out.returncode != 0:
            bad.append("pipeline failed rc=%d: %s" % (out.returncode, out.stderr.strip()[:300]))
        else:
            docs = {}
            for name in ("route-plan.json", "team-dossier.json", "execution-contract.json"):
                f = wd / name
                if not f.is_file():
                    bad.append("%s was not produced" % name)
                else:
                    docs[name] = json.loads(f.read_text(encoding="utf-8"))
            for name, dotted in REQUIRED:
                if name not in docs:
                    continue
                _, ok = dig(docs[name], dotted)
                if not ok:
                    bad.append("%s is missing %s" % (name, dotted))
            # 六条隔离规则必须**逐条**到齐，不是「有这个键」就算数
            contract = docs.get("execution-contract.json", {})
            sep = contract.get("separation_protocol") or []
            if len(sep) != len(json.loads((wd / "route-plan.json").read_text(encoding="utf-8"))
                              .get("separation_protocol", [])):
                bad.append("separation_protocol 条数与 route-plan 不一致：合同 %d 条" % len(sep))
            if not any("cannot review their own" in x for x in sep):
                bad.append("合同里没有「生成者不得复审自己」这一条：%r" % sep[:2])

            # ★ 校准状态必须到达合同顶层。manifest 把架构写作 C-calibrated-MoE，
            #   而 2026-08-17 实测结果遥测 **0 条** —— 路由内部对此诚实
            #   （samples<5 → prior 0.0 并附 reason），但那句话只在每个候选的
            #   meta 里，**没有一处到达消费者读的合同**。这里钉住它。
            cal = contract.get("calibration_status")
            if not isinstance(cal, dict):
                bad.append("execution-contract 缺 calibration_status")
            else:
                if "calibrated" not in cal:
                    bad.append("calibration_status 没说 calibrated 与否：%r" % cal)
                elif cal.get("calibrated") is False and not cal.get("note"):
                    bad.append("未校准却没有写明这意味着什么（note 为空）")
                if cal.get("calibrated") is False and cal.get(
                        "outcome_samples_behind_those_priors") != 0:
                    bad.append("说未校准，样本数却非 0：%r" % cal)

            # A task the roster covers must not claim it was picked blind.
            if contract.get("selection_caveats"):
                bad.append("a task WITH a domain signal must have no selection caveat, got %r"
                           % contract["selection_caveats"])

        # ── The other direction. A caveat that never fires is not a caveat. ──
        wd2 = pathlib.Path(td) / "without"
        wd2.mkdir()
        out2 = run_pipeline(WITHOUT_SIGNAL, wd2)
        if out2.returncode != 0:
            bad.append("pipeline failed on the no-signal task rc=%d: %s"
                       % (out2.returncode, out2.stderr.strip()[:300]))
        else:
            contract2 = json.loads((wd2 / "execution-contract.json").read_text(encoding="utf-8"))
            caveats = contract2.get("selection_caveats") or []
            if not caveats:
                bad.append("a task with NO domain signal must carry a selection caveat "
                           "into the execution contract, got []")
            elif not any("NO DOMAIN SIGNAL" in c for c in caveats):
                bad.append("caveat did not name the condition: %r" % caveats)

    for b in bad:
        print("  x " + b)
    print("disclosures-reach-the-contract %s" % ("FAIL" if bad else "OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
