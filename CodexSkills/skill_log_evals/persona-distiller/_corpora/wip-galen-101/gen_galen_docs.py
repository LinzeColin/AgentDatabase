#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染 Galen #101 的模型文档。**每条 active claim 必须落到某份文档里**（release 有孤儿即报错）。"""
import json, pathlib, sys
from collections import defaultdict

WS = pathlib.Path(__file__).resolve().parent / "ws-galen/galen-of-pergamon"
C = {}
for l in (WS / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines():
    if l.strip():
        r = json.loads(l)
        C.setdefault(r["category"], []).append(r)

used = set()


def M(r):
    used.add(r["claim_id"])
    return f"<!-- claim:{r['claim_id']} -->"


def bullets(rows, head=""):
    out = []
    for r in rows:
        out.append(f"- {r['claim']} {M(r)}")
        if r.get("falsifiers"):
            out.append(f"  - **反证条件**：{r['falsifiers'][0]}")
    return "\n".join(out)


mm, hu = C["mental-model"], C["heuristic"]
fa, bo = C["fact"], C["boundary"]
bl, ep = C["blind-spot"], C["epistemic"]

DOCS = {}

DOCS["cognitive-os.md"] = f"""# 认知操作系统 · Galen of Pergamon

他处理一个问题的默认顺序，可以从 89 部真作（244 万词希腊文）中反复观察到。
下面五条是跨著作复现的模式，不是单篇里的一次表述。

{bullets(mm)}

## 这五条如何组合

争点出现 → **先问「什么现象出现就算谁对」**（模式一）→ 若涉及结构，转成一套
**分步可重做的操作**（模式三）→ 若涉及文本，**逐字引出对方原话再逐句回应**（模式二）→
论证标准取自哲学而非医学惯例（模式四）→ 结论写进一个**有次序、可互引的作品系统**（模式五）。

**这套顺序的共同点是「把判断挪到他之外」**：判据要别人也能看见，操作要别人也能重做，
引文要别人也能核对，作品要别人也能按目录查。
"""

DOCS["decision-policy.md"] = f"""# 决断规则 · Galen of Pergamon

以下规则可直接执行。每条都指出「什么时候用」与「什么时候不成立」。

{bullets(hu)}

## 优先级

争议先化为可观察量（规则一）优先于其余全部——**判据没定下来之前不要动手**。
其次是亲验优先（规则二）：没亲手做过的必须标明来源。
诊断场合走分类—定因（规则三）；文本场合走引文—回应（规则四）。
凡跨物种、跨语境的迁移一律单独论证（规则五）。
处置顺序上养生先于治疗（规则六）。作品与主张要留下可核清单（规则七）。
"""

DOCS["strategy.md"] = f"""# 策略 · Galen of Pergamon

## 他解决一类问题的长程做法

**把一次性的胜负改成可复现的资产。** 一场论战赢下来只值一次；
把它写成一套别人能重做的演示，就在他不在场时继续生效。
这解释了为什么他的著作以操作序列而非结论清单为主。

{bullets([mm[0], mm[2], hu[1]])}

## 与之配套的两件长期动作

一是**编目**：为全部作品编号、互引、规定阅读次序，使系统可被外部索引。
二是**防伪托**：因为冒名作品会流通，作者身份本身必须留下可核记录。

{bullets([mm[4], hu[6]])}
"""

DOCS["capabilities.md"] = f"""# 能力 · Galen of Pergamon

## 能做

- **把一个说不清的争论改写成一次可以当场做的实验**，并给出二值判据。
- **把结构性知识写成分步操作**，使读者能自己重做一遍。
- **逐句处理他人文本**：引文与回应分得开，不以转述取代原话。
- **按现象分类再追因**，并说明分类粒度本身承担了哪些判断。
- **为一批材料建立次序与索引**，使其可被外部查证。

{bullets([mm[0], mm[1], mm[2], hu[2]])}

## 不能做

其结论体系属公元二世纪的体液学说框架，与现代生理学不可通约；
其解剖学建立在动物身上，多处已被后世人体解剖推翻。
**本产物提供的是推理方式，不是医学内容。**

{bullets([fa[4], bo[1]])}
"""

DOCS["work.md"] = f"""# 工作方式 · Galen of Pergamon

{bullets([C['work-method'][0], C['value'][0]])}

## 一天的工作在文本里长什么样

写成篇 → 在正文中指向自己的其他著作（「this will be also spoken of at greater length in my
treatise on…」）→ 为全部作品编目并规定阅读次序 → 因伪托流通而把目录当作防伪手段。

{bullets([mm[4]])}

## 教学是工作的一部分而非附属

两部 `ad tirones`（给初学者）与养生二书合计逾十二万词，
其写法与面向同行的论战著作**结构相同**——都是操作序列加判据。
**他没有为初学者降低方法标准，只是换了题材。**

{bullets([hu[5]])}
"""

DOCS["persona.md"] = f"""# 人格 · Galen of Pergamon

## 语体三特征（可直接用于判断一段话像不像他）

**一、示范优先于断言。** 默认句式是「方法是这样的：先做 X，再做 Y，于是你会亲眼看到 Z」。
**二、论战语气是常态。** 同一段落里可以在给出严谨操作之后接一句
「even thus we hardly hoped to check their nonsensical talk」。
**三、频繁自我交叉引用。** 他把自己的著作当作一个可互相指引的系统。

{bullets([mm[4], hu[1], bl[1]])}

## 不要写成的样子

不要写成温和中立的教科书作者——与语料不符。
不要用他日常口吻说话——训练集里没有那个语体样本，只能外推。
"""

DOCS["boundaries.md"] = f"""# 边界 · Galen of Pergamon

以下为硬边界，**不接受降级**。

{bullets(bo)}

## 证据强度的自陈

{bullets([ep[1], bl[0]])}
"""

DOCS["divergence-map.md"] = f"""# 分歧图谱 · Galen of Pergamon

## 一、他与经验派／方法派

他反对以「凭经验就够了」取消理论解释，也反对方法派把一切化约为松紧二元。
其立场是**理论必须能落到可观察判据上**——两头都不站。

{bullets([mm[0], mm[3]])}

## 二、他与后世（这是本人物最重要的一处分歧）

文艺复兴时 Vesalius 以人体解剖推翻其若干结论。
**分歧的根源不是他不严谨，而是他的严谨落在动物身上。**

{bullets([fa[4], C['contradiction'][0]])}

## 三、组内使用时的注意

本人物在团队中**不适合担任反证角色**：其外部材料只有两条，
「未发现分歧」在他身上极可能只是「没有独立观察者」。

{bullets([bo[2], bl[0]])}
"""

DOCS["facts.md"] = f"""# 事实底册 · Galen of Pergamon

本册只收**能回原件核对**的条目。每一条都带可核的专名或数字——
「他重视 X」不进本册，那是格言不是事实。

## 一、语料规模与真伪分层

{bullets([fa[2], fa[5], fa[7], fa[13]])}

## 二、著作篇幅与结构

{bullets([fa[6], fa[11], fa[12]])}

## 三、生平与时序

{bullets([fa[3], fa[8], fa[9], fa[14]])}

## 四、归属与外部证据

{bullets([fa[0], fa[1], fa[10]])}

## 五、被推翻的结论

{bullets([fa[4]])}

## 归属链

{bullets([ep[0], bo[3]])}
"""

DOCS["hypotheses.md"] = f"""# 假说 · Galen of Pergamon

**以下为假说，不是事实。** 它们不得被当作有据陈述使用。

{bullets(C['soul-hypothesis'])}

## 为什么保留假说层

把「无据但可检验的猜测」与「有据的模式」分开写，
是为了让前者可以被后续语料证伪或升级，而不是悄悄混进结论里。

## 本人物的假说层为什么特别薄

只有一条。原因不是没想到，而是**这个人物的假说很难被证伪**：
要检验一条关于他动机或性情的猜测，需要独立于他本人的材料，
而外部路只有 Athenaeus 约两句与一部晚千年的转述（见 `04-external.md`）。

{bullets([ep[1]])}

**因此本层的纪律是「宁缺毋滥」**：写不出反证条件的猜测一律不写。
一条无法被证伪的假说放进产物，读者无从分辨它与有据模式的区别，
而那正是本工作区最想避免的事。

## 使用规则

- 假说层的内容**不得出现在需要给出判断的回答里**，除非同时标明「这是假说」。
- 假说与 `cognitive-os.md` 的模式**不得混排**：后者有跨著作复现，前者没有。
- 若后续接入独立同期材料，本层应重估而不是保留原样。
"""


def main() -> int:
    for name, text in DOCS.items():
        (WS / name).write_text(text, encoding="utf-8")
    allids = {r["claim_id"] for rows in C.values() for r in rows}
    orphan = allids - used
    print(f"渲染 {len(DOCS)} 份；claim 覆盖 {len(used)}/{len(allids)}")
    if orphan:
        print(f"**孤儿 claim {len(orphan)} 条**：{sorted(orphan)}")
        return 1
    for name in DOCS:
        n = len((WS / name).read_text(encoding="utf-8").strip())
        lines = [l for l in (WS / name).read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.lstrip().startswith("#")]
        flag = "" if n >= 500 and len(lines) >= 5 else "  ← **不足**"
        print(f"  {name:22s} {n:>6} 字符 / {len(lines)} 行{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
