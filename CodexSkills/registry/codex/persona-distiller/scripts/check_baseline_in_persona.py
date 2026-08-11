#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**基线入戏门**：对照臂必须也在扮演这个人，否则 delta 测的不是产物。

## 触发实例（2026-08-12 全库实测）

追「那 8 个负 delta 的人为什么负」时，把 delta 拆成两条臂的**绝对分**，
发现分开正负两组的几乎全在**对照臂**（候选侧差 +0.0522、对照侧差 −0.1085）。
顺着对照臂看编号，撞见一处台阶：

| 批次 | 人 | 题 | 候选臂均 | **对照臂均** | delta 区间 |
|---|---:|---:|---:|---:|---|
| #101–104 | 4 | 32 | 0.7929 | **0.8353** | −0.1456 … +0.0156 |
| #106–112 | 7 | 32 | 0.8249 | **0.7170** | +0.0803 … +0.1364 |

同一族、同一套题、连号，而 **delta 区间完全不重叠**；
两批的**候选臂只差 +0.0320，对照臂差 −0.1183**。

去读原文，一眼就看见了——**两批的对照臂不是同一种东西**：

- #101–104 是**入戏第一人称**
  「**我**确曾把昆虫的生成写成一批稿子……1642 年那里被劫，纸稿散尽。」（Harvey）
- #106–112 是**第三人称百科口吻，直呼其名**
  「……是**南丁格尔**最广为流传的著作。」（Nightingale）
  「**科赫**在细菌学早期就重视显微摄影，**他**把照相作为记录细菌形态的手段。」（Koch）

⇒ 那一批的基线**根本没被要求扮演这个人**，它在回答「介绍一下 X」。
  拿「扮演 X」去比「介绍 X」，赢的是任务差异，不是产物。

## 代价

这 7 个读数是当时 22 个可用读数里的 7 个，**14 个正读数里的 7 个**，
并且是 **+0.08 以上那 10 个里的 7 个**。剔掉之后：

| | 剔之前 | 剔之后 |
|---|---:|---:|
| 中位 delta | +0.0300 | **−0.0003** |
| delta > 0 | 14/22 | **7/15** |
| 过 deep 门 0.07 | 10 | **3** |

★ 幸而**这 7 人一个都没入库**（医疗护理师族目录下只有 `_category.json`）——
  没有已交付产物依赖这批被抬高的读数。

## 判据（**这是筛查器，不是判决**）

按**整份载荷**算第一人称覆盖率 = 含「我」的答案数 ÷ 答案总数，
低于 `LOW` 记为候选，**要人去读**。

### 为什么按整份算，不按单条算

中文成句常省主语。Harvey 那份里 `hv-decoy-01`
「没那么干脆。1616 年那册笔记里，确有一句说心的构造使血不断经肺送入大动脉——」
**通篇没有「我」，却完全是入戏的**。单条判会把它误杀。
整份 32 条里只有 8 条无「我」，覆盖率 0.750，一眼就与 0.062 的那批分开。

### ★ 这个阈值是**拟合出来的**，不是先验的

下面那个 `LOW` 常量（四成）是在 22 个已判分人物上定的：
（★ 正文里**不写它的字面量**——2026-08-12 做变异测试时，
  `sed 's/LOW = 0.40/LOW = 0.0/'` 替中的是这段散文而不是代码，
  变异体因此与原件行为相同、rc=0，我差点读成「这条断言不承力」。
  [[counter-example-red-can-be-red-by-coincidence]] 的又一种：**变异根本没造成。**）
不入戏那 7 个的覆盖率是 0.062–0.250，其余 15 个是 0.438–1.000
（最低的 0.438 是 Galen #101，读过，**是入戏的**）。
中间那段空白里任取一点都能把这 22 个分对——**所以它对这 22 个必然准**，
对第 23 个人没有保证。它只负责把可疑的挑出来给人读。

### 本件**不**查「直呼其名」

那才是最直接的证据（「是南丁格尔最广为流传的著作」），但正文是中文而
`meta.json` 里只有英文名（`name: "Robert Koch"`），
按英文名去中文正文里搜是搜不到的，硬编中文译名又会撞
[[namesakes-whose-works-are-also-public-domain]] 那一类的坑。
**姓名式判别留给读的人**，本件只管把该读的挑出来。

用法：

    python3 check_baseline_in_persona.py <载荷.json> [更多载荷…]
    python3 check_baseline_in_persona.py --self-test

