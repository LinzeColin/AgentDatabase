#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**「这是我发明的」——限定呢？**

## 为什么有这道判据

首创声明是人物产物里**最容易写宽、也最难被评委抓住**的一类：
评委没有语料（见 `judges-cannot-verify-quotes`），
**「电弧焊是我发明的」读起来和真的一模一样。**

眼下的直接风险：**#115 Slavyanov 与 Benardos 都在队列里**，
两人的发明长期被互相混记——

| | 生卒 | 电极 |
|---|---|---|
| Benardos | 1842–1905 | **碳** |
| Slavyanov | 1854–1897 | **金属**（可熔） |

**两份产物将来会同时在册。** 任何一方写宽了，它们就自相矛盾。

同类风险不止这一对：Fleming #111 的「青霉素是我发明的」
（分离纯化是牛津团队）、Jenner #104 的「机理我给不出」。

## 判据

第一人称的首创／独创声明，**同一句里必须带至少一个限定**：

- **年份**（`1888 年`、`那一年`）
- **材料／方法／范围**（`可熔金属电极`、`碳电极`、`第一次在…上`）
- **分层**（`不是我一个人`、`我做的那一段是`、`在此之前 X 已经`）

一个都没有 → 报出来。

## ★★ 它绝不惩罚诚实的分层

这是本流水线**已经犯过三次**的错：判据把「我**不**把它称作我的报告」
「我没核过，不核就不报数」判成缺陷，**逼作者把诚实的那句删掉**。

所以这里的规则是反的：**只要句子里有分层／让渡，就算限定，直接放行。**
宁可漏报一句写宽的，也不许逼人删掉一句诚实的。

## 它判不了什么

- **判不了限定是不是真的。** 「1888 年我发明了电弧焊」有年份，它放行——
  **年份对不对是引文核查器的事。**
