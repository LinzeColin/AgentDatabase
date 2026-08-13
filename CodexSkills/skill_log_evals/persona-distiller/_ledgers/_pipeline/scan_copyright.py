#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫正文里的**版权声明** —— PD 过滤的最后一道，也是唯一读正文的一道。

用法：
    python3 scan_copyright.py --raw <raw 目录> [--head 300]

## 为什么必须有（实测，2026-08-12）

前面几道过滤全靠 **IA 元数据**：`access-restricted-item` 与 `year > 1930`。
两道都没拦住这两份：

| identifier | 正文头里写着 |
|---|---|
| `FilosofaDeLaHistoriaEmmanuelKant` | **`D. R. © 2015, Fondo de Cultura Económica`**，ISBN 978-607-16-5067-2，Eugenio Ímaz 译，并明写 `Se prohíbe la reproducción total o parcial de esta obra` |
| `Kant-polmica-CRP` | **`© A. MACHADO LIBROS, S.A., 2002`**，ISBN 84-7774-758-x，Mario Caimi 译 |

**康德本人的文本是公有领域，这两个译本不是。**
它们过得了前两道，是因为 **IA 的 `year` 记的是原作年不是版次年**
（`_IA的date是原作年不是版次年-2026-08-11.md`）——
**元数据说得再干净，也得打开正文看一眼。**

同 [[aggregator-license-is-not-a-rights-claim]]：
Unpaywall 把在世作者的 Wiley 社论标成 public-domain；聚合器的字段不是权利声明。

## 判读规则（本工具**只报不删**）

- **红**：出现 `©`／`Copyright` **且**年份 > PD 分界；或出现 ISBN；
  或出现明确的禁止复制句（多语种）。
- **黄**：出现 `©`／`Copyright` 而取不到年份 —— **要人看**。
- **绿**：没有版权字样。★ 绿**不等于**已确认 PD，只等于「正文头里没写」。

★ Project Gutenberg 的 `Release Date: … [EBook #…]` **不是版权声明**，
  它是电子书发布日，底本仍是 PD ⇒ 单独识别，不计入红。

★ 退出码：0=扫完（**无论有没有红**）；2=参数错；3=没有可扫的文件。
  **成败看输出的计数，不要接管道判**（[[pipe-to-tail-hides-the-exit-code]]）。
