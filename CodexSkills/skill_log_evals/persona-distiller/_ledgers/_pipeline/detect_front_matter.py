#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""detect_front_matter.py —— 找出**一手卷里正文从哪儿开始**（前面那一截是别人写的）

## 为什么有这件

2026-08-13，Brandeis #172 写断言层时差一点把**三条事实**记成他的，而它们出自
《Business—a profession》三个扫描件的**卷前导言**：

    src-f262a6c0fb76  导言 0–62,094    Ernest Poole，末尾以欧里庇得斯几行收束
    src-3d16531d4151  导言 0–64,956    同上
    src-cc33bc7e060b  导言 0–73,433    ★ 1925 版还多一套注，署名
                                        `Felix Frankfurter Cambridge, Massachusetts November i, 1924`

三个数分别是全文的 **13.6% / 14.1% / 13.7%** —— 一部署他名字的书，前七分之一不是他写的。

★ 揭穿它的是一句第三人称：`"Our work so far," said Brandeis, "has af¬ fected only
industrial insurance…"` ——**一本他自己的书里，不会有人用第三人称转述他**。

★★ `flag_borrowed_voice` 原来的 ③ 用**写死的 12000 字**当序言区，
   而这三份的真边界是它的 5–6 倍。写死的常数在这一族书上等于没有。

## 判法

不猜、不数页码，**看书眉（running head）从哪儿开始连续出现**：

1. 从台账 `title` 取前几个实词，作成宽松正则（大小写、连字符、空格都放开）；
2. 全文找出所有命中；扉页会命中一两次，然后是一段长空白（导言），
   再往后每一页页眉都命中一次；
3. **正文起点 = 第一个「其后 40,000 字内还有 ≥8 次命中、且这些命中是周期性的」的位置。**
   扉页那一两次因为后面紧跟着导言，40,000 字内凑不够，自动被跳过。
4. ★ 「周期」这一条不是装饰：书眉每页一次，实测中位间隔 1300 字左右、90% 规整；
   而**没有书眉**的辩状里题名短语只是散落扎堆，规整度 25%——
   少了这一条，它会被判成「正文从 91% 开始」。

书眉找不到（没有页眉、或题名与页眉不同）就**如实报 `null`，不猜**——
[[empty-default-swallows-unknown]]：这里 `null` 的意思是「没测出来」，
**不是「没有导言」**，调用方必须分开处理这两种。

## 用法

    python3 detect_front_matter.py --raw <raw> --ledger <source-ledger.jsonl> [--json]
    python3 detect_front_matter.py --self-test     # 跑真语料的三个已知边界

