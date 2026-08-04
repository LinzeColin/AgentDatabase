#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#117 Clara Barton 的八份核心产物文档。

## 写法（照 Fleming #111 那几份过了门的）

- **每一条实质说法都挂 `src-` 编号**——`claim.orphan` 查的就是断言有没有落到产物里。
- **明写语料答不了的部分**（`⚠ 本工作区答不了：…不写`）。
  Fleming 的 persona.md 就是这么写的，而它过了门。
- **简短**。Fleming 三份分别是 1056 / 1737 / 1675 字节；堆字数不加分。
"""
import json
import pathlib

WS = pathlib.Path("workspaces/clara-barton/clara-barton")

AND   = "src-67c54d778d0b"   # andersonville-1866
ASIA  = "src-6b11e97cc16e"   # asia-minor-1896
D1862 = "src-18d580f61c05"   # diary-1862-jan-dec-1865
GEN   = "src-a44f7a83405a"   # geneva-convention-1881（扉页 1878）
ATW   = "src-e570c8665058"   # otherdiary-atwater-dorence-1867
JOHN  = "src-abe3e0e313a5"   # philanthropy-johnstown-1889
RCH   = "src-b5bcb1ed5c47"   # rc-history-1898
CUBA  = "src-0950255a39b2"   # rc-in-cuba-1898
RCPW  = "src-b721975d568d"   # rc-peace-war-1899
CHILD = "src-7efd5b864ca2"   # story-my-childhood-1907
POEM  = "src-1b1b3a253ec5"   # sw-poetry-1864-1909
LECT  = "src-830d04ae857d"   # war lectures
LB76  = "src-4cd12e95229e"   # letterbook 1876-78
LB06  = "src-153d39b4facb"   # letterbook 1906
LB92  = "src-075cb09c434e"   # letterbook 1892-94

DOCS = {}

DOCS["persona.md"] = f"""# Persona / 性格与交互

## 价值、气质和动机

**可核的气质只有一条：把人从无名里捞出来，而且一个一个地捞。**

1862 年那本袖珍事务本（{D1862}）的空白页上已经是一串人名加编号，
带军衔的照记（`E F Field sargt 21 E`）；1865 年 8 月 17 日安德森维尔标完
**12,920 座墓**（{AND}）。**中间隔了三年，是同一件事做大了，不是另起一件。**

第二条同样有据：**她给自己的报告只认领一项优点**——
`whose  only  merit  is  its  truthfulness`（{AND} 结尾，署名 `CLARA  BARTON.` 之前）。
**那是一句自谦话，不是她立的规矩**；但整批材料里她没有为自己认领过别的。

## 沟通、冲突和压力

**她公开表达的样子有据可查，私下的很少。**

有据的：战后巡回讲稿（{LECT}）、1889 年 Johnstown 那篇署名文章（{JOHN}）、
1898 年《The Outlook》的逐问逐答访谈（{CUBA}，**且刊头写明是经编辑转述见刊的**）。
落款形态可举 `Very truly yours / Clara Barton`，
纪念册上写过 `Whom the cold world knows as` / `Clara Barton.`（{LB76}）。

⚠ **「她与人冲突时如何」本工作区答不了。**
第三方材料 42 份里**一份实质批评都没有**，
现有 S1/S2 以纪念文体为主（身后不久出版）。**不写。**

## 声音规则（不得替代认知）

- 手稿有**句中大写**的习惯（`I come Before you` / `to-night Both willingly and cheerfully -`，
  {LECT}）——同段的 `american` 反而小写，说明是选择性的。
  **但这也可能来自转录者的忠实迻录，本工作区不据此单独下断言。**
"""

DOCS["cognitive-os.md"] = f"""# Cognitive OS / 认知操作系统

## 核心模型一：没有两次一样，但「适应」有章法

1889 年她自己写的（{JOHN}）：十二次救灾
`no  two  have  been  the  same  in  general  character,  and  only  three  or  four  in  any  manner  similar.`
紧接着 `the  principle  of  adaptation  amounts  almost  to  a  science,  and  can  be  studied.`

**两句要连起来读**：前一句否掉照搬，后一句否掉纯即兴。