- **不判第三方叙述。** 只看第一人称。别人写「他发明了电弧焊」不归它管。
"""
import argparse
import json
import pathlib
import re
import sys

# 第一人称首创／独创声明
# ★ 首创声明的说法比「发明」宽得多。实测（2026-08-04）：十个已完成人物的
#   全部 payload 里，含「发明／首创／首次」的只有 5 句，而第一版 CLAIM
#   **一句都没认出来**——真数据用的是「首次发表」「首次陈述」这类说法。
#   **报 0 是因为判据窄，不是因为产物干净。**
CLAIM = re.compile(
    r"(?:我|本人)(?:[^。！？\n]{0,24})?"
    r"(?:发明|首创|开创|第一个(?:做出|提出|实现|想到|用)"
    r"|首次(?:做出|实现|提出|发表|陈述|使用|报告|描述|应用))"
    r"|(?:是|由)我(?:一个人|独自|单独|亲手)?(?:发明|做出|搞出|首创)(?:的|出来的)?"
)

# 限定：年份／材料方法范围／分层让渡
QUALIFIER = re.compile(
    r"\b1[6-9]\d{2}\b|\b20\d{2}\b|那一年|同年|次年"                       # 年份
    r"|电极|碳|金属|可熔|方法|工艺|装置|专利|在[^。\n]{0,10}上|范围|限于"   # 材料方法范围
    r"|不是我(?:一个人|独自|单独)|不止我|并非我(?:一个人)?"                # ★ 分层让渡
    r"|我(?:做|写|负责)的那(?:一)?(?:段|部分|块)"
    r"|在(?:此|我)之前|更早|先于我|与[^。\n]{0,12}(?:同时|各自)"
    r"|只(?:是|做了)|仅(?:限|就)|其中(?:一|某)(?:段|部分|环)"
    r"|合著|合撰|团队|他们(?:做|完成)"
)


def sentences(text: str):
    for s in re.split(r"(?<=[。！？\n])", text):
        s = s.strip()
        if s:
            yield s


def scan_text(unit_id: str, text: str, acc):
    for s in sentences(text):
        if not CLAIM.search(s):
            continue
        acc["claims"] += 1
        if QUALIFIER.search(s):
            acc["qualified"] += 1
        else:
            acc["bad"].append((unit_id, s[:110]))


def scan(paths):
    """→ `{claims, qualified, bad, units, badjson, unread}`。

    ★ 射程（不写清，「0 处」就会骗人）：
    - `.jsonl` **按行**拆成单元；其余按整份文件扫。
    - jsonl 里**只取顶层的字符串字段**，且跳过 `id`/`case_id`——
      **嵌套 dict/list 里的正文本件看不见**。
    - `units` 是真正被送进 `scan_text` 的单元数。
      **「claims=0」与「一个单元都没扫到」在旧版报告里长得一样**，故单列。

    ★★ 2026-08-12：坏 JSON 行原先是 `except ValueError: continue`——**整行消失**，
      而屏幕只会说「首创声明 0 处」。同理读不了的文件原先直接抛异常崩掉。
      两者现在都记数并报出来（[[empty-default-swallows-unknown]]）。
    """
    acc = {"claims": 0, "qualified": 0, "bad": [],
           "units": 0, "badjson": 0, "unread": []}
    for p in paths:
        try:
            raw = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            acc["unread"].append((str(p), str(exc)))
            continue
        if p.suffix == ".jsonl":
            for i, line in enumerate(raw.splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    acc["badjson"] += 1          # ← 不许静默消失
                    continue
                blob = " ".join(str(v) for k, v in r.items()
                                if isinstance(v, str) and k not in ("id", "case_id"))
                acc["units"] += 1
                scan_text(f"{p.name}:{i}", blob, acc)
        else:
            acc["units"] += 1
            scan_text(p.name, raw, acc)
    return acc


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    def run(t):
        a = {"claims": 0, "qualified": 0, "bad": []}
        scan_text("t", t, a)
        return a

    print("── ★ 正向：无限定的首创声明要被抓住 ──")
    a = run("电弧焊是我发明的。")
    print(f"    抓到 {len(a['bad'])} 处：{a['bad'][0][1] if a['bad'] else '—'}")
    chk("「电弧焊是我发明的」→ 报", len(a["bad"]) == 1)

    print("── ★ 反向对照 ①：带年份就放行 ──")
    a = run("1888 年我做出了用可熔金属电极的焊法。")
    chk("有年份＋材料 → 不报", not a["bad"])

    print("── ★★ 反向对照 ②：**分层让渡算限定，绝不惩罚诚实** ──")
    a = run("这不是我一个人发明的。")
    chk("「不是我一个人发明的」→ **不报**", not a["bad"])
    a = run("我发明的只是其中一段，在此之前已有人做过。")
    chk("「只是其中一段／在此之前」→ **不报**", not a["bad"])

    print("── ★★ 反向对照 ③：**第三方叙述不归它管** ──")
    a = run("他发明了电弧焊。史书如此记载。")
    chk("第三人称 → 不报", not a["bad"] and a["claims"] == 0)

    print("── ★ 反向对照 ④：材料限定单独也算 ──")
    a = run("我首创的是碳电极那一路。")
    chk("有「碳电极」→ 不报", not a["bad"])

    print("── ★★ 反向对照 ⑤：**限定必须在同一句内** ──")
    a = run("电弧焊是我发明的。碳电极是另一回事。")
    chk("限定落在下一句 → 仍报（不许跨句捡限定）", len(a["bad"]) == 1)

    print("── ★★ 反向对照 ⑦：**真数据的说法要认得出**（第一版一句都没认出） ──")
    a = run("我 1827 年生、1853 年才首次发表。")
    print(f"    claims={a['claims']} bad={len(a['bad'])}")
    chk("Lister 那句被认成首创声明，且因带年份而**放行**",
        a["claims"] == 1 and not a["bad"])

    print("── 反向对照 ⑥：没有首创声明的文本一律不报 ──")
    a = run("我量过三次，两次成功。")
    chk("普通陈述 → 不报，且 claims=0", not a["bad"] and a["claims"] == 0)

    # ══════════════════════════════════════════════════════════════
    # ㉘ `scan()` 本体 —— 2026-08-12 之前它一次也没被自测进入过
    # ══════════════════════════════════════════════════════════════
    #
    # 上面各条打的是 `scan_text()`（**一段话算不算无限定首创声明**），
    # 而 `scan()` 决定**哪些文本进得了那把尺子底下**：`.jsonl` 怎么拆、
    # 哪些字段被拼进 blob、坏行与读不了的怎么记。
    print("\n── ㉘ scan() 本体（tempdir 上跑真流程）──")
    import tempfile as _tf
    _BAD = "电弧焊是我发明的。"                       # 无限定 → 应报
    # ★ 夹具**先单独喂给 `scan_text` 确认它落在射程里**才写的断言：
    #   第一版写的是「电弧焊我 1881 年做成，同期还有别人在做。」——
    #   `CLAIM` **根本不认它**（claims=0），于是 ㉘b 断言 claims==2 当场变红。
    #   [[counter-example-red-can-be-red-by-coincidence]]：夹具不在射程里，绿也好红也好都不作数。
    _OK = "电弧焊是我 1881 年发明的，同期还有别人在做。"   # 认得出 + 带年份让渡 → 放行

    def _files(d: dict):
        t = pathlib.Path(_tf.mkdtemp())
        out = []
        for name, body in d.items():
            f = t / name
            f.write_text(body, encoding="utf-8")
            out.append(f)
        return out, t

    ps, _ = _files({"a.md": _BAD})
    a = scan(ps)
    chk(f"㉘a 单份 .md → units=1、报 1 处（units={a['units']} bad={len(a['bad'])}）",
        a["units"] == 1 and len(a["bad"]) == 1)

    ps, _ = _files({"c.jsonl": json.dumps({"claim": _BAD}, ensure_ascii=False) + "\n"
                              + json.dumps({"claim": _OK}, ensure_ascii=False) + "\n"})
    a = scan(ps)
    chk(f"㉘b `.jsonl` **按行拆**成 2 个单元，只报无限定那行"
        f"（units={a['units']} claims={a['claims']} bad={len(a['bad'])}）",
        a["units"] == 2 and a["claims"] == 2 and len(a["bad"]) == 1)

    # ㉘c ★ 坏 JSON 行不许静默消失（改前是 `except ValueError: continue`）
    ps, _ = _files({"c.jsonl": "{not json\n"
                               + json.dumps({"claim": _BAD}, ensure_ascii=False) + "\n"})
    a = scan(ps)
    chk(f"㉘c 坏 JSON 行 → 记进 `badjson`（{a['badjson']}），**不是静默丢掉**",
        a["badjson"] == 1 and a["units"] == 1 and len(a["bad"]) == 1)

    # ㉘d ★ 读不了的文件不许把整次扫描崩掉，也不许静默消失
    _t = pathlib.Path(_tf.mkdtemp())
    (_t / "ok.md").write_text(_BAD, encoding="utf-8")
    (_t / "gone.md").symlink_to(_t / "nowhere.md")     # 断链
    a = scan([_t / "ok.md", _t / "gone.md"])
    chk(f"㉘d 读不了的文件 → 进 `unread`（{len(a['unread'])} 份），其余照扫"
        f"（units={a['units']}）",
        len(a["unread"]) == 1 and a["units"] == 1 and len(a["bad"]) == 1)

    # ㉘e ★★ 射程声明：jsonl 里**嵌套 dict/list 中的正文本件看不见**。
    #    这不是缺陷、是射程——写成断言才不会被下一个人当成「查过了」。
    ps, _ = _files({"c.jsonl": json.dumps({"nested": {"claim": _BAD}},
                                          ensure_ascii=False) + "\n"})
    a = scan(ps)
    chk("㉘e 射程：**嵌套字段里的首创声明扫不到**（顶层字符串字段之外看不见）",
        a["units"] == 1 and a["claims"] == 0)

    # ㉘f 射程：`id`/`case_id` 被排除——题号里带的字样不该被当成正文
    ps, _ = _files({"c.jsonl": json.dumps({"case_id": _BAD, "claim": "我量过三次。"},
                                          ensure_ascii=False) + "\n"})
    a = scan(ps)
    chk("㉘f 射程：`case_id` 不进 blob（题号不是正文）", a["claims"] == 0)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    paths = [p for p in a.paths if p.is_file()]
    if not paths:
        print("✗ **一个文件都没读到——本次未检查（不是通过）**")
        return 3
    acc = scan(paths)
    print(f"已扫 **{acc['units']}** 个单元"
          f"（{len(paths)} 份文件；`.jsonl` 按行拆）")
    if acc["badjson"] or acc["unread"]:
        print(f"⚠ **{acc['badjson']} 行 JSON 解析不了、{len(acc['unread'])} 份文件读不了"
              f"——那些没被查，不是没问题**")
        for pth, err in acc["unread"][:5]:
            print(f"     {pth}　{err[:70]}")
    if not acc["units"]:
        print("✗ **一个单元都没扫到——本次未检查（不是通过）**")
        return 3
    print(f"第一人称首创声明 **{acc['claims']}** 处，其中带限定 **{acc['qualified']}** 处\n")
    if not acc["bad"]:
        print("  ✓ 没有无限定的首创声明")
        return 0
    print(f"✗ **{len(acc['bad'])} 处首创声明没有任何限定**：")
    for uid, s in acc["bad"][:12]:
        print(f"    {uid}\n      {s}")
    print("\n  **限定要么是年份，要么是材料／方法／范围，要么是分层让渡。**\n"
          "  评委没有语料——**「这是我发明的」读起来和真的一模一样。**")
    return 1


if __name__ == "__main__":
    sys.exit(main())