退出码：0 无候选｜1 有候选（要人读）｜2 **一条答案都没扫到——未核验，不是通过**｜3 用法错
"""
from __future__ import annotations

import json
import pathlib
import sys

# 第一人称标记。只用「我」——「吾」「余」在文言人物里出现，但它们同时是
# 第三人称叙述里的引文标记，加进来反而糊。宁可窄。
FIRST_PERSON = "我"

# 覆盖率低于此值 → 候选。**拟合值，见 docstring。**
LOW = 0.40


def iter_answers(data):
    """把一份判分／基线载荷摊成 `(case_id, 答案文本)`。

    ★ 本项目的载荷有三种形状，这段逻辑与 `check_refusal_overflow.iter_answers`
      **是重复的**。明知重复仍然重复，理由：跨文件 import 在
      `quality_check` 用 `spec_from_file_location` 装载时**不会**把 scripts/
      放进 `sys.path`，那条路会在真跑的时候炸 NameError 而三道静态检查都碰不到
      （[[a-checker-nothing-calls-is-not-a-checker]] 第五批就是这么来的）。
      三种形状各有一条自测钉着，改了一边另一边会红。
    """
    if isinstance(data, dict):
        # 扁平：{"hg-known-01": "…"}（16 题这一代）
        # 字典套字典：{"hg-known-01": {"baseline": "…"}}
        for cid, val in data.items():
            if isinstance(val, str):
                yield str(cid), val
            elif isinstance(val, dict):
                for key in ("baseline", "answer", "text", "response", "output"):
                    if isinstance(val.get(key), str):
                        yield str(cid), val[key]
                        break
    elif isinstance(data, list):
        # 行式：[{"case_id": …, "baseline": "…"}]（32 题一代）
        for row in data:
            if not isinstance(row, dict):
                continue
            cid = str(row.get("case_id") or row.get("id") or "")
            for key in ("baseline", "answer", "text", "response", "output"):
                if isinstance(row.get(key), str):
                    yield cid, row[key]
                    break


def scan_payload(path: pathlib.Path) -> dict:
    """读一份载荷 → `{总数, 含第一人称数, 覆盖率, 无第一人称的 case_id}`。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {"错": f"读不了：{exc}"}
    except ValueError as exc:
        return {"错": f"不是 JSON：{exc}"}
    pairs = list(iter_answers(data))
    without = [cid for cid, text in pairs if FIRST_PERSON not in text]
    return {
        "总数": len(pairs),
        "含第一人称": len(pairs) - len(without),
        "覆盖率": (len(pairs) - len(without)) / len(pairs) if pairs else 0.0,
        "无第一人称的": without,
    }


def judge_payload(stat: dict) -> dict:
    """按整份载荷判：候选／无候选／未核验。**不判单条。**"""
    if "错" in stat:
        return {"状态": f"**未核验**：{stat['错']}", "候选": False, "未核验": True}
    if stat["总数"] == 0:
        return {"状态": "**摊出 0 条答案——未核验，不是通过**"
                        "（形状对不上？扁平 `{cid: 文本}` / 行式 `[{case_id, baseline}]`）",
                "候选": False, "未核验": True}
    if stat["覆盖率"] < LOW:
        return {"状态": f"**候选：基线可能不入戏**（第一人称覆盖率 {stat['覆盖率']:.3f} < {LOW}）",
                "候选": True, "未核验": False}
    return {"状态": f"无候选（第一人称覆盖率 {stat['覆盖率']:.3f}）",
            "候选": False, "未核验": False}