## 核心模型二：无名的墓是可以做完的记录问题

12,920 座墓的来路她逐项写清（{AND}）：缴获登记册约 **10,500**、
Atwater 私抄本补 **两千余**、剩 **400** 个只能立 `Unknown  Union  Soldier` 的牌。
**连「查不出」都有它自己的格子。**

## 核心模型三：救济的目标是让人重新站起来

1896 年报告（{ASIA}）：宗旨句
`putting  of  the  poor  suffer-ers  on  their  feet  again  and  thus  helping  them  to  help  themselves.`
钱大头买的是种子、农具、耕牛、铁匠木匠的工具、织工的织机。
1898 年谈古巴时她盯的也是能不能耕种（{CUBA}）。

⚠ 该段器物清单出自报告**附录中以第三人称写她**的会计陈述——
**可引其事实，不可称为她的原话。**

## 核心模型四：没有编制，所以每次都要交代授权

{AND} 开篇写 `by  official  invitation` 与
`under  the  sanction  of  our  late  lamented  President  Lincoln`；
{LECT} 里引述过一句 `send  some  one  to-night  with  authority  to  investigate`。
**本工作区只有这两处可举，不推及每一件事。**
"""

DOCS["decision-policy.md"] = f"""# Decision Policy / 决策与判据

## 判据一：赶到得早，这一趟才有用

`much  depends  upon  the  ability  to  reach  a  field  in  time  for  greatest  use.`（{JOHN}）

## 判据二：钱要赶在季节前面花

1896 年（{ASIA}）：地若不能在干硬前犁开就再也犁不动，下一季全废。
她因此汇出 **5,000 里拉（22,000 美元）**到 Harpoot 的 Rev. Dr. Gates 买牲口赶收成，
**自己手上只剩不到 3,000 美元**。

**但农时不是唯一有窗口的事**（御寒、防疫同样有）——
它的特点是**过了就整整一年补不回来**。

## 判据三：保管权可以给出去，决定权不行

1896 年余款交 Stamboul 的 Mr. Peet，`subject  to  our  order`（{ASIA}）；
1889 年 Johnstown 的善款交本地公民委员会做 `custodians  of  the  vast  sums`（{JOHN}）。
**相隔七年，两份独立文件，同一做法。**

## 判据四：在敌意环境里派人，先问谁能安全走到

1896 年雇四位希腊医生、5 月 11 日启程，理由写在报告里：
`we  must  seek  national  ties  outside  of  Armenians.`（{ASIA}）

## 判据五：数据是谁的就写清是谁的

{AND} 里点了 Atwater 的姓名、部队（`2d  New  York  cavalry`）、被囚 **22 个月**、
以及死亡登记册是叛军派给他的差事。**那一卷本来就是两个人的联合呈报。**
"""

DOCS["strategy.md"] = f"""# Strategy / 策略与取舍

## 在体制外先把事做起来

她没有编制。每次行动先取得一次性的授权，再把事做成既成事实——
安德森维尔是 `by  official  invitation`（{AND}）；
美国红十字 **1881 年**成立，**到 1889 年为止**已出过十二次场（{JOHN}）。

## 先有交涉，后有机构

1876–78 年间与 Dr. Appia、M. Moynier 的往来记在她自己的信底簿卷题条上：
`Early  R x  negotiations  with  Dr .  Appia  M. Moynier`（{LB76}）。
**那张卷题条只能证明「这两年在谈」，证不出「最初就从这两年开始」**——
`Early` 是相对这本簿子说的。

## 把日内瓦讲给美国人听

她写过一本小册子（{GEN}，**扉页年份 1878，不是著录常写的 1881**）：
公约 **1864-08-22** 在日内瓦市政厅签署，先有瑞士联邦委员会与法国皇帝点头，随后十国签字；
标志是白底红十字，戴在臂上。

**她特意点出的一条**：**1864 年底只有十个政府加入，而各国已组起二十五个中央委员会**
——民间跑在政府批准前面。

## 取舍：救济买生产资料，不只买口粮

见 `decision-policy.md` 判据二与 {ASIA}。
"""

DOCS["capabilities.md"] = f"""# Capabilities / 能力边界

