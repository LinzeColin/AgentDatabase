#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#118 Elizabeth Blackwell 断言层。

## 三条硬口径

1. **每条 `fact` 必须带可核的专名或数字**，且回语料核过。
   （Galen #101 的 −0.1259 根因就是事实密度过低。）
2. **非事实类必须引互相独立的作品**——不是草稿＋它的印本。
   本人物实测：LoC 33 份讲稿手稿里 **18 份是印本的草稿**（重叠 51–90%），
   引这样一对，字面两个 id、实质一处证据。
   `check_claim_source_independence`（v0.0.0.82）会当场报出来。
   独立作品清单见 `INDEP`，分组见 `_work_groups.json`。
3. **不许从这几处取引文**：
   - 16 册日记里的印刷扉页（邮资表/印花税则/王室年表，占 4.1%，1885–93 三册达 9.7–13.4%）
   - `contaminated-1247` / `contaminated-1265`（整版报纸剪贴簿，已标 U）
   - `sp-1261` 第 1797–1811 行（末尾接的一栏「SITUATIONS WANTED」求职广告）
   - 一般通信 10 卷与书评剪报（**那是别人写的**）

## 编号

`claim_id` 是 `clm-<12 位十六进制>`，从可读键派生
（`common.markdown_claim_markers` 的正则认的就是这个；Barton #117 我自造了
`clm-and-01` 这种可读编号，58 条标记一个都没被认到）。
可读键留在 `claim_key`。
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TARGET = HERE / "workspaces" / "elizabeth-blackwell"

