#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#118 六条道的研究文档 —— **从台账实算，不手写份数**。

## 口径

- 每条道列**它实际收了哪些源**（份数与字数都从台账/正文现算），
  并逐条给 `src-` 编号——`evaluate_research` 要的就是这个。
- **只列 train 侧**：holdout 不许出现在研究文档里（那 6 份是用来验泛化的）。
- 每份文档写明**这条道的证据强在哪、弱在哪**——弱处照实写，不粉饰。

## ★ 三处杂质在每份文档里都要复述一遍

写这些文档的人未必读过 `INGEST_TODO.md`：

1. 16 册日记混有商品袖珍日记本的**印刷扉页**（邮资表/印花税则/王室年表），
   实测 1885–87 占 9.7%、1888–90 占 12.2%、1891–93 占 13.4%，其余约 2%，合计 **4.1%**
2. `contaminated-1247` / `contaminated-1265` 是整版报纸剪贴簿，**已标 U**
3. `sp-1261` 末尾第 1797–1811 行接了一栏「SITUATIONS WANTED」求职广告（284 词 = 1.7%）

**引文不许引到这三处。**
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TARGET = HERE / "workspaces" / "elizabeth-blackwell"
OUT = TARGET / "references/research"

LANES = {
 "writings": ("01-writings.md", "著述",
   "**最厚的一条道**。15 部刊行著作（1852–1902）加上 LoC 的讲稿/文章/书稿手稿。\n\n"
   "★ **强在跨度**：从 1852 年的《The Laws of Life》到 1902 年的《Essays in Medical Sociology》"
   "两卷，整整五十年，同一条线（卫生／教育／道德）一路展开。\n\n"
   "★ **弱在独立性**：LoC 的 33 份讲稿手稿里 **18 份是印本的草稿**（重叠 51–90%）——"
   "它们是同一部作品的两个见证，**不算两处证据**。去重后独立作品 56 部。"),
 "conversations": ("02-conversations.md", "对谈与书信",
   "3 封 Middlebury/Abernethy 藏的致 Anna Q. T. Parsons 信（1847–1851），"
   "加上 LoC 家庭通信里**实测确认是她写出去的**那几卷。\n\n"
   "★ **方向必须逐卷读，不许按 folder 名推**：folder 名是通信对象，不指方向。"
   "11 卷家庭通信里 **4 卷实为寄给她的**（`Dear Aunt Elizabeth`、"
   "`Dear Doctor…send to you`、Henry 的《Woman's Journal》信笺、`Dear Cousin Elizabeth`），"
   "已改 S1；另 1 卷（Kitty Barry）**双向混装**（实测收 5/发 4），"
   "**从该卷取引文前必须先认清说话人**。\n\n"
   "★ 第三封信的年份是**内证推定的 1851**（Kossuth 1851 年 12 月访纽约），"
   "馆方只著录为 `18--`——**推定就写成推定**。"),
 "expression": ("03-expression.md", "文体样本",
   "诗、故事与译作、1830 年的少年习作本、演讲笔记，以及 1890 年伦敦女子医学院的开学致辞。\n\n"
   "★ **最早的样本是 1830 年那本**，档案著录为 "
   "`Eliz. Blackwell's notebook 1830 with various compositions`——那年她九岁。\n\n"
   "★ 她用过笔名：《Margaret St. Omer》档案卡片注 "
   "`by E. H. Lane in Dr. Eliz. writing written under pen name`。"),
 "external": ("04-external.md", "外部评述",
   "LoC 一般通信 10 卷（**寄给她的来信**）与书评剪报 1 卷。\n\n"
   "★ **收信人是她 ≠ 她写的**——这一整条道都标 S1/THIRD-PARTY，`author` 留空，"
   "**不计入一手占比**。其中 Florence Nightingale 卷档案标注 `from + To`，3,661 词。\n\n"
   "★ 这条道是本人物**最薄**的一条：只有 11 份，且都在 LoC 一处。"
   "同时代医学界对她的系统评述（Waite 1947、Fleming 1956 等）**在版权期内，未取**。"),
 "decisions": ("05-decisions.md", "决策与建制文本",
   "1860《Medicine as a Profession for Women》、1864《Address on the Medical Education of Women》、"
   "1868 年 Woman's Medical College 开学辞、致校友会的正式抗议书。\n\n"
   "★ **两份最重的建制文本都是与妹妹 Emily 合署的**："
   "1860 年那篇正文自陈 `lecture was prepared by Drs. Elizabeth and Emily Blackwell`，"
   "1864 年那篇扉页署 `DRS. E. AND E. BLACKWELL`。"
   "**计入一手，但引用时不得写成她一人所言。**\n\n"
   "★ 这条道 5 份，是六条里第二薄的。LoC 的 *Subject File*（18 件）与 *Miscellany*（49 件）"
   "**本次未探测**——按序列名推测决策类材料多半在那里，**那是「未探测」不是「取不到」**。"),
 "timeline": ("06-timeline.md", "编年",
   "1895 年自传《Pioneer Work in Opening the Medical Profession to Women》为主干，"
   "加 LoC 的 16 册日记（1836–1908）与著作系年表。\n\n"
   "★ **关键锚点**：1847 年 10 月入 Geneva Medical College（自传里那封信落款 "
   "`Geneva: October 20, 1847.`）、1848 年夏在费城 Blockley Almshouse 实习、"
   "1849 年赴巴黎入 La Maternité、1854 年 New York Infirmary 立案。\n\n"
   "★ **日记不适合做事实断言**：逐日流水（天气、家用账、访客名单），"
   "它们的价值在编年与文体，不在事实密度。"),
}

