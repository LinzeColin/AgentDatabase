#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲判载荷生成 → 不透明编号 + 两侧落进工作区 + **当场跑表面特征泄题门**。

**每人共用这一份，不许再各写各的。**

## 为什么收成共享件

此前每人一份 `build_XX_blind.py`，虽然文件头自称「母版」，
但**工作区路径是写死的**（`workspaces/clara-barton/clara-barton/evals/cases.jsonl`）——
复制出去改漏一处就是静默错。同一个失误类已经在
`assemble_XX_results.py` 上炸过一次（同一处除以 10 做了两遍，
三轮 delta 全差一个数量级）。

## 它替哪几条已知缺陷把关

**① `case_id` 不许把期望行为写在题号上。**
`jl-refusal-stop-01` / `jl-style-decoy-02` 这类题号**直接告诉评委这题该拒答**。
两席在 Lister #108 三轮里共报四次：

> 席 D：「`case_id` 已把期望行为写进名字…**这份盲判并不盲。**」
> 席 E：「`refusal-stop`／`style-decoy`／`token-efficiency` 直接写在 id 里，
>        **两侧都在照名字表演。**」

发给评委的一律是 `q-01`…，套组归属只留在 key 里。

**② 报候选/基线的均长比，不报 A/B 侧的差。**
候选被 `sha256 % 2` 均分到两侧，**A/B 均长必然接近——那是分配方式的产物**，
不是「两个系统长度对等」。Lister 三轮：A/B 侧差 5.5%/0.8%/8.7%，
而真实的候选比基线长 **73%/109%/144%**。

**③ 两侧一起落进工作区。**
`evals/` 里一度只有候选侧，基线只存在于人物工作目录——
**判据造好了、接线好了，却没有数据可判**，只能报「未核（不是通过）」。

**④ ★ 生成即判：当场跑 `check_answer_surface_leak`。**
Barton #117 的格式泄题（一条正则分开 32/32）是**第 3 轮判完之后**
才由席 E 说出来的——三轮判分全部作废在这上面。
**泄题必须拦在派发评委之前，不是拦在判完之后。**
本件默认在落盘后直接跑那道门，未过就**退出 1 且不建议派发**。

## 用法

    python3 build_blind_payload.py --workspace <target> --round-dir round1 \\
        --candidate cb_candidate.json --baseline cb_baseline.json [--prefix cb]
    python3 build_blind_payload.py --self-test
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEAK_CHECKER = HERE / "check_answer_surface_leak.py"
LOC_CHECKER = HERE / "check_quote_locator.py"   # ★ v0.0.0.89：坐标也在生成时把


def assign(cases: dict, cand: dict, base: dict) -> tuple:
    """→ (payload, key)。A/B 由 `sha256(case_id) % 2` 决定，**与内容无关、可复现**。"""
    payload, key = [], {}
    for i, cid in enumerate(sorted(cases), 1):
        if cid not in cand or cid not in base:
            raise SystemExit(f"✗ **缺答案：{cid}**——不是「这题跳过」，是载荷不完整")
        flip = int(hashlib.sha256(cid.encode()).hexdigest(), 16) % 2
        a, b = (cand[cid], base[cid]) if flip == 0 else (base[cid], cand[cid])
        opaque = f"q-{i:02d}"
        key[opaque] = {"A": "candidate" if flip == 0 else "baseline",
                       "B": "baseline" if flip == 0 else "candidate",
                       "case_id": cid}
        payload.append({"case_id": opaque, "question": cases[cid], "A": a, "B": b})
    return payload, key


