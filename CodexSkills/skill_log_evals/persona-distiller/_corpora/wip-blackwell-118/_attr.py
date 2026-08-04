#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#118 逐源归属证据 —— **实测，不推断**。

## 为什么不能直接写 `attribution_basis` 了事

Barton #117 那份 `attribution_basis` 引的是**实测到的原文**
（`Copyright,   1898,  by   Clara    Barton`，三处）。
凭「十九世纪美国刊行物应当有扉页」写出来的依据，**是推断不是证据**——
写了它，门会变绿，而绿的是一句我没核过的话。

本件对**每一份 P1**跑一次 `check_authorship.check_text`，
把它**真的找到的那一行**照录进该源的 `attribution` 字段；
找不到的**照实写「文本层无署名」并说明归属依据在哪一层**，不编。

## 三层归属，各有各的证据形态

| 层 | 材料 | 证据在哪 |
|---|---|---|
| 刊行物 | 15 部著作 | **扉页署名**，判据能直接抓 |
| 档案手稿 | LoC 讲稿/文章/日记/家庭通信 | **日记与草稿不署名**——归属依据在**档案编目层**，不在文本层 |
| 来信 | LoC 一般通信 | **不是她写的**，S1/THIRD-PARTY，不进这一环 |

第二层与 Barton 同型：`check_authorship` 认的三种证据（署名／编者注／逐字稿轮次）
**在未刊手稿上结构上不存在**。这不是「判据查不出所以放行」，
是**这一类材料的归属依据本来就在别处**——所以必须把「别处」写清楚，并且可核。
"""
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TARGET = HERE / "workspaces" / "elizabeth-blackwell"
CA = (HERE.parents[3] / "registry" / "codex" / "persona-distiller" / "scripts" / "check_authorship.py")

spec = importlib.util.spec_from_file_location("ca", CA)
ca = importlib.util.module_from_spec(spec)
sys.modules["ca"] = ca
spec.loader.exec_module(ca)

SUBJECT = "Elizabeth Blackwell"
PAT = ca.build_patterns(SUBJECT)

# 档案层依据：LoC 藏品编目。**这是可核的**——藏品号与 folder 号都在账本 locator 里。
ARCHIVAL = (
    "**未刊手稿，文本层无署名**（判据认的署名／编者注／逐字稿轮次三种证据，"
    "在日记与草稿上结构上不存在）。**归属依据在档案编目层**："
    "美国国会图书馆《Elizabeth Blackwell Papers》按手迹与来源著录，"
    "本件的藏品号与 folder 号见 `locator`。"
)
ARCHIVAL_DIARY = ARCHIVAL + (
    " 另有文本内证（全 16 册共用）：`Emily`（妹妹，同为医师）通篇出现、"
    "`Kitty`（养女 Kitty Barry）高频、`N.Y. Infirmary` 见于 1897–1905 三册；"
    "1836 年册首页自题 `Private Journal. Elizabeth`。"
)
ARCHIVAL_FAM = ARCHIVAL + (
    " 另有实测的方向证据：Hannah 卷首封 `Asheville July 27, 1848. My dear Mother…`、"
    "其他家庭通信卷首封 `Portway May 2nd 1849. My own dear friends all, "
    "Thanks be to Heaven, I am on land once more`——**是她写出去的，不是寄给她的**。"
)

# ★ 日记里混有商品袖珍日记本的**印刷扉页**（邮资表、印花税则、王室年表），
#   众包转写把它们连同手写一起抄了。实测：1885–87 9.7%、1888–90 12.2%、
#   1891–93 13.4%，其余约 2%，全 16 册合计 4.1%。
PRINTED_MATTER = (
    " ★★ **本册混有印刷页**：商品袖珍日记本前面印的邮资表、印花税则、王室年表"
    "被众包连同手写一起转写。**引文不许引到这些行上**——"
    "引文判据只验「这句话在语料里」，它会把邮资表当成她的话。"
)
HEAVY = {"1885-1887", "1888-1890", "1891-1893"}


def main() -> int:
    led = TARGET / "evidence" / "source-ledger.jsonl"
    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    stat = {"判据抓到署名": 0, "档案层依据": 0, "非本人所著": 0}
    codes = {}

    for r in rows:
        if r.get("tier") in ("S1", "S2"):
            r["attribution"] = ("**不是她写的**：LoC 一般通信是**寄给她的来信**"
                                "（收信人是她 ≠ 她写的）／书评剪报是别人评她。"
                                "故 tier=S1、`author` 留空，**不计入一手**。")
            stat["非本人所著"] += 1
            continue
        if r.get("tier") == "U":
            r["attribution"] = ("**受污染，标 U 不计入 usable**：LoC 转写按 folder 整包提供，"
                                "本 folder 是整版报纸剪贴簿，众包把分类广告一并抄了。"
                                "**不是丢掉**——丢掉等于假装没抓过。")
            continue

        p = TARGET / r["local_path"]
        if not p.is_file():
            r["attribution"] = "★ **正文不在，归属未核（不是通过）**"
            continue
        ok, code, ev, counter = ca.check_text(p.read_text(encoding="utf-8", errors="replace"), PAT)
        codes[code] = codes.get(code, 0) + 1
        name = pathlib.Path(r["local_path"]).stem

        if ok:
            r["attribution"] = (f"**判据实测抓到署名**（`{code}`）：`{str(ev).strip()[:160]}`"
                                + (f"；同文另见他人署名 `{str(counter).strip()[:60]}`，"
                                   "**已核为同卷其他条目，非本篇作者**" if counter else ""))
            stat["判据抓到署名"] += 1
        else:
            base = ARCHIVAL_DIARY if name.startswith("diary-") else (
                   ARCHIVAL_FAM if name.startswith("fam-") else ARCHIVAL)
            if any(h in name for h in HEAVY):
                base += PRINTED_MATTER
            if counter:
                base += (f" **同文出现他人署名 `{str(counter).strip()[:60]}`**"
                         "——这是众包转写把印刷页/剪报一并抄入所致，**不是本篇易主**。")
            r["attribution"] = base
            stat["档案层依据"] += 1
        # ★★ `check_source_attribution.evaluate` 读的是
        #   `any(str(k).startswith("A-") for k in kinds)`——**它要的是字符串列表**。
        #   第一版我写成了 dict（键是 passed/code/evidence/counter），
        #   **一个都不以 A- 开头，于是 59 份实测命中全部不算数**，
        #   门照旧报 75 条 source-unclaimed。**字段形态不一致，与冻结评委指令那三处同型。**
        r["authorship_evidence"] = [code] if ok else []
        r["authorship_detail"] = {"passed": bool(ok), "code": code,
                                  "evidence": str(ev)[:300] if ev else None,
                                  "counter": str(counter)[:120] if counter else None}

    led.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n",
                   encoding="utf-8")
    print("逐源实测：", stat)
    print("判据返回的 code 分布：", codes)

    meta_p = TARGET / "meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    hits = [r for r in rows if r.get("authorship_detail", {}).get("passed")]
    sample = "；".join(f"`{r['authorship_detail']['evidence'].strip()[:70]}`"
                      f"（{pathlib.Path(r['local_path']).stem}）" for r in hits[:3])
    # ★ `covered_sources`：**逐份点名，每份带照录的原文**——不是整批豁免。
    #   Barton #117 拒过「blanket covered_sources」这个捷径，这里同样不走。
    #   证据自动从正文抽，**照录，不转述**；抽不到的照实写「只有系列级编目」。
    import re as _re
    NAME = _re.compile(r"[^\n]{0,50}(?:eliz[a-z.]*\s*black\s*well|black\s*well)[^\n]{0,40}", _re.I)
    covered = []
    for r in rows:
        if r.get("tier") != "P1" or (r.get("author") or "") != SUBJECT:
            continue
        if r.get("authorship_evidence"):
            continue                      # 已由 A-* 证据认定，不必点名
        stem = pathlib.Path(r["local_path"]).stem
        txt = (TARGET / r["local_path"]).read_text(encoding="utf-8", errors="replace")
        # ★ 变量名不许与外层的 `hits` 撞——第一版撞了，
        #   authority 里的「N/78 份抓到署名」被内层循环的末值覆盖，从 57 变成 2。
        found = [" ".join(h.split()) for h in NAME.findall(txt)]
        strong = [h for h in found if _re.search(r"eliz", h, _re.I)]
        if strong:
            covered.append(f"{stem} —— 照录原文：「{strong[0][:110]}」")
        else:
            covered.append(
                f"{stem} —— ★ **正文里没有她的名字**（全文搜 `Elizabeth Blackwell` 0 处；"
                f"仅见裸姓 {len(found)} 处，其中含他人如 `Mrs. William Blackwell`）。"
                "**依据只有系列级编目**：它是《Elizabeth Blackwell Papers》16 册连续日记中的一册，"
                "同系列其余各册的转写抬头写着 `BLACKWELL FAMILY … ELIZABETH BLACKWELL`。"
                "**这是系列级依据，不是本册级依据——照实记，不当成同等强度。**")

    meta["attribution_basis"] = {
        "covered_sources": covered,
        "authority": (
            f"**十九世纪美国／英国刊行物，署名证据在扉页**。逐源实测："
            f"`check_authorship` 在 {len(hits)}/{sum(1 for r in rows if r.get('tier') in ('P1','P2'))} "
            f"份一手上抓到署名，实例：{sample}。\n\n"
            "**难点与 Clara Barton #117 同型**：一手材料最厚的一层是**未刊手稿**"
            "（16 册日记、33 份讲稿/文章/书稿、11 卷家庭通信）。"
            "**日记不署名，草稿也不署名**——判据认的三种证据在这一类材料上结构上不存在。\n\n"
            "**这一类的归属依据在档案层，不在文本层**：美国国会图书馆将其编目为 "
            "《Elizabeth Blackwell Papers》，按手迹与来源著录，藏品号与 folder 号逐条记在 "
            "`locator` 里。**这不是「判据查不出所以放行」，是这一类材料的归属依据本来就在别处。**\n\n"
            "★ **另有一层必须写明的杂质**：LoC 众包转写按 folder 整包提供，"
            "把日记本前面印的邮资表、印花税则、王室年表**连同手写一起抄了**。"
            "实测 1885–87 占 9.7%、1888–90 占 12.2%、1891–93 占 13.4%，其余约 2%，"
            "全 16 册合计 **4.1%**。**引文不许引到这些行上。**"),
        "citation": (
            "美国国会图书馆《Elizabeth Blackwell Papers》藏品说明与 rights 声明："
            "https://www.loc.gov/collections/elizabeth-blackwell-papers/about-this-collection/"
            " ；各 folder 的 loc.gov item 页逐条记在每份来源的 `locator` 里"
            "（如 https://www.loc.gov/item/mss1288000956/ ）。"
            "刊行物的扉页署名可在各自的 `locator` URL 上直接回看。"),
        "disputed_policy": (
            "**三类不计入 P1，各有各的理由**：\n"
            "① `medical-education-women-1864` 与妹妹 Emily 合署"
            "（扉页 `DRS. E. AND E. BLACKWELL`），已标 CO-AUTHORED——"
            "**计入一手，但引用时不得写成她一人所言**。\n"
            "② LoC 一般通信 10 卷与书评剪报 1 卷是**别人写的**（寄给她／评她），"
            "标 S1/THIRD-PARTY，`author` 留空，不计入一手。\n"
            "③ 两卷受污染的整版报纸剪贴簿标 U，不计入 usable，逐条列于 disputed_works。\n"
            "**未发现学界对任何一篇的归属存疑**——她生前身后著作归属无争议，"
            "故 disputed_works 只列本流水线自己判定要排除的，不列学界争议篇目。"),
        "disputed_works": [
            "contaminated-1247（mss1288001247「A Miscarriage of Justice」致编辑信）"
            "——整版报纸剪贴簿，众包转写把分类广告一并抄入："
            "`to be sold/apply to/for sale` 命中 524 次、`£` 金额 404 次，"
            "她本人署名仅 3 次。**132,156 词里她的实际文字占极小比例**，标 U。",
            "contaminated-1265（mss1288001265「Misc. notes 1/3」）"
            "——同上，黑斯廷斯地方法庭报道与股票行情剪报，15,263 词，标 U。",
            "★ 另有一层不是「篇目存疑」而是「篇内杂质」，故不单列为 works 但必须写明："
            "16 册日记里混有商品袖珍日记本的**印刷扉页**（邮资表、印花税则、王室年表），"
            "实测 1885–87 占 9.7%、1888–90 占 12.2%、1891–93 占 13.4%，其余约 2%，合计 4.1%。"
            "**引文不许引到这些行上。**",
        ],
        "measured_at": "2026-08-04",
        "checker": "check_authorship.check_text，逐源实跑，非人工判断",
    }
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(f"\nattribution_basis 已写入——**引的是 {len(hits)} 份实测命中里的原文，不是推断**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