CONTAM = ("\n---\n\n## ★ 三处杂质（引文不许引到这里）\n\n"
          "1. **16 册日记混有印刷扉页**——商品袖珍日记本前面印的邮资表、印花税则、王室年表，"
          "被众包连同手写一起转写。实测 1885–87 占 9.7%、1888–90 占 12.2%、1891–93 占 13.4%，"
          "其余约 2%，全 16 册合计 **4.1%**。\n"
          "2. **`contaminated-1247` / `contaminated-1265`** 是整版报纸剪贴簿（分类广告、"
          "地方法庭报道、股票行情），**已标 U，不计入 usable**。\n"
          "3. **`sp-1261` 末尾第 1797–1811 行**接了一栏「SITUATIONS WANTED」求职广告"
          "（约 284 词 = 1.7%），从她的句子中断处突起。\n\n"
          "**引文判据只验「这句话在语料里」——它分不出这三处不是她的话。**\n")


def main() -> int:
    rows = [json.loads(l) for l in
            (TARGET / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for lane, (fname, zh, body) in LANES.items():
        got = [r for r in rows if r.get("split") == "train" and lane in (r.get("dimensions") or [])]
        if not got:
            print(f"  ✗ **{lane} 一份都没有**"); return 1
        words = 0
        for r in got:
            p = TARGET / r["local_path"]
            if p.is_file():
                words += len(p.read_text(encoding="utf-8", errors="replace").split())
        lines = [f"# {zh}（`{lane}`）", "",
                 f"**train 侧 {len(got)} 份，合计 {words:,} 词**（份数与字数由 `gen_lanes.py` "
                 f"从台账与正文现算，不手写）。holdout 的 6 份**不列在此**。", "",
                 body, "", "## 逐份清单", "",
                 "| 来源编号 | 档 | 篇名 |", "|---|---|---|"]
        for r in sorted(got, key=lambda x: x.get("tier", "")):
            title = str(r.get("locator") or "").split("｜")[0][:70] or pathlib.Path(r["local_path"]).stem
            lines.append(f"| `{r['source_id']}` | {r.get('tier')} | {title} |")
        lines.append(CONTAM)
        (OUT / fname).write_text("\n".join(lines) + "\n", encoding="utf-8")
        total += len(got)
        print(f"  {lane:<14} {len(got):>3} 份　{words:>9,} 词 → {fname}")
    print(f"\n六条道合计（含跨道重复计）{total} 份")
    return 0


if __name__ == "__main__":
    sys.exit(main())