退出码：0＝跑完（无论测没测出）；2＝参数不对；4＝读不到语料；**5＝自测跳过（语料不在本树）**
"""
import argparse
import json
import pathlib
import re
import statistics
import sys

WS = re.compile(r"\s+")
STOP = {"the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "being", "part",
        "his", "her", "its", "with", "by", "at", "from", "how", "it"}
WINDOW = 40000          # 「其后这么长里还有几次」
MIN_RUN = 8             # …至少这么多次，才算进了正文页眉区
# ★★ 光看「密不密」会认错东西。实测踩到的：
#   《Scientific management and railroads》**根本没有书眉**，题名短语只在正文里散落 8 处；
#   而末尾几处凑在一起，被第一版判成「正文从 91% 开始」——**荒谬但绿灯**。
#   ⇒ 再加一条：书眉是**每页一次**的，必须**周期**，不是扎堆。
#   实测中位间隔与规整度：真书眉 1306 字 / 90% 规整、1302 / 90%；
#   假的那两份 2924 / **25%**、3036 / **25%**。取 70%。
PERIODIC_MIN = 0.70
PERIODIC_LO, PERIODIC_HI = 0.4, 2.5     # 间隔落在中位数的这个区间内才算规整


def dehyphen(t: str) -> str:
    t = re.sub(r"(\w)[-‐‑]\s*\n\s*([a-z])", r"\1\2", t)
    return re.sub(r"(\w)[-‐‑]\s+([a-z])", r"\1\2", t)


def norm_text(p: pathlib.Path) -> str:
    return WS.sub(" ", dehyphen(p.read_text(encoding="utf-8", errors="replace")))


def head_pattern(title: str, n_words: int = 3):
    """题名 → 宽松书眉正则。取前 n 个实词，词间允许任意空白/连字符/破折号。"""
    words = [w for w in re.findall(r"[A-Za-z']{2,}", title or "") if w.lower() not in STOP]
    if len(words) < 2:
        return None, []
    use = words[:n_words]
    # ★ 词间要允许**一个短填充词**。实测踩到的：题名《Business--a profession》
    #   去掉停用词后是 Business / profession，而书眉印的是 `BUSINESS -A PROFESSION`
    #   —— 中间那个 `A` 让「只允许标点空白」的间隔正则一次都匹配不上，
    #   三份全报「测不出」。冠词在题名里是停用词，在书眉里还在。
    gap = r"[^A-Za-z]{0,5}(?:[A-Za-z]{1,3}[^A-Za-z]{0,5})?"
    return re.compile(gap.join(re.escape(w) for w in use), re.I), use


def body_start(text: str, title: str):
    """→ (正文起点或 None, 诊断)。**测不出就 None，不猜。**"""
    # ★★ **不做「少取几个词再试一次」的回退。** 实测踩到的：
    #   《Scientific management and railroads》三词版只有 8 处命中（它没有书眉），
    #   回退到两词 `Scientific management` 之后——那是**这本书的主题词**，满篇都是——
    #   于是找到一段看着很周期的run，报出「正文从 91% 开始」。
    #   放宽检索式换来的从来不是更准，是**把主题词当成了书眉**。测不出就报 null。
    for n in (3,):
        pat, used = head_pattern(title, n)
        if pat is None:
            return None, {"为什么": "题名实词不足 2 个，做不出书眉正则"}
        hits = [m.start() for m in pat.finditer(text)]
        if len(hits) < MIN_RUN + 1:
            continue
        best = None
        for i, o in enumerate(hits):
            run = [h for h in hits[i:] if h < o + WINDOW]
            if len(run) < MIN_RUN:
                continue
            gaps = [b - a for a, b in zip(run, run[1:])]
            med = statistics.median(gaps)
            reg = sum(1 for g in gaps if PERIODIC_LO * med <= g <= PERIODIC_HI * med) / len(gaps)
            best = best or {"窗内命中": len(run), "中位间隔": round(med), "规整度": round(reg, 2)}
            if reg < PERIODIC_MIN:
                continue
            return o, {"书眉词": " ".join(used), "命中总数": len(hits),
                       "跳过的扉页命中": hits[:i], "正文起点": o,
                       "窗内命中": len(run), "中位间隔": round(med), "规整度": round(reg, 2),
                       "占全文": round(o / max(1, len(text)) * 100, 2)}
        return None, {"书眉词": " ".join(used), "命中总数": len(hits),
                      "为什么": (f"扎堆但不周期（规整度 {best['规整度']} < {PERIODIC_MIN}）"
                                if best else
                                f"没有任何一处命中在其后 {WINDOW} 字内凑够 {MIN_RUN} 次"),
                      **(best or {})}
    return None, {"为什么": f"书眉命中 < {MIN_RUN + 1} 次，判不出页眉区"}


def run(raw: pathlib.Path, ledger: pathlib.Path):
    rows, unread = [], []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        f = raw / pathlib.Path(r.get("local_path", "")).name
        if not f.exists():
            unread.append(r["source_id"])
            continue
        t = norm_text(f)
        o, why = body_start(t, r.get("title", ""))
        rows.append({"source_id": r["source_id"], "title": (r.get("title") or "")[:52],
                     "字符数": len(t), "正文起点": o, "诊断": why})
    return rows, unread


# ---------------- 自测：三个边界**是逐字读出来的，不是这只工具报的** ----------------
BASE = pathlib.Path(__file__).resolve().parents[2] / "_corpora"
WS_BRANDEIS = "wip-brandeis-172/workspaces/louis-brandeis"
# (source_id, 期望正文起点, 该处往前那句话——**人读出来的证据**)
KNOWN = [
    ("src-f262a6c0fb76", 62094, "Poole 导言以欧里庇得斯收束：`Go forth, my son, and help!`"),
    ("src-3d16531d4151", 64956, "同上（另一扫描件，OCR 作 `Go forth, my son, and hdpl`）"),
    ("src-cc33bc7e060b", 73433, "1925 版：`Felix Frankfurter Cambridge, Massachusetts November i, 1924`"),
]
TOL = 200


SKIP_NO_CORPUS = 5      # 语料不在本树 ⇒ **未跑**，不是不过


def self_test() -> int:
    W = BASE / WS_BRANDEIS
    # ★★ 自测建在**真语料**上，而语料按裁定不进 git。
    #   在别人 clone 出来的树里，第一版**直接抛异常**——
    #   [[untested-fallback-branches-only-fire-on-their-machine]]：
    #   「没装就跳过」那条路我从没走过。
    #   ⇒ 语料不在就**明说未跑并给独立退出码 5**，不许崩，也不许打 ✓。
    led = W / "evidence" / "source-ledger.jsonl"
    if not led.exists() or not any((W / "raw").glob("*.txt")):
        print("★★ **未跑，不是通过**：本件自测建在真语料上，而语料不在这棵树里。")
        print(f"   需要：{W / 'raw'}/*.txt（见仓根 START-HERE.md「语料在哪」一节）")
        print(f"   退出码 {SKIP_NO_CORPUS} = 跳过；0 = 全过；1 = 有不符。")
        return SKIP_NO_CORPUS
    recs = {r["source_id"]: r for r in
            (json.loads(l) for l in (W / "evidence" / "source-ledger.jsonl")
             .read_text(encoding="utf-8").splitlines() if l.strip())}
    bad = 0
    print("### 正对照：三个**人读出来的**导言边界")
    for sid, want, ev in KNOWN:
        t = norm_text(W / "raw" / pathlib.Path(recs[sid]["local_path"]).name)
        got, why = body_start(t, recs[sid].get("title", ""))
        ok = got is not None and abs(got - want) <= TOL
        bad += 0 if ok else 1
        print(f"  {'✓' if ok else '✗'} {sid} 期望 {want} 实得 {got}"
              f"（占全文 {why.get('占全文', '—')}%）")
        print(f"      依据：{ev}")
        if not ok:
            print(f"      诊断：{why}")

    # 反对照：**把书眉词换成书里根本没有的词，必须报测不出**，而不是随便给个数。
    print("\n### 反对照：书眉对不上时必须报 null（不许猜）")
    t = norm_text(W / "raw" / pathlib.Path(recs[KNOWN[0][0]]["local_path"]).name)
    got, why = body_start(t, "Zzyzx Qwerty Vorpal")
    ok = got is None
    bad += 0 if ok else 1
    print(f"  {'✓' if ok else '✗'} 假题名 → {got}（{why.get('为什么', '')}）")

    # ★★ 反对照三：**这一份根本没有书眉**，题名短语只在正文里散落 8 处，
    #   末尾几处扎堆。第一版据此判「正文从 91% 开始」——荒谬而绿灯。
    print("\n### 反对照：扎堆但不周期，必须报 null")
    for sid in ("src-696d2c185f7d", "src-dc08306e597b"):
        t3 = norm_text(W / "raw" / pathlib.Path(recs[sid]["local_path"]).name)
        g3, w3 = body_start(t3, recs[sid].get("title", ""))
        ok3 = g3 is None
        bad += 0 if ok3 else 1
        print(f"  {'✓' if ok3 else '✗'} {sid}（无书眉的辩状）→ {g3}｜{w3.get('为什么', '')}")

    # 反对照：**正文里的普通句子不该被当成书眉**——用一份没有该书眉的源试。
    other = "src-ea2c7920700d"
    t2 = norm_text(W / "raw" / pathlib.Path(recs[other]["local_path"]).name)
    got2, why2 = body_start(t2, recs[KNOWN[0][0]].get("title", ""))
    ok2 = got2 is None
    bad += 0 if ok2 else 1
    print(f"  {'✓' if ok2 else '✗'} 拿 A 书的题名去测 B 书 → {got2}（{why2.get('为什么', '')}）")

    print(f"\n{'✓ 正负对照全过' if bad == 0 else f'✗ {bad} 项不符'}"
          f"（正 {len(KNOWN)} 例边界逐字读过、反 4 例）")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw")
    ap.add_argument("--ledger")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.raw and a.ledger):
        print("要么 --self-test，要么同时给 --raw 与 --ledger", file=sys.stderr)
        return 2
    rows, unread = run(pathlib.Path(a.raw), pathlib.Path(a.ledger))
    if not rows:
        print("读不到任何正文", file=sys.stderr)
        return 4
    det = [r for r in rows if r["正文起点"]]
    out = {
        "源数": len(rows),
        "测出正文起点": len(det),
        "★ 测不出的": len(rows) - len(det),
        "★ null 的含义": "**没测出来**，不是「没有导言」——调用方必须分开处理",
        "读不到正文": unread,
        "逐条": sorted(rows, key=lambda r: -(r["正文起点"] or 0)),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