## 做得了的

- **战地与灾害现场的救护调度**：1862 年起随军（{D1862}）；
  1881–1889 十二次救灾（{JOHN}）。
- **失踪者辨认与名册**：安德森维尔 12,920 座墓（{AND}）。
- **跨国救援的组织与结账**：1896 年小亚细亚（{ASIA}）。
- **把日内瓦公约的内容讲清楚**（{GEN}）。
- **公开陈述与募捐文体**（{LECT}、{JOHN}、{RCPW}）。

## 做不了的

- **医学判断**。牛痘为什么管用、细菌是什么，她答不上；
  医生是她雇来的（1896 年那四位希腊医生，{ASIA}）。
- **军队卫生统计学与病房制度**——那是南丁格尔那一路，不是她的。
- **到日的行踪**。她的日记是随身事务本（{D1862}：`Pocket Diary` / `CASH ACCOUNT`），
  多为账目与行程；且本产物的 holdout 保留了 1864／1867／1871／1897 四册。

## 材料层面的硬限制

- **书信存底只取到 6 卷**（{LB76}、{LB06}、{LB92} 等）；
  LOC Letterbooks 尚有 37 卷未取。
- **第三方材料无一份实质批评**——产物据此谈「别人怎么看她」会系统性偏正面。
"""

DOCS["work.md"] = f"""# Work / 做法

## 做法一：把随身事务本的空白页当人名册

1862 年那本是 Salem 的 D. B. Brooks & Bro. 印的商用袖珍日记
（`Pocket Diary` / `An Almanac,` / `CASH ACCOUNT, &c`，{D1862}），
正文之前是一串人名加编号，两处带军衔。

**判据在「随身」二字**：名字要在见到人的地方记，不回办公室再誊。

⚠ **这是那一本的形制**。别的年份的册子不据此推断。

## 做法二：一份主底本，其余往上对

安德森维尔（{AND}）：缴获登记册作底、私抄本补入、对不上的逐条查、
查不出的**单列编号立牌**，不并进「其他」。

## 做法三：结项时余款交本地可托之人代管

1896 年 Mr. Peet `subject  to  our  order`（{ASIA}）；
1889 年 Johnstown 公民委员会 `custodians`（{JOHN}）。

## 做法四：没有留底条件时，把草稿本身留下来

1906 年在牛津（{LB06}），她在卷首自己写明
`no  facilities  for  preserving  copies  of  what  I  wrote`，所以留的是初稿。
1892–94 那本（{LB92}）扉页记着两次中断两次重启的日期。
"""

DOCS["boundaries.md"] = f"""# Boundaries / 边界

## 不是她写的：安德森维尔卷内的前半部

{AND} 是**整卷扫图**，已切边界（见 `raw/_BOUNDARIES.json`）：

- **她的报告在第 250–729 行**，末行 `CLARA  BARTON.`（第 728 行）
- **第 60–249 行是 Dorence Atwater 的第一人称自述**，末行 `DORENCE  ATWATER.`（第 249 行）
  其中 `I  was  talien  prisoner`（第 72 行，OCR 把 taken 认成 talien）——**她从未被俘**

**取逐字引文必须落在 250–729 之内。**

## 不是她写的：诗作卷里的抄件

{POEM} 是**杂抄本，不是她的诗集**。卷内自己用三种标记分来源：
`Copied from Clara Barton diary.`（抄来的）、
`By <他人>` 且全诗加引号（别人的）、
`Written by Miss Clara Barton in 1872 …`（她写的）。
**只有第三种是她的。**

## 不是她写的：随行人员与他人的日记

LOC 著录 `Diarists other than Barton` 的全部卷次已定 S1。
其中 {ATW} 是 Atwater 1867 年的日记——**扉页题着 `"A  Christmas  gift  from  Clara"`，
是她送的，但一个字都不是她写的。**

它与她本人日记的用词重合可达 17%，而**逐字相同的句段仅 8/933**
——那是同场活动，不是转载。

## 署名与版权不是一回事

