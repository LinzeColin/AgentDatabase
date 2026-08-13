#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rebuild_derived_slices.py —— **重抓拿不回切片，这里把它算回来**

## 为什么要有这个

语料按裁定不进 git；重建靠 `raw/_ids-rebuild.txt` 重新抓 archive.org。
2026-08-14 出现了第一份**派生**语料：Dewey 的 `src-9fdb7da7d9d3` 原件是
《Science》1915-01-29 **整期**（多作者），台账指向的是从中切出的他那一篇。

**重抓只会拿回整期原件，拿不回切片。** 于是台账里那条 `checksum` 在一台新机器上
永远对不上 —— 而且**没有任何判据会说这是为什么**，只会报「校验和不符」。
⇒ 把「原件 → 切片」的配方写成 `evidence/_derived-slices.json`，由本件执行。

    抓原件（_ids-rebuild.txt） → **本件** → 台账 checksum 对得上

## 它怎么判「切对了」

**不信自己的输出**：切完立刻算 sha256，与配方里记的 `out_sha256` 比。
对不上就红，不写盘（`--check` 只比不写）。锚点在原件里**必须唯一**，
不唯一就红 —— 不许「取第一个」蒙混过去。

## 它做不到什么（**必须一起念**）

1. **原件不在就做不了**，报「未重建」不报「通过」。
2. 它**不判切得对不对**（那是署名判据与人的事），只保证**可复现**：
   同一份原件 ＋ 同一份配方 → 同一个字节序列。
3. 它**不改台账**。台账与配方对不上要人看。

## 用法

    python3 rebuild_derived_slices.py --all              # 扫全库，缺切片就补
    python3 rebuild_derived_slices.py --all --check      # 只比对，不写盘
    python3 rebuild_derived_slices.py --workspace <工作区>
    python3 rebuild_derived_slices.py --self-test