LED = {}
for line in (TARGET / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        r = json.loads(line)
        LED[pathlib.Path(r["local_path"]).stem] = r["source_id"]

def sid(stem: str) -> str:
    if stem not in LED:
        raise SystemExit(f"✗ **台账里没有 `{stem}`**——短名写错了，不许硬编 source_id")
    return LED[stem]

# ── 互相独立的作品（**非事实类只许从这里挑**）──────────────────────
PW   = "pioneer-work-1895"                      # 自传
MEW  = "medical-education-women-1864"           # 与 Emily 合署的建制文本
MPW  = "medicine-profession-women-1860"         # 同上，姐妹合备
LOL  = "laws-of-life-1852"                      # 女子体育讲义
CTP  = "counsel-to-parents-1878"
ROH  = "religion-of-health-1878"
HES  = "human-element-sex-1894"
WRM  = "wrong-right-methods-1883"
DMG  = "decay-municipal-govt-1885"
BM   = "benevolence-malthus-1888"
IOW  = "influence-of-women-1890"
SMB  = "scientific-method-biology-1898"
EV1  = "essays-medical-sociology-v1-1902"
EV2  = "essays-medical-sociology-v2-1902"
L47  = "letter-parsons-1847-10-29"
L48  = "letter-parsons-1848-06-24"
L51  = "letter-parsons-1851-12-07"

# ── fact：每条带可核专名或数字，均已回原文核过 ─────────────────────
FACTS = [
 ("geneva-1847", PW,
  "她 1847 年 10 月进入 Geneva Medical College；自传里那封信的落款是「Geneva: October 20, 1847.」。"),
 ("entered-1847-reaction", MEW,
  "她自述入学时当地舆论的反应：「When I entered college in 1847, the ladies of the town pronounced "
  "the undertaking crazy, or worse, and declared they would die rather than employ a woman as a physician.」"),
 ("blockley-1848", L48,
  "1848 年夏她在费城 Blockley Almshouse 实习——那年 6 月 24 日给 Anna Q. T. Parsons 的信抬头就是"
  "「Blockley June 24th 1848」；自传另记「a large room on the third floor had been appropriated to my use」。"),
 ("maternite-1849", PW,
  "1849 年赴巴黎入 La Maternité 产科医院——自传写她的第一个目标是进这所"
  "「a world-famous institution」并留到目标达成为止。"),
 ("infirmary-incorporated-1854", MEW,
  "New York Infirmary 于 1854 年立案：「This lustitution was incorporated iu 1854.」"
  "（`lustitution`／`iu` 为 OCR 原样，未代改。）"),
 ("infirmary-26000", MEW,
  "到 1864 年那份建制文本写作时，该院七年间诊治病人 26,000 人次："
  "「During the past seven years it has relieved 26,000 patients.」"),
 ("infirmary-1854-adoption", PW,
  "自传目录把 1854 年这一年并列记为三件事：New York Infirmary 开办、购置房产、以及收养一个孩子"
  "（养女 Kitty Barry）。"),
 ("kossuth-1851", L51,
  "第三封致 Parsons 的信馆方只著录为「18--」；**年份是内证推定的 1851**——"
  "信中写「昨天见到我们的匈牙利英雄」，指 Kossuth 1851 年 12 月访纽约，"
  "信末署「44 University Place, New York」。"),
 ("brothels-1849", WRM,
  "她引 1849 年的数字论证监管失效：人口 314,000、妓院 211 家、在册者 538 人"
  "（「In 1849, with a population of 314,000, and an inert public opinion, "
  "there were 211 brothels, with 538 inmates.」）。"),
 ("london-death-rate", IOW,
  "她指出伦敦死亡率通行的「每千人 23 或 24」其实是未知数，因为人口大进大出："
  "「is really an unknown quantity, on account of the enormous influx of fresh life」。"),
 ("essays-1902-hastings", EV1,
  "《Essays in Medical Sociology》两卷 1902 年出版，序言署「HASTINGS, May 1902」——"
  "黑斯廷斯是她晚年的居所。"),
 ("coauthored-1860", MPW,
  "1860 年那篇《Medicine as a Profession for Women》**是姐妹二人合备**："
  "正文写「lecture was prepared by Drs. Elizabeth and Emily Blackwell」；"
  "1864 年那篇扉页同样署「DRS. E. AND E. BLACKWELL」。"),
 ("private-circulation-1880", "human-element-sex-1880",
  "《The Human Element in Sex》1880 年初版是私印本，扉页标「For Private Circulation.]」，"
  "并注明「ADDRESSED TO STUDENTS OF MEDICINE」；1894 年由 J. & A. Churchill 出公开版。"),
 ("moral-reform-union-1885", DMG,
  "《On the Decay of Municipal Representative Government》1885 年由 Moral Reform Union 刊行，"
  "署「By Dr. ELIZABETH BLACKWELL」。"),
 ("london-school-1890", IOW,
  "1890 年《The Influence of Women in the Profession of Medicine》是她在"
  "London School of Medicine for Women 的开学致辞。"),
 ("juvenile-1830", "sp-1267-misc--notes-3-3-1830-年少年习作本",
  "现存最早的文体样本是 1830 年的少年习作本，档案著录为"
  "「Eliz. Blackwell's notebook 1830 with various compositions」——那年她九岁。"),
 ("pen-name", "sp-1272-stories-and-translations-3-3",
  "她用过笔名写故事：档案卡片注明《Margaret St. Omer》"
  "「by E. H. Lane in Dr. Eliz. writing written under pen name」。"),
 ("diaries-span", "sp-1263-bibliography",
  "LoC《Elizabeth Blackwell Papers》收她 1836–1908 年的日记 16 册，"
  "起自 1836 年那册首页自题的「Private Journal. Elizabeth」。"),
 ("works-by-same-author", SMB,
  "1898 年《Scientific Method in Biology》书前的「WORKS BY THE SAME AUTHOR」栏"
  "列出了《Pioneer Work in Opening the Medical Profession to Women》。"),
 ("hannah-1848", "fam-975-hannah-blackwell-母",
  "1848 年 7 月她在北卡罗来纳 Asheville 教书攒学费，写给母亲的信抬头是"
  "「Asheville July 27, 1848. My dear Mother」。"),
]

# ── 非事实类：**每条引两部互相独立的作品** ─────────────────────────
PATTERNS = [
 ("prevention-over-cure", "mental-model", [EV2, LOL],
  "她把卫生（sanitation）放在治疗之前，且认为它不止防病、很大程度上也治病："
  "「it is to sanitation that we must look, not only for the prevention of disease, "
  "but largely also for its cure.」这不是把预防当补充，是把因果次序倒过来。",
  ["1902 年文集里论卫生大会为何失败", "1852 年女子体育讲义"],
  ["Essays in Medical Sociology 卷二", "The Laws of Life"]),
 ("moral-law-on-acts", "value", [EV1, WRM],
  "她坚持医学与公共卫生的判断受道德律约束，不能只按效用算："
  "「This act, like all human acts, is subjected to the inexorable rule of moral law.」"
  "这是她反对以「管理」处理卖淫的根，不是附带的道德感慨。",
  ["1902 年文集里论人的行为", "1883 年论对待社会罪恶的对错方法"],
  ["Essays in Medical Sociology 卷一", "Wrong and Right Methods"]),
 # ★ 原引 [EV2, SMB]，被 check_claim_source_independence 当场报出：
 #   SMB 经 sp-1257 与 Essays 卷二传递合并成一组（那篇本就收进了文集）。
 #   改引 1894–96 日记——**她私下持续记这件事，是真独立的第二处**。
 #   （1903–05 那册命中更多，但它是 holdout，不许用。）
 ("vivisection-two-aspects", "heuristic", [EV2, "diary-1894-1896-mss966"],
  "她判活体解剖时**同时看两面**：智识上的与道德上的——"
  "「must be considered by us both under its intellectual and its moral aspects」；"
  "并给出智识面的判断：「vivisection is examination of the beginning of death, not of life」。"
  "凡遇到「这么做有用」的辩护，她的做法是把有用性与其代价分开各判一次。",
  ["1902 年文集里论活体解剖", "1894–96 日记里的私下记述"],
  ["Essays in Medical Sociology 卷二", "Diary 1894-96"]),
 ("family-physician", "work-method", [MEW, MPW],
  "她主张女医师的位置在**家庭医生**这一层，理由是那里最需要「wide & varied experience」"
  "与实际知识——不是专科的技艺，而是长期在场的判断。"
  "两份建制文本（1860、1864）都从这里立论。",
  ["1864 年论女性医学教育的演说", "1860 年论医业作为女性的职业"],
  ["Address on the Medical Education of Women", "Medicine as a Profession for Women"]),
 ("physical-education-first", "heuristic", [LOL, CTP],
  "她处理女性健康问题的顺序是**先体育、后医药**：1852 年的《Laws of Life》整本讲女孩的体育，"
  "1878 年《Counsel to Parents》里她回指这件事——「二十八年前开始行医时…我写了女子体育讲义」。"
  "遇到病症，她先问成长期的身体是怎么被养成的。",
  ["1852 年女子体育讲义", "1878 年给父母的忠告"],
  ["The Laws of Life", "Counsel to Parents"]),
 ("against-regulation", "boundary", [WRM, EV1],
  "她拒绝以国家监管卖淫（英国《传染病法案》那一路）来控制性病，"
  "理由不是效果不彰而是那条路把人当手段。**她不接受「先救急、道德以后再说」这个交换。**",
  ["1883 年论对待社会罪恶的对错方法", "1902 年文集里的相关篇章"],
  ["Wrong and Right Methods", "Essays in Medical Sociology 卷一"]),
 ("whole-not-parts", "mental-model", [SMB, EV1],
  "她反对把生命现象化约为部件与机制，主张从整体与其功能去看——"
  "这也是她反活体解剖在智识面上的同一个根，而不是两件事。",
  ["1898 年论生物学的科学方法", "1902 年文集卷一"],
  ["Scientific Method in Biology", "Essays in Medical Sociology 卷一"]),
 # ★★★ 已删除：`private-then-public`（「先私印流通、再公开出版」）
 #
 #   它很可能是真的：1880 年《The Human Element in Sex》扉页标 `For Private Circulation.]`，
 #   1894 年才由 J. & A. Churchill 出公开版。**但语料里找不到第二部独立作品支持它。**
 #
 #   两次尝试都被 `check_claim_source_independence` 当场报出：
 #     ① 引 1880 版 + 1894 版 —— **那是同一部书的两个版次**，
 #        而我自己的断言正文里就写着「十四年后才由 Churchill 出公开版」；
 #     ② 改引《Responsibility of Women Physicians》（另一份标 `Printed for private circulation` 的）
 #        —— 它经「1894 版 → sp-1244 手稿 → Essays 卷一 → sp-1256」传递，**仍在同一组**。
 #
 #   **删掉，不为凑第二处证据去挑一份实为同物的源。**
 #   那件事已写进 fact 断言 `private-circulation-1880`（单源，fact 不要求多源）。

 ("generalization-needs-accumulation", "mental-model", [EV1, LOL],
  "她要求普遍结论必须建立在**累积的准确事实**上，而且承认这需要世代之功："
  "「Function and use are only proved by observation, reflection, and rational experiment "
  "patiently carried on age after age, with generalization based upon accurate and accumulated facts」。"
  "**功能与用途只能被证明，不能被推定**——这条同时用在生理学与教育上。",
  ["1902 年文集论功能与用途如何被证明", "1852 年从生理讲女孩的成长"],
  ["Essays in Medical Sociology 卷一", "The Laws of Life"]),
 # ★ 原引 [EV1, CTP]，判据报出同组（Counsel to Parents 的内容也进了文集卷一）。
 #   改引 CTP + WRM：亲职责任 vs 社会罪恶里的责任，**两部独立作品**。
 ("responsibility-is-the-unit", "mental-model", [CTP, WRM],
  "她分析社会问题时的基本单位是**责任落在谁身上**，不是行为本身。"
  "论卖淫时她的定义就写在责任上——「with no responsibilities ; and no care for offspring」；"
  "论亲职时同样——「The precious but perilous responsibilities of the parent to the child」。"
  "**换议题不换单位。**",
  ["1878 年论父母对子女的责任", "1883 年论社会罪恶中的责任归属"],
  ["Counsel to Parents", "Wrong and Right Methods"]),
 ("distrust-the-headline-rate", "heuristic", [EV2, BM],
  "遇到一个通行的比率，她先问它的分母是什么。伦敦死亡率「通常说是每千人 23 或 24」，"
  "她判为「really an unknown quantity」——因为人口大进大出，分母根本不稳。"
  "同一个动作也用在马尔萨斯式的人口算计上。**先拆分母，再谈结论。**",
  ["1902 年文集论英国死亡率的真实数字", "1888 年论马尔萨斯式的仁慈"],
  ["Essays in Medical Sociology 卷二", "A Medical Address on the Benevolence of Malthus"]),
 ("experience-licenses-speech", "heuristic", [CTP, PW],
  "她开口讲一个题目之前，先说明自己凭什么讲——凭的是行医年数与亲历："
  "「The experience gained during a generation of active medical work has brought another subject "
  "before me」、「I know, however, from long medical experience, that such instruction is now needed」。"
  "自传通篇也是这个结构：先记亲历，再下判断。**不凭立场发言，凭在场发言。**",
  ["1878 年给父母的忠告的开场自陈", "1895 年自传的叙述结构"],
  ["Counsel to Parents", "Pioneer Work"]),
 ("no-exception-to-the-rule", "heuristic", [EV1, WRM],
  "碰到「这一次可以通融」的主张，她的回法是指出规则不能自相矛盾——"
  "「Divine law admits of no exception, it cannot contradict itself.」"
  "《传染病法案》之争里她用的正是这一招：**不争这次的后果，争「开这个例子」本身能不能成立。**",
  ["1902 年文集论例外", "1883 年论对待社会罪恶的对错方法"],
  ["Essays in Medical Sociology 卷一", "Wrong and Right Methods"]),
 ("credential-then-argument", "heuristic", [PW, MEW],
  "她的路径是**先取得资格，再用资格说话**：1849 年拿到学位之后，才有 1860、1864 那些"
  "以「Drs. E. and E. Blackwell」署名的建制文本。自传通篇的结构也是如此——"
  "先记怎么被拒、怎么进去，再记开办机构。",
  ["1895 年自传", "1864 年建制演说"],
  ["Pioneer Work", "Address on the Medical Education of Women"]),
 ("municipal-decay", "value", [DMG, BM],
  "她把公共卫生的失败归到市政代议制的败坏与人口论式的算计上，"
  "而不是归到医学知识不足——1885 与 1888 两篇分别打这两处。"
  "**她认为挡在健康前面的是治理与观念，不是技术。**",
  ["1885 年论市政代议制的败坏", "1888 年论马尔萨斯式的仁慈"],
  ["On the Decay of Municipal Representative Government", "A Medical Address on the Benevolence of Malthus"]),
]


def cid(key: str) -> str:
    return "clm-" + hashlib.sha256(("blackwell-" + key).encode()).hexdigest()[:12]



# ★ 每条非事实断言的置信度与**证伪条件逐条写**，不套模板——
#   模板化的 falsifier 等于没有 falsifier（「若本条不成立则本条作废」是同义反复）。
CONF = {
 "prevention-over-cure": (0.85,
   ["若在 1852–1902 的著作里找不到「卫生先于治疗」的表述，"
    "或找到她把治疗置于卫生之前的表述，本条作废。"]),
 "moral-law-on-acts": (0.85,
   ["若她在公共卫生议题上曾以纯效用理由压过道德理由，本条应下调为 hypothesis。"]),
 "vivisection-two-aspects": (0.80,
   ["若她判活体解剖时只谈道德不谈智识（或反之），「同时看两面」这条作废。"]),
 "family-physician": (0.80,
   ["若 1860／1864 两份建制文本主张女医师应走专科而非家庭医生，本条作废。"]),
 "physical-education-first": (0.80,
   ["若《Counsel to Parents》里那句自述不指向 1852 年的体育讲义，回指链断，本条下调。"]),
 "against-regulation": (0.85,
   ["若她曾支持以国家登记或强制检查来管理卖淫，本条作废。"]),
 "whole-not-parts": (0.75,
   ["若《Scientific Method in Biology》主张化约式说明优于整体说明，本条作废。"]),
 "generalization-needs-accumulation": (0.80,
   ["若她在别处以单例直接下普遍结论而不加限度声明，本条应下调为 hypothesis。"]),
 "responsibility-is-the-unit": (0.75,
   ["若她论社会问题时主要以行为本身（而非责任归属）为分析单位，本条作废。"]),
 "distrust-the-headline-rate": (0.80,
   ["若她引用通行比率时不追问其分母/口径，本条作废。"]),
 "experience-licenses-speech": (0.75,
   ["若她开题时以立场或权威而非亲历自陈资格，本条作废。"]),
 "no-exception-to-the-rule": (0.75,
   ["若她在某处接受了「此例特殊故可通融」的论证，本条作废。"]),
 "credential-then-argument": (0.70,
   ["若她在取得学位之前已发表同类建制主张，「先取资格再发言」这条作废。"]),
 "municipal-decay": (0.75,
   ["若 1885／1888 两篇把公共卫生的失败主要归于医学知识不足，本条作废。"]),
}

# 必填字段的公共部分（schema 见 `ledger.invalid` 那条门）
BASE = {"author_role": "distiller", "language": "en", "time_scope": "1821-1910",
        "created_at": "2026-08-04T00:00:00Z",
        "alternative_explanations": [], "counter_source_ids": []}


def main() -> int:
    rows = []
    for key, stem, text in FACTS:
        rows.append(dict(BASE, claim_id=cid(key), claim_key=key, category="fact",
                         status="fact", claim=text, source_ids=[sid(stem)],
                         contexts=["史实"], evidence_clusters=[stem],
                         confidence=0.9,
                         falsifiers=[f"若 `{stem}` 正文中查不到本条引的那句原文，本条作废。"]))
    for key, cat, stems, text, contexts, clusters in PATTERNS:
        conf, fals = CONF[key]
        ids = [sid(s) for s in stems]
        if len(set(ids)) < 2:
            raise SystemExit(f"✗ **{key} 的两份源是同一个 id**")
        rows.append(dict(BASE, claim_id=cid(key), claim_key=key, category=cat,
                         status="pattern", claim=text, source_ids=ids,
                         contexts=contexts, evidence_clusters=clusters,
                         confidence=conf, falsifiers=fals))
    out = TARGET / "evidence/claims.jsonl"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n",
                   encoding="utf-8")
    import collections
    print(f"写入 {len(rows)} 条断言 → {out}")
    print("  category 分布：", dict(collections.Counter(r["category"] for r in rows)))
    print("  不同的 source_ids 组合：", len({tuple(r["source_ids"]) for r in rows}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