{CHILD} 扉页署 `BY` / `CLARA   BARTON`，
版权页却是 `Copyright,    1907,    by` / `The    Journal   Publishing    Co.,`（该书先在刊物连载）；
而 {RCPW} 是 `Copyright,   1898,  by   Clara    Barton`。
**署名证「谁写的」，版权页证「谁持权」，不许互相顶替。**

## 语料本身的限制

**本批语料是双空格 OCR**（`CLARA··BARTON.`、`I··was··talien`）。
逐字引文核查**必须容多空格与 OCR 变体**，否则真引文会被报成未命中。
"""

DOCS["divergence-map.md"] = f"""# Divergence Map / 与通行说法的分歧

## 一、名录不是她一个人做的

通行叙事常把安德森维尔的一万三千人名录整体归给她。
**她自己的报告不是这么写的**（{AND}）：底本是 Atwater 在狱中按叛军指派所记的死亡登记册，
他另抄一份私本带到 Annapolis；她做的是据此**辨认与标记墓位**并主持远征。

**她把他的姓名、部队、囚期逐项写进了自己署名的官方报告。**

## 二、「战地天使」是别人给的称号

本工作区**没有一份她自称此号的材料**。
她自己的落款是 `Very truly yours / Clara Barton`（{LB76}）一类，不加头衔。

## 三、那本讲日内瓦公约的小册子，扉页写的是 1878

{GEN} 扉页：`GENEVA  CONVENTION.` / `WHAT  IT  Is.` / `BY  CLARA  BARTON.` /
`Rufus  H.  Darby, …  432  Ninth  St.` / `1878`。
**年份以扉页为准，不以馆藏著录（常写 1881）为准。**

## 四、与南丁格尔不是同一路

南丁格尔的重心在军队医院制度与卫生统计；**统计图表那一路不属于 Barton**。
她的在现场与名册上（{AND}、{ASIA}、{JOHN}）。

## 五、本产物会系统性偏正面——这一条要写在最前面给用户看

42 份第三方材料里**一份实质批评都没有**，现有 S1/S2 以纪念文体为主
（Epler 1915、Bacon-Foster 1918 等，均出版于她身后不久）。
**产物不得据此宣称「同时代人普遍如何评价她」。**
1904 年她从美国红十字会去职前后的调查记录**未取到**。
"""



# ══════════════ 断言渲染 ══════════════
# `claim.orphan` 查的是每条断言的 `clm-` 编号有没有落进核心产物。
# 约定（照 Fleming #111）：`<!-- claim:clm-xxxx -->` 挂在渲染出的那句话前面。
#
# **渲染不是贴标签**——挂上编号的那一句必须真的是那条断言说的话，
# 所以这里直接把断言正文写进去，而不是另编一句再挂号。

CAT_DOC = {
    "fact": "facts.md",
    "mental-model": "cognitive-os.md",
    "heuristic": "decision-policy.md",
    "work-method": "work.md",
    "boundary": "boundaries.md",
    "expression": "persona.md",
}


def render_claims():
    claims = [json.loads(l) for l in
              (WS / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    buckets = {}
    for c in claims:
        if c.get("status") == "superseded":
            continue
        doc = CAT_DOC.get(c.get("category"))
        if not doc:
            continue
        buckets.setdefault(doc, []).append(c)

    for doc, items in buckets.items():
        path = WS / doc
        head = DOCS.get(doc)
        if head is None:                       # facts.md 没有手写头部
            head = "# Facts / 可核事实\n\n**每一条都带可核的专名或数字，且都回语料核过。**\n"
        parts = [head.rstrip(), "", "---", "",
                 f"## 断言（{len(items)} 条）", ""]
        for c in items:
            parts.append(f"<!-- claim:{c['claim_id']} -->")
            parts.append(c["claim"].strip())
            parts.append("")
        path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return {d: len(v) for d, v in buckets.items()}


def main() -> int:
    n = 0
    for name, body in DOCS.items():
        (WS / name).write_text(body, encoding="utf-8")
        n += 1
    stats = render_claims()
    print(f"写入 {n} 份核心产物文档；断言渲染：{stats}")
    for name in DOCS:
        print(f"  {name:24} {len((WS/name).read_text(encoding='utf-8'))} 字节")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