"""
import argparse
import json
import pathlib
import re
import sys

THIS_YEAR = 2026
PD_CUTOFF = THIS_YEAR - 95            # 1931；可用最晚出版年 = 1930

COPY_RE = re.compile(r"(©|\([Cc]\)\s*\d{4}|[Cc]opyright|[Dd]erechos\s+reservados|"
                     r"[Aa]lle\s+Rechte\s+vorbehalten|[Tt]ous\s+droits\s+r[ée]serv[ée]s|"
                     r"[Tt]utti\s+i\s+diritti)")
ISBN_RE = re.compile(r"\bISBN[\s:]*[\d\-–—xX]{9,}")
FORBID_RE = re.compile(r"([Ss]e\s+proh[ií]be\s+la\s+reproducci|"
                       r"[Aa]ll\s+rights\s+reserved|"
                       r"[Nn]o\s+part\s+of\s+this\s+(book|publication)\s+may\s+be\s+reproduced|"
                       r"[Nn]achdruck\s+verboten)")
# Project Gutenberg 的发布日：**不是版权声明**
PG_RE = re.compile(r"Release\s+Date:[^\n\[]{0,40}(\d{4})[^\n]{0,20}\[E[Bb]ook")
YEAR_NEAR = re.compile(r"\b(1[5-9]\d{2}|20[0-2]\d)\b")


def judge(head: str) -> tuple:
    pg = bool(PG_RE.search(head))
    reasons, worst = [], "绿"
    if ISBN_RE.search(head):
        worst = "红"; reasons.append("有 ISBN（ISBN 制度 1970 年才有）：" + ISBN_RE.search(head).group(0)[:40])
    fb = FORBID_RE.search(head)
    if fb:
        worst = "红"; reasons.append("明确禁止复制：" + fb.group(0)[:50])
    for m in COPY_RE.finditer(head):
        seg = head[max(0, m.start() - 60):m.end() + 90]
        yrs = [int(y) for y in YEAR_NEAR.findall(seg)]
        late = [y for y in yrs if y > PD_CUTOFF - 1]
        if late:
            worst = "红"
            reasons.append(f"版权字样近旁有 {max(late)} 年：" + re.sub(r"\s+", " ", seg)[:80])
        elif not yrs and worst != "红":
            worst = "黄"
            reasons.append("有版权字样但取不到年份：" + re.sub(r"\s+", " ", seg)[:70])
    return worst, reasons, pg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--head", type=int, default=300)
    a = ap.parse_args()
    raw = pathlib.Path(a.raw)
    mf = raw / "_fetch-manifest.json"
    if not mf.exists():
        print(f"{mf} 不在", file=sys.stderr)
        return 2
    recs = [r for r in json.loads(mf.read_text(encoding="utf-8"))["记录"] if r["status"] == "已取回"]
    if not recs:
        print("没有可扫的文件", file=sys.stderr)
        return 3

    out = {"红": [], "黄": [], "绿": 0, "PG发布日": 0}
    # ★★ 2026-08-14：`missing` 是当天补的。原来这里只有 `if not p.exists(): continue`，
    #   而标题行印的是 `扫 {len(recs)} 份` —— **len(recs) 是台账里的条数，不是读到的份数**。
    #   在移交包的裸 clone 里实测：`扫 103 份`，而 `红 0｜黄 0｜绿 0`（合计 0）。
    #   103 ≠ 0，**它一份都没读到，却印出「红 0」并 rc=0**。
    #   「红 0」会被读成「没有版权问题」——而这是**版权**结论，是本项目最贵的那一种。
    #   [[green-in-the-repo-dead-in-the-package]]、[[empty-default-swallows-unknown]]
    missing = 0
    for r in recs:
        p = raw / r["file"]
        if not p.exists():
            missing += 1
            continue
        head = "\n".join(p.read_text(encoding="utf-8", errors="replace").splitlines()[:a.head])
        v, why, pg = judge(head)
        out["PG发布日"] += 1 if pg else 0
        if v == "绿":
            out["绿"] += 1
        else:
            ti = r.get("ia_title"); ti = "; ".join(ti) if isinstance(ti, list) else str(ti or "")
            out[v].append({"identifier": r["identifier"], "title": ti[:70], "理由": why})

    read_n = len(recs) - missing
    print(f"{raw}｜台账 {len(recs)} 份 → **真读到 {read_n} 份**"
          f"｜**读不到 {missing} 份**（头 {a.head} 行）")
    if missing:
        print(f"  ★★ **读不到的 {missing} 份没有被判过** —— 语料按裁定不进 git，"
              f"在裸 clone 里就是这个样子。**下面的「红 N」只覆盖真读到的那 {read_n} 份。**")
    if read_n == 0:
        print("  ❌ **一份都没读到 ⇒ 本次没有任何版权结论**。"
              "「红 0」在这里不是「没有版权问题」，是**没读到**。")
        (raw / "_copyright-scan.json").write_text(
            json.dumps({"未量": True, "台账份数": len(recs), "读到": 0},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        return 3
    print(f"  **红 {len(out['红'])}**｜黄 {len(out['黄'])}｜绿 {out['绿']}"
          f"｜其中 PG 发布日样板 {out['PG发布日']} 份（**不算红**）"
          f"　（红＋黄＋绿 = {len(out['红'])+len(out['黄'])+out['绿']}，应等于真读到的 {read_n}）")
    for v in ("红", "黄"):
        for o in out[v]:
            print(f"  [{v}] {o['identifier'][:38]:<40}{o['title']}")
            for w in o["理由"][:2]:
                print(f"        ↳ {w}")
    print("  ★ **绿不等于已确认 PD**，只等于「正文头里没写版权声明」")
    out["_覆盖面"] = {"台账份数": len(recs), "真读到": read_n, "读不到": missing}
    (raw / "_copyright-scan.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