# ── 负对照 ────────────────────────────────────────────────────────────
def self_test() -> int:
    fails = []

    def chk(msg, ok):
        print(f"  {'✓' if ok else '✗'} {msg}")
        if not ok:
            fails.append(msg)

    import tempfile

    # ★ 夹具全部照抄仓里的真实答案（[[fixtures-cleaner-than-the-real-thing]]）。
    #   入戏那三条取自 Harvey #103，**其中第三条通篇没有「我」而仍是入戏的**。
    IN = {
        "hv-known-01": "有过，但它不在了。我确曾把昆虫的生成写成一批稿子，"
                       "与论生成的其余札记一并存在白厅的住处。1642 年那里被劫，纸稿散尽。",
        "hv-boundary-01": "这我不能答。我隔着纸看不见你，摸不到你的脉，"
                          "也听不出你心跳的强弱快慢——我一生的规矩是不见的东西不下断语。",
        "hv-decoy-01": "没那么干脆。1616 年那册笔记里，确有一句说心的构造使血不断经肺"
                       "送入大动脉——方向是对的，但那还不是循环。",
    }
    #   不入戏那四条取自 #107/#109/#110/#112，一律第三人称直呼其名。
    OUT = {
        "rk-known-01": "是的。科赫在细菌学早期就重视显微摄影，他把照相作为记录细菌形态的手段，"
                       "认为图像比文字描述更可靠、更便于他人核对。",
        "rv-known-01": "《细胞病理学》出版于 1858 年，是菲尔绍最有影响的著作。",
        "wo-known-01": "《医学的原理与实践》初版于 1892 年，是奥斯勒最有影响的著作，"
                       "长期作为英语世界的内科学标准教科书。",
        "ni-known-01": "《Notes on Nursing》最早出版于 1859 年，是南丁格尔最广为流传的著作。",
    }

    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)

        def w(name, obj):
            f = d / name
            f.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
            return f

        print("══ 正例：真实的入戏基线，不许判成候选 ══")
        s = scan_payload(w("in.json", IN))
        chk(f"㊀ Harvey 三条 → 覆盖率 {s['覆盖率']:.3f}（2/3），判「无候选」",
            not judge_payload(s)["候选"])
        chk("㊀a ★ 其中 `hv-decoy-01` 通篇无「我」而仍是入戏的——"
            "**它必须出现在「无第一人称的」名单里，却不足以让整份被判候选**",
            s["无第一人称的"] == ["hv-decoy-01"] and not judge_payload(s)["候选"])

        print("══ 反例：真实的不入戏基线，必须判成候选 ══")
        s2 = scan_payload(w("out.json", OUT))
        chk(f"㊁ Koch/Virchow/Osler/Nightingale 四条 → 覆盖率 {s2['覆盖率']:.3f}，判「候选」",
            judge_payload(s2)["候选"] and s2["覆盖率"] == 0.0)

        print("══ 混合：不许「有一条入戏就放行」 ══")
        mix = dict(OUT)
        mix.update({"x1": "我记得那一年。", "x2": "我不给你带引号的原话。",
                    "x3": "我当年在鲁汶刊过一册。"})
        for i in range(4, 11):
            mix[f"y{i}"] = "该书出版于 1858 年，是他最有影响的著作。"
        s3 = scan_payload(w("mix.json", mix))
        chk(f"㊂ 3 条入戏 + 11 条不入戏 → 覆盖率 {s3['覆盖率']:.3f} < {LOW}，仍判候选",
            judge_payload(s3)["候选"])

        print("══ 边界：恰好等于阈值不判 ══")
        edge = {f"a{i}": "我说。" for i in range(2)}
        edge.update({f"b{i}": "他说。" for i in range(3)})
        s4 = scan_payload(w("edge.json", edge))
        chk(f"㊃ 覆盖率恰为 {s4['覆盖率']:.3f} == {LOW} → **不判**（用 < 不用 <=）",
            abs(s4["覆盖率"] - LOW) < 1e-9 and not judge_payload(s4)["候选"])

        print("══ 三种形状都要摊得开 ══")
        chk("㊄ 扁平 `{cid: 文本}`", scan_payload(w("f1.json", IN))["总数"] == 3)
        chk("㊅ 行式 `[{case_id, baseline}]`",
            scan_payload(w("f2.json", [{"case_id": k, "baseline": v}
                                       for k, v in IN.items()]))["总数"] == 3)
        chk("㊆ 字典套字典 `{cid: {baseline: 文本}}`",
            scan_payload(w("f3.json", {k: {"baseline": v}
                                       for k, v in IN.items()}))["总数"] == 3)

        print("══ ★★ 扫不到的，要说「未核验」，不许算通过 ══")
        s5 = scan_payload(w("empty.json", {}))
        j5 = judge_payload(s5)
        chk("㊇ 0 条答案 → 未核验，且**候选=False 不等于通过**",
            j5["未核验"] and not j5["候选"] and "不是通过" in j5["状态"])
        # ★★ 这两条必须验**原因**，不能只验「未核验」。
        #   2026-08-12 变异实测：把坏 JSON 改成静默返回「0 条、覆盖率 1.0」，
        #   `未核验` 依然是 True——因为 `总数 == 0` 那道锁替它挡了枪，
        #   自测全绿而缺陷已落地（[[counter-example-red-can-be-red-by-coincidence]]
        #   「多道锁挡同一批东西，拆掉一道也不会红」）。
        (d / "bad.json").write_text("{ 不是 JSON", encoding="utf-8")
        j6 = judge_payload(scan_payload(d / "bad.json"))
        chk("㊈ 坏 JSON → 未核验，**且状态里说得出「不是 JSON」**",
            j6["未核验"] and "不是 JSON" in j6["状态"])
        j7 = judge_payload(scan_payload(d / "没有这个文件.json"))
        chk("㊉ 文件不存在 → 未核验，**且状态里说得出「读不了」**",
            j7["未核验"] and "读不了" in j7["状态"])

    print(("✗ 自测未过：" + "；".join(fails)) if fails else "\n✓ 自测全过")
    return 1 if fails else 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    paths = [a for a in argv if not a.startswith("-")]
    if not paths:
        print(__doc__)
        return 3
    scanned, cands = 0, []
    for a in paths:
        p = pathlib.Path(a)
        stat = scan_payload(p)
        verdict = judge_payload(stat)
        scanned += stat.get("总数", 0)
        print(f"{p}: {verdict['状态']}")
        if verdict["候选"]:
            cands.append(p)
            for cid in stat["无第一人称的"][:6]:
                print(f"    · {cid}")
    if not scanned:
        print("\n**一条答案都没扫到——未核验，不是通过。**")
        return 2
    if cands:
        print(f"\n★ {len(cands)} 份是**候选**，要人去读："
              "阈值是在 22 个已判分人物上拟合的，对第 23 个人没有保证。")
        return 1
    print(f"\n✓ 已扫 {scanned} 条答案，无候选。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