def length_report(cases: dict, cand: dict, base: dict) -> dict:
    """→ 候选/基线的均长与比值。**A/B 侧的差不在这里，因为那不是该看的数。**"""
    n = len(cases)
    lc = sum(len(cand[c]) for c in cases) / n
    lb = sum(len(base[c]) for c in cases) / n
    return {"n": n, "cand": lc, "base": lb, "ratio_pct": (lc - lb) / max(lb, 1) * 100}


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    cases = {f"xx-refusal-stop-{i:02d}": f"题面 {i}" for i in range(1, 9)}
    cand = {c: "候选答案" * 10 for c in cases}
    base = {c: "基线答案" * 10 for c in cases}

    print("── 正向：题号必须是不透明编号，套组不许出现在发给评委的那份里 ──")
    payload, key = assign(cases, cand, base)
    chk(f"载荷题号形如 {payload[0]['case_id']}（**不是 xx-refusal-stop-01**）",
        all(p["case_id"].startswith("q-") for p in payload))
    blob = json.dumps(payload, ensure_ascii=False)
    chk("载荷里搜不到 refusal-stop 这类会泄期望行为的串", "refusal-stop" not in blob)
    chk("而 key 里留着真 case_id（回查用）",
        all(v["case_id"] in cases for v in key.values()))

    print("── 正向：A/B 分配可复现，同一 case_id 每次都落同一侧 ──")
    _, key2 = assign(cases, cand, base)
    chk("两次生成的 key 逐条相同", key == key2)

    print("── 反向对照 ①：缺一条答案 → 必须退出，不许静默少一题 ──")
    short = {k: v for k, v in cand.items() if k != sorted(cases)[0]}
    try:
        assign(cases, short, base); ok = False
    except SystemExit as e:
        ok = "缺答案" in str(e)
    chk("候选少一题 → SystemExit（**不是「这题跳过」**）", ok)

    print("── ★ 反向对照 ②：长度报的是候选/基线，不是 A/B 侧 ──")
    #   造一组「候选整体长一倍」的：A/B 侧均长会接近，而候选/基线比必须是 +100%
    long_cand = {c: "候选答案" * 20 for c in cases}
    r = length_report(cases, long_cand, base)
    chk(f"候选比基线长 {r['ratio_pct']:+.0f}%（**A/B 侧差在这里根本没被算**）",
        abs(r["ratio_pct"] - 100) < 1)
    pl, ky = assign(cases, long_cand, base)
    a_len = sum(len(p["A"]) for p in pl) / len(pl)
    b_len = sum(len(p["B"]) for p in pl) / len(pl)
    chk(f"同一组数据的 A/B 两侧均长 {a_len:.0f} vs {b_len:.0f}"
        f"——**接近，且这正是它不该被当成「长度对等」的原因**",
        abs(a_len - b_len) / max(b_len, 1) < 0.35)

    print("── 反向对照 ③：泄题门必须存在，缺了不许当成通过 ──")
    chk(f"{LEAK_CHECKER.name} 在", LEAK_CHECKER.is_file())
    chk(f"{LOC_CHECKER.name} 在", LOC_CHECKER.is_file())
    # ★ 反向对照：两道生成时判据必须都在——少一道就等于那一道从没跑过
    chk("两道生成时判据都在（少一道 = 那道从没跑过）",
        LEAK_CHECKER.is_file() and LOC_CHECKER.is_file())

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def locator_gate(cand_path) -> int:
    """引文坐标在**生成时**把关。→ 0 过 / 1 拦。

    ★★ 它**不受 `--skip-leak-check` 影响**——那个旗标按名字只该跳过表面泄题门。
    第一版我把这段接在泄题门之后，而 `--skip-leak-check` 是 `return 0` 早退，
    **实跑才发现这道门永远跑不到**。只看代码不算。

    实测 12 人：长逐字引文 198 条，**缺坐标 66 条（33%）**——
    判据一直在报 ⚠、席 E 也点名过同一批题（「未在本题标出 CR 卷次」
    「图注标『出自全集』而无卷页」），**而它从没被当成缺陷修过**：
    因为它是 ⚠ 不是 error，没有人回头看清单。

    ★ 装在这里而不是把发布门的 ⚠ 改成 error——后者会改动已判过的人的门。
    **这一道只拦新载荷。**

    ★★ 它**不需要语料**：`check_quote_locator` 只看答案里引文附近有没有坐标，
    从不读 raw/。我第一版加了个 `--corpus` 前置条件，于是没给语料时它打印
    「未核（不是通过）」却**返回 0（通过）**——**印的话和做的事相反**。
    条件已删，这道门无条件跑。
    """
    print("\n── 引文坐标门（**派发之前必须过**）──")
    if not LOC_CHECKER.is_file():
        print("⚠ check_quote_locator.py 不在，**引文坐标未核（不是通过）**")
        return 0
    q = subprocess.run([sys.executable, str(LOC_CHECKER), "--answers", str(cand_path)],
                       capture_output=True, text=True)
    print(q.stdout.rstrip())
    if q.returncode != 0:
        print("\n✗ **这份载荷不许派发评委：有逐字引文找不到坐标。**")
        print("  坐标 = 卷/期/页/篇名/图注编号，写在同一段里。")
        print("  「详见那篇论文」不算坐标；「出自全集」不算坐标。")
        print("  ★ 补坐标是**有实质**的改动（读者从此能回查），"
              "与「为过长度门加几个字」性质相反。")
        print("  ★★ 同一段话可能有手稿版与印本版两个措辞（Blackwell #118 实例）"
              "——不带坐标，读者无从知道引的是哪一版。")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", type=pathlib.Path, help="人物工作区（含 evals/cases.jsonl）")
    ap.add_argument("--round-dir", type=pathlib.Path, help="本轮落盘目录")
    ap.add_argument("--candidate", help="{case_id: 候选答案} 的 JSON")
    ap.add_argument("--baseline", help="{case_id: 基线答案} 的 JSON")
    ap.add_argument("--prefix", default="blind", help="落盘文件名前缀")
    ap.add_argument("--baseline-source", default="self-authored-strawman",
                    help="基线来源，透传给泄题门。★ bare-model-run 免长度两条的**拦**"
                         "（仍照报），其余照旧硬拦——见待裁定 ⑭")
    ap.add_argument("--skip-leak-check", action="store_true",
                    help="★ 只在判据本身出问题时用；跳过就等于把泄题拖到判完之后才发现")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.workspace and a.round_dir and a.candidate and a.baseline):
        ap.error("要么 --self-test，要么给齐 --workspace/--round-dir/--candidate/--baseline")

    ev = a.workspace / "evals"
    if not ev.is_dir():
        print(f"✗ **{ev} 不在——工作区路径给错了，没落盘**"); return 3
    cases = {}
    for line in (ev / "cases.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line); cases[r["case_id"]] = r["prompt"]

    cand = json.loads(pathlib.Path(a.candidate).read_text(encoding="utf-8"))
    base = json.loads(pathlib.Path(a.baseline).read_text(encoding="utf-8"))
    payload, key = assign(cases, cand, base)

    a.round_dir.mkdir(parents=True, exist_ok=True)
    _payload_path = a.round_dir / f"{a.prefix}_blind_payload.json"
    _payload_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    # ★★ v0.0.0.117：**冻结指令要求按某个字段打分，而载荷里没有那个字段。**
    #   Mendel #125 第 1 轮**派发之后**才发现：两席都写「给 `candidate` 和 `baseline`
    #   各打一个分」，而载荷里是 `A`／`B`；席 D 另有五处提到 `rubric`，载荷里根本没有。
    #   **派发之后就改不得了**：改指令＝中途换尺子，补载荷＝两席看到不同的东西。
    #   ★ **只报不拦**——「该不该有 rubric」是待裁定 ④，一个不能自行选的口子。
    #     本处只保证：这个不一致**不会再到派发之后才被看见**。
    # ★★ v0.0.0.119：**有几道题，rubric 明说克制才对——而评委看不到 rubric。**
    #   Mendel #125 实测：`gm-known-01` 的 rubric 写「答『不确定／记不得』**可接受**」，
    #   候选照做，**得 −0.1800**；`gm-boundary-01` 写「**顺着答下去即为失败**」，
    #   基线顺着答了，**赢 0.18**。两份冻结 rubric 判候选对、基线错，评委两者都看不到。
    #   ★ **只报不拦，且绝不把这些题剔出去**——去掉不利子集再报数就是为凑数放宽判据。
    # ★★★ v0.0.0.122：**引文真伪，必须在派发之前核——因为评委核不了。**
    #   `check_quote_integrity` 早就支持 `--answers`，**但全项目没有一处这样调用它**。
    #   Mendel #125 补跑：6 条德文引文，**1 条未命中**——
    #   `Einleitende Bemerkungen`，而语料里印的是 OCR 讹字 `Hinleitende Bemerkungen`。
    #   **我把 OCR 错字改正后当逐字引文用了**，正是该件文件头点名的那一类。
    #   两席都没抓到（席 D 反而给了那一题全场最高的 0.93）——**评委没有语料，核不了。**
    _qi = pathlib.Path(__file__).resolve().parent / "check_quote_integrity.py"
    _src = pathlib.Path(a.workspace) / "references" / "sources"
    if _qi.is_file() and a.candidate and _src.is_dir():
        print("\n── 引文真伪：拿答案里的原文去语料里逐字找（**只报不拦**）──")
        _rq = subprocess.run([sys.executable, str(_qi), "--answers", a.candidate,
                              "--cache", str(_src)], capture_output=True, text=True)
        for _ln in _rq.stdout.splitlines():
            if any(k in _ln for k in ("引文", "未命中", "⚠", "语料")):
                print("  " + _ln.strip())
        print("  ★ 未命中不等于伪造，但**「改了 OCR 错字再当逐字引文用」也落在这里**——"
              "那一类是真问题，且评委查不出来。")

    # ★★ v0.0.0.121：**每修一处引入一处，连续两轮四个实例**（见 _fix-introduces-new-defect.md）。
    #   R2 修 contrast 引入「至今未见数字化本」；R3 修 task-completion 引入「同一卷」而全篇无卷次。
    #   修完之后**没有任何一步去验改的那一处自己站不站得住**，要等下一轮评委再抓。
    _oc = pathlib.Path(__file__).resolve().parent / "check_answer_overclaims.py"
    if _oc.is_file() and a.candidate and pathlib.Path(a.candidate).is_file():
        print("\n── 候选答案的两类过度断言（**只报不拦**）──")
        _ro = subprocess.run([sys.executable, str(_oc), "--answers", a.candidate],
                             capture_output=True, text=True)
        try:
            _io = json.loads(_ro.stdout)
            _no = _io.get("**报出**", 0)
            if _no:
                for _h in _io.get("逐条", []):
                    print(f"  ⚠ {_h['case_id']}　{_h['类']}（{_h['触发词']}）")
                    print(f"      {_h['句']}")
            else:
                print("  ✓ 已故人物谈当下／指代悬空　各 0 处")
            print("  ★ 本件判不了：「原文写的」后面的断言是否真在引文里、译文是否比原文宽")
        except Exception as _eo:                                 # noqa: BLE001
            print(f"  ⚠ 输出无法解析，**未核（不是通过）**：{_eo}")

    _here0 = pathlib.Path(__file__).resolve().parent
    _rw = _here0 / "check_restraint_without_remainder.py"
    _cases = pathlib.Path(a.workspace) / "evals" / "cases.jsonl"
    if _rw.is_file() and _cases.is_file():
        print("\n── rubric 要求克制、而评委看不到 rubric（**只报不拦**）──")
        _r0 = subprocess.run([sys.executable, str(_rw), "--cases", str(_cases)],
                             capture_output=True, text=True)
        try:
            _i0 = json.loads(_r0.stdout)
            _n0 = _i0.get("**rubric 把克制指定为正确行为的题**", 0)
            print(f"  {_n0} / {_i0.get('题数')} 题的 rubric 把克制指定为正确行为")
            for _h in _i0.get("逐题（按实测 delta 升序）", []):
                print(f"      {_h['套组']}")
            if _n0:
                print("      ★ 评委按题面判「谁更合题」，**克制在这些题上天然吃亏**。"
                      "这是待裁定 ④，本件不替它选。")
        except Exception as _e0:                                 # noqa: BLE001
            print(f"  ⚠ 输出无法解析，**未核（不是通过）**：{_e0}")

    _here = pathlib.Path(__file__).resolve().parent
    _jm = _here / "check_judge_prompt_matches_payload.py"
    _pdir = _here.parent / "references" / "pipeline" / "judge_prompts"
    _prompts = sorted(_pdir.glob("seat_*.md")) if _pdir.is_dir() else []
    if _jm.is_file() and _prompts:
        print("\n── 评委指令 vs 载荷字段（**只报不拦**）──")
        _argv = [sys.executable, str(_jm), "--payload", str(_payload_path)]
        for _pp in _prompts:
            _argv += ["--prompt", str(_pp)]
        _r = subprocess.run(_argv, capture_output=True, text=True)
        try:
            _info = json.loads(_r.stdout)
            _n = _info.get("**对不上的字段数**", 0)
            if _n:
                print(f"  ⚠⚠ **指令引到而载荷里没有的字段：{_n} 处**")
                for _row in _info.get("逐席", []):
                    if _row.get("**载荷里没有的**"):
                        print(f"      {_row['指令']}：{_row['**载荷里没有的**']}")
                print("      ★ 评委拿不到这些字段，只能按题面自拟判据。"
                      "**派发前知道，比派发后才发现强。**")
            else:
                print("  ✓ 指令引到的字段，载荷里都有")
        except Exception as _exc:                                # noqa: BLE001
            print(f"  ⚠ 输出无法解析，**未核（不是通过）**：{_exc}")
    (a.round_dir / f"{a.prefix}_blind_key.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")

    # ★ 两侧一起落进工作区——**门看不见的东西，等于没做。**
    cand_path = ev / "judge_payload.v1.json"
    base_path = ev / "baseline.v1.json"
    cand_path.write_text(json.dumps({c: cand[c] for c in cases}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    base_path.write_text(json.dumps({c: base[c] for c in cases}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"★ 候选与基线两侧已落进 {ev}/——发布门现在看得见它们")

    # 轮次之间 A/B 映射必须一致，否则各轮不可比
    r1 = a.round_dir.parent / "round1" / f"{a.prefix}_blind_key.json"
    if a.round_dir.name != "round1" and r1.is_file():
        if json.loads(r1.read_text(encoding="utf-8")) != key:
            print("✗ **A/B 映射与第 1 轮不一致——中止（轮次之间不可比）**"); return 3
        print("A/B 映射与第 1 轮逐条一致 ✅")
        # ★★ 把这个设计的**代价**一起说出来——上面那句注释只写了收益。
        #   ★ 翻转率**由判据算**，不是我写死的一句话：
        #     check_blind_rounds_independent 此前从未被任何代码调用过。
        rk = HERE / "check_blind_rounds_independent.py"
        if rk.is_file():
            q = subprocess.run([sys.executable, str(rk), "--keys", str(r1),
                                str(a.round_dir / f"{a.prefix}_blind_key.json")],
                               capture_output=True, text=True)
            for line in (q.stdout or "").splitlines():
                if line.strip():
                    print("  " + line.strip())
        else:
            print("  ⚠ check_blind_rounds_independent.py 不在，**翻转率未核（不是通过）**")
        print("    两席已实测能靠格式/长度认出候选侧（Barton 100%，四人合计 91%），"
              "**第 1 轮认出的边在后两轮原样有效**——")
        print("    所以「三轮 delta 逐轮向零」这类跨轮趋势"
              "**不宜当三个独立样本读**。（权衡不是缺陷，待裁定 ⑦）")

    r = length_report(cases, cand, base)
    print(f"{r['n']} 对；A 侧是候选的题数 "
          f"{sum(1 for v in key.values() if v['A'] == 'candidate')}")
    print(f"★ **候选均长 {r['cand']:.0f}，基线均长 {r['base']:.0f}"
          f"——候选比基线长 {r['ratio_pct']:+.0f}%**")
    print("  （A/B 两侧的均长差**不是**该看的数：候选被均分到两侧，"
          "两侧接近是分配方式的产物）")
    print("★ 题号已改为不透明编号 q-01…（套组归属只在 key 里）")

    # ★★ 生成即判：泄题必须拦在派发评委之前
    if locator_gate(cand_path):                  # ★ 在早退之前——它不该被 skip 掉
        return 1
    if a.skip_leak_check:
        print("\n⚠ **跳过了表面特征泄题门**——"
              "Barton #117 三轮判分正是因为这道门没在派发前跑而全部作废")
        return 0
    print("\n── 表面特征泄题门（**派发之前必须过**）──")
    p = subprocess.run([sys.executable, str(LEAK_CHECKER),
                        "--candidate", str(cand_path), "--baseline", str(base_path),
                        "--baseline-source", a.baseline_source],
                       capture_output=True, text=True)
    print(p.stdout.rstrip())
    if p.returncode != 0:
        print("\n✗ **这份载荷不许派发评委。** 判出来的 delta 不能当作盲判结果引用——"
              "重写答案，不要改门。")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
