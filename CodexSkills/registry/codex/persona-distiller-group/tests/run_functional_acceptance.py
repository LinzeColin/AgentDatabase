#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run functional acceptance for the expert-team candidate.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    test_dir = Path(__file__).resolve().parent
    command = [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir), "-p", "test_*.py", "-v"]
    completed = subprocess.run(command, text=True, capture_output=True)
    result = {
        "schema_version": "persona-team.functional-acceptance.v1",
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
        "scope": [
            "four owner-frozen modes and seat ranges",
            "mandatory hypothesis/adversary/review/judge/synthesis controls",
            "route-to-dossier subject_slug continuity",
            "real nested runtime payload loading",
            "C-to-B calibration fallback",
            "95 target and 75 floor score contract",
        ],
        "limitations": [
            "Synthetic registry fixtures prove candidate mechanics, not production Persona quality.",
            "Native commercial competitor runs, production blind tasks and external verifier remain separate gates.",
        ],
    }

    # ★★★ 2026-08-18：**真跑一次**模式档位可达性，把数字写进验收记录。
    #   为什么要在这里跑：`test_all_selftests_have_a_runner.py` 只会收编它的
    #   `--self-test`（判定逻辑对不对），**不会拿真名册跑一遍**（当前语料够不够得到各档）。
    #   一件判据可以同时「被调用」和「从没对现实跑过」。
    #   ★ **只披露，不改退出码** —— 「2 档不可达」是已知状态、且改门槛需要本件
    #     给不了的证据（多人是否真的更好）。不许因为过不了门而卡住流程。
    # ★★ 版本绑定是**硬门**（今天两次抓到漏改 manifest.json.version）——
    #   它便宜、确定，且版本漂移是真错，不该只当披露。
    vb = test_dir.parent / "scripts" / "check_group_version_binding.py"
    if vb.is_file():
        vr = subprocess.run([sys.executable, str(vb)], text=True, capture_output=True)
        result["version_binding"] = {"returncode": vr.returncode,
                                     "verdict": "bound" if vr.returncode == 0 else "DRIFT"}
        if vr.returncode != 0:
            result["status"] = "FAIL"
            print("── 版本绑定 **红** ──\n" + (vr.stdout or "")[-600:])
    # ★ 名册独立性：它自己声明「恒为 0，只报不判」⇒ 披露，不参与 status
    ri = test_dir.parent / "scripts" / "check_roster_independence.py"
    if ri.is_file():
        rr2 = subprocess.run([sys.executable, str(ri)], text=True, capture_output=True)
        tail2 = [ln for ln in (rr2.stdout or "").splitlines() if ln.strip()]
        result["roster_independence"] = {"returncode": rr2.returncode,
                                         "summary": tail2[-3:] if tail2 else []}

    reach_script = test_dir.parent / "scripts" / "check_mode_ladder_reachable.py"
    if reach_script.is_file():
        rr = subprocess.run([sys.executable, str(reach_script)], text=True, capture_output=True)
        tail = [ln for ln in (rr.stdout or "").splitlines() if ln.strip()]
        result["mode_ladder_reachability"] = {
            "returncode": rr.returncode,
            "verdict": "all modes reachable" if rr.returncode == 0
                       else ("some modes unreachable" if rr.returncode == 1 else "not measured"),
            "summary": [ln for ln in tail if ("不可达" in ln or "够不到" in ln or "实际落到各档" in ln)][:8],
            "note": "披露项，不参与 status —— 改门槛需要「多人是否真的比单人好」的证据，"
                    "而遥测尚未标定（sample_count=1）。",
        }
        print("── 模式档位可达性（披露，不参与 status）──")
        for ln in result["mode_ladder_reachability"]["summary"]:
            print("   " + ln)
    else:
        result["mode_ladder_reachability"] = {"returncode": None, "verdict": "not measured",
                                              "note": "找不到 check_mode_ladder_reachable.py"}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "returncode": completed.returncode}, ensure_ascii=False))
    if completed.stdout:
        print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    # ★★★ 2026-08-18：退出码必须**与 `status` 一致**。
    #   原来无条件 `return completed.returncode`（只反映 unittest），
    #   于是我新加的版本绑定硬门把 `status` 置成 FAIL、也打印了红，
    #   而 **rc 仍是 0** —— 反例实验（故意写坏 VERSION）当场抓到：
    #   `{"status": "FAIL", "returncode": 0}`。看 rc 的调用方会读成绿。
    #   [[verdict-computed-before-the-corrections]]｜[[pipe-to-tail-hides-the-exit-code]]
    if result["status"] == "FAIL" and completed.returncode == 0:
        return 1
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
