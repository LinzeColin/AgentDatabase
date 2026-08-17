#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冗余体检：同一引文／同一事实在一段里说了两遍。

## 为什么需要它（RUNBOOK 第十七种的落地面）

订正的默认动作是**加**，而订正常常需要的是**换**。
Jesse Vincent #94 里，我把新的说法追加进括号、没删掉原来那句，
结果同一条英文引文在一句话里引了两遍——
**而这正是三位评委都指出过、我自己刚写进 RUNBOOK 的那个模式。**

写进 RUNBOOK 挡不住它，因为落地订正时人是在「改这一处」的模式里，
看不见整段。**必须有一个机器来看整段。**

## 查什么

- 同一段英文引文（≥20 字符投影）出现 ≥2 次
- 同一串数字组合（如「技术 9、纯个人 11」）出现 ≥2 次
- 同一句中文短语（≥12 字）出现 ≥2 次

**只列不判**——有些重复是刻意的（如 rubric 复述要点、分层作答的收束）。
"""
import argparse, collections, pathlib, re, sys

NONWORD = re.compile(r"[^0-9A-Za-z]+")
EN = re.compile(r"[「\"]([A-Za-z][^」\"]{18,300})[」\"]")
CN = re.compile(r"[一-鿿，、]{12,40}")
NUM = re.compile(r"(?:[一-鿿]{2,4}\s*\d+[、，]){2,}")


# ★ 元数据文件不进冗余检查：source-ledger 的 title/checksum 字段天然重复，
#   把它算进来会产生成百上千条误报，把真命中淹没
#   （Salatin #95：217 处误报全部来自 source-ledger.jsonl）。
SKIP = {"source-ledger.jsonl", "results.jsonl"}


# 计数串的归一：`[一-鿿]{2,4}` 是贪婪的，会把前文的字一并吃进来，
# 于是「构成是技术 9、…」与「仍是技术 9、…」这**同一串计数**被当成两串，重复就漏掉了。
# **自测抓出来的**——只取紧贴每个数字的两个汉字，把前文的噪声甩掉。
_PAIR = re.compile(r"([一-鿿]{2,4})\s*(\d+)")


def _norm_num(s: str) -> str:
    return "|".join(f"{a[-2:]}{b}" for a, b in _PAIR.findall(s))


def scan_text(text: str) -> list:
    """→ [(类别, 次数, 片段)]。**逐段扫**——跨段重复往往是刻意的，段内才是订正留下的。"""
    rows = []
    for para in text.split("\n"):
        if len(para) < 60:
            continue
        for label, rx, norm in (("英文引文", EN, lambda s: NONWORD.sub("", s).lower()),
                                ("计数串", NUM, _norm_num),
                                ("中文短语", CN, lambda s: s.strip())):
            c = collections.Counter(norm(m) for m in rx.findall(para))
            for k, n in c.items():
                if n >= 2 and len(k) >= 12:
                    rows.append((label, n, k[:70]))
    return rows


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：Jesse Vincent #94 的真实形态（订正只加不换）──")
    # 我把新说法追加进括号、没删原来那句，同一条英文引文在一句话里引了两遍。
    real = ('他自己的说法是「the whole point is that you can just read the source '
            'and see what it does」，我先前写成了别的意思（原话其实是'
            '「the whole point is that you can just read the source and see what it does」），'
            '这里以原话为准，不再转述。')
    out = scan_text(real)
    chk("同一条英文引文在一段里出现两次 → 报出",
        any(lab == "英文引文" and n >= 2 for lab, n, _ in out))

    print("── 反向对照 ①：只出现一次的引文不许报 ──")
    once = ('他自己的说法是「the whole point is that you can just read the source '
            'and see what it does」，这一句我照录，不转述，也不做删节处理，以免走样。')
    chk("同一条引文只出现一次 → 不报",
        not [r for r in scan_text(once) if r[0] == "英文引文"])

    print("── 反向对照 ②：跨段的重复不许报（分层作答会刻意复述）──")
    across = (real.split("，我先前")[0] + "。\n"
              + "另起一段再说一次：他的原话是「the whole point is that you can just "
                "read the source and see what it does」，这是刻意的收束，不是冗余啊。")
    chk("同一条引文分处两段 → 不报（判据只看段内）",
        not [r for r in scan_text(across) if r[0] == "英文引文"])

    print("── 反向对照 ③：短行不许扫（标题、列表项天然会重复用词）──")
    chk("整行短于 60 字 → 跳过", scan_text("## 引文\n- 引文\n- 引文") == [])

    print("── 反向对照 ④：数字串重复要抓，但单次不抓 ──")
    numpara = ("这一轮统计出来的构成是技术 9、纯个人 11、其他 3，"
               "复核一遍之后仍然是技术 9、纯个人 11、其他 3，两次统计完全一致因此可以采用。")
    single = ("这一轮统计出来的构成是技术 9、纯个人 11、其他 3，"
              "此外没有别的类别需要在这里单独列出来统计并加以说明，"
              "所以这一段里那串计数只出现了一次，判据不该报它。")
    # **两条夹具都必须过 60 字的长度门**，否则反向对照是空过的——
    # 第一版 numpara 只有 58 字，判据根本没扫到它，两条控制一起失效。
    chk(f"夹具本身够长（正 {len(numpara)} 字 / 反 {len(single)} 字，门 60）",
        len(numpara) >= 60 and len(single) >= 60)
    chk("同一串计数在一段里出现两次 → 报出",
        any(lab == "计数串" for lab, _, _ in scan_text(numpara)))
    chk("只出现一次的计数串 → 不报",
        not [r for r in scan_text(single) if r[0] == "计数串"])
    # ↑ 这一条第一版没过，查出来是真缺陷：`[一-鿿]{2,4}` 贪婪吃进前文，
    #   「构成**是技术** 9…」与「仍**是技术** 9…」被当成两串不同的计数，重复就漏了。
    chk("**前面的字不同也要算同一串**（贪婪吃前文那个坑）",
        _norm_num("成是技术 9、纯个人 11、其他 3，")
        == _norm_num("仍是技术 9、纯个人 11、其他 3，")
        != "")
    chk("**数字不同就不是同一串**——归一不许归过头",
        _norm_num("技术 9、纯个人 11、") != _norm_num("技术 8、纯个人 11、"))

    print("── 反向对照 ⑤：元数据文件必须排除，否则真命中会被淹没 ──")
    # Salatin #95：217 处误报全部来自 source-ledger.jsonl 的 title/checksum 字段
    chk("source-ledger.jsonl 在 SKIP 里", "source-ledger.jsonl" in SKIP)
    chk("results.jsonl 在 SKIP 里", "results.jsonl" in SKIP)

    print("── 反向对照 ⑥：空文本不许报「无重复」，也不许崩 ──")
    chk("空串 → 返回空", scan_text("") == [])

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--extra", nargs="*", default=[], type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 --workspace")

    files = [f for f in sorted(list(a.workspace.rglob("*.md"))
                               + list(a.workspace.rglob("*.jsonl")) + list(a.extra))
             if f.name not in SKIP]
    if not files:
        print(f"✗ **{a.workspace} 下一个 .md／.jsonl 都没读到——结果不可信，不是「没问题」**")
        return 3
    total = 0
    # ★ 真正的可比单位是**长度 ≥60 的段**（`scan_text` 的射程），不是文件数。
    _n_para = 0
    for f in files:
        _txt = f.read_text(encoding="utf-8", errors="replace")
        _n_para += sum(1 for _p in _txt.split("\n") if len(_p) >= 60)
        rows = scan_text(_txt)
        if rows:
            print(f"── {f.name}")
            for label, n, k in rows[:6]:
                print(f"   [{label} ×{n}] {k}")
            total += len(rows)
    # ★★★ 2026-08-17 第二轮：**扫了 N 份文件 ≠ 比过 N 个段落**。
    #   [[zero-hit-gates-must-prove-they-can-hit]]（第二轮：分母是文件数，断言的单位却是别的）
    if total:
        print(f"\n扫过 {len(files)} 份；⚠ {total} 处段内重复——只列不判，逐条判断是否刻意")
    elif not _n_para:
        print(f"\n扫过 {len(files)} 份；⚠ **可比段落 0 个 —— 本次未核，不是通过。**"
              "\n   「无段内重复」在空集上恒真。")
    else:
        print(f"\n扫过 {len(files)} 份 / **{_n_para}** 个段落；✓ 无段内重复")
    return 0


if __name__ == "__main__":
    sys.exit(main())