退出码：0＝全部对得上（或按需补齐）；1＝有对不上的；4＝原件不在，未重建
"""
import argparse
import glob
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent
CORPORA = PD / "_corpora"


def cut(text: str, start: str, end: str, inclusive: bool = True):
    """原件正文 → (切片, 说明)。**纯函数**，自测不碰磁盘。

    ★ 锚点不唯一一律拒绝 —— 「取第一个」在 OCR 文本里是错的常见来源
      （目录里出现一次、正文里再出现一次，取第一个就切到目录上了）。
    """
    ns, ne = text.count(start), text.count(end)
    if ns == 0:
        return None, f"起点锚在原件里找不到（`{start[:28]}`）"
    if ns > 1:
        return None, f"起点锚出现 {ns} 次，**不唯一**，拒绝切（不许取第一个）"
    a = text.index(start)
    if ne == 0:
        return None, f"终点锚在原件里找不到（`{end.strip()[:28]}`）"
    if ne > 1:
        return None, f"终点锚出现 {ne} 次，**不唯一**，拒绝切"
    # ★ 用 find 不用 index：终点锚**只出现在起点之前**时 index 会抛 ValueError 而不是报错
    #   （自测里 b6 那条当场崩了——判据不许崩，要给出诊断）
    e = text.find(end, a)
    if e == -1:
        return None, "终点锚只出现在起点锚**之前**，切不出正向区间"
    return text[a:e + len(end)] if inclusive else text[a:e], "ok"


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    doc = "BOILERPLATE junk\nCONTENTS listing\nHEAD START\nbody one two three\n名字 \n后面是别人的文章"
    body, why = cut(doc, "HEAD START", "\n名字 \n")
    chk(f"★ 正常切：拿到中间那段（why={why}）",
        body == "HEAD START\nbody one two three\n名字 \n")
    chk("★ 切片是原件的**连续子串**", body in doc)
    chk("★ 切掉了前面的样板与后面的别人文章",
        "BOILERPLATE" not in body and "别人的文章" not in body)
    b2, w2 = cut(doc, "HEAD START", "\n名字 \n", inclusive=False)
    chk("★ inclusive=False 时不含终点锚", b2 == "HEAD START\nbody one two three")
    # ★★ 反例组
    dup = "HEAD START x HEAD START y\n名字 \n"
    b3, w3 = cut(dup, "HEAD START", "\n名字 \n")
    chk(f"★★ **反例：起点锚出现两次 → 拒绝切**（不许取第一个）（{w3[:24]}）", b3 is None)
    b4, w4 = cut(doc, "NOT THERE", "\n名字 \n")
    chk(f"★ 反例：起点锚找不到 → None（{w4[:22]}）", b4 is None)
    b5, w5 = cut(doc, "HEAD START", "\n没有这个锚 \n")
    chk(f"★ 反例：终点锚找不到 → None（{w5[:22]}）", b5 is None)
    b6, w6 = cut(doc, "名字 ", "\nCONTENTS listing\n")
    chk(f"★★ 反例：终点在起点**之前** → None（{w6[:22]}）", b6 is None)
    # ★ 校验和：切对了才等
    chk("★ 同一份原件＋同一份配方 → 同一个 sha256（可复现）",
        hashlib.sha256(cut(doc, "HEAD START", "\n名字 \n")[0].encode()).hexdigest()
        == hashlib.sha256(body.encode()).hexdigest())
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def run(ws: pathlib.Path, check_only: bool) -> int:
    rec = ws / "evidence/_derived-slices.json"
    if not rec.is_file():
        return 0
    d = json.loads(rec.read_text(encoding="utf-8"))
    rc = 0
    for s in d.get("slices", []):
        src = ws / s["from_file"]
        out = ws / s["out_file"]
        tag = f"{ws.name}／{s['source_id']}"
        if not src.is_file():
            print(f"  ！ {tag}：**原件不在，未重建**（不是通过）—— 先跑 "
                  f"`fetch_ia.py --ids-file {ws}/raw/_ids-rebuild.txt`")
            rc = rc or 4
            continue
        raw = src.read_bytes()
        got = hashlib.sha256(raw).hexdigest()
        if got != s["from_sha256"]:
            print(f"  ❌ {tag}：**原件本身对不上**（{got[:12]}… ≠ {s['from_sha256'][:12]}…）"
                  f"——重抓到的不是当初那一份，切片不做")
            rc = 1
            continue
        body, why = cut(raw.decode("utf-8", errors="replace"),
                        s["start_anchor"], s["end_anchor"], s.get("end_anchor_inclusive", True))
        if body is None:
            print(f"  ❌ {tag}：切不出来 —— {why}")
            rc = 1
            continue
        new = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if new != s["out_sha256"]:
            print(f"  ❌ {tag}：切出来了但**校验和不符**（{new[:12]}… ≠ {s['out_sha256'][:12]}…）"
                  f"——不写盘")
            rc = 1
            continue
        if check_only:
            print(f"  ✓ {tag}：配方复现得出（{len(body.split())} 词，sha256 对得上）")
        elif out.is_file() and hashlib.sha256(out.read_bytes()).hexdigest() == new:
            print(f"  ✓ {tag}：切片已在且一致（{len(body.split())} 词）")
        else:
            out.write_text(body, encoding="utf-8")
            print(f"  ✓ {tag}：**已重建**（{len(body.split())} 词，sha256 对得上）")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true", help="只比对，不写盘")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.workspace:
        return run(pathlib.Path(a.workspace), a.check)
    if a.all:
        rc = 0
        n = 0
        for p in sorted(glob.glob(str(CORPORA / "wip-*" / "workspaces" / "*"))):
            ws = pathlib.Path(p)
            if (ws / "evidence/_derived-slices.json").is_file():
                n += 1
                r = run(ws, a.check)
                rc = r if r == 1 else (rc or r)
        print(f"\n有派生切片配方的工作区：**{n}** 个"
              + ("（全库暂时只有 Dewey 一个）" if n <= 1 else ""))
        return rc
    ap.error("要 --workspace 或 --all 或 --self-test")


if __name__ == "__main__":
    raise SystemExit(main())
