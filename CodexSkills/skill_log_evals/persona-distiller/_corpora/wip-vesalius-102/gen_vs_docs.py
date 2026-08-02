#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染 Vesalius #102 文档。每条 active claim 必须有锚点。"""
import json, pathlib, sys
WS = pathlib.Path(__file__).resolve().parent / "ws-vesalius/andreas-vesalius"
C={}
for l in (WS/"evidence/claims.jsonl").read_text(encoding="utf-8").splitlines():
    if l.strip():
        r=json.loads(l); C.setdefault(r["category"],[]).append(r)
used=set()
def M(r): used.add(r["claim_id"]); return f"<!-- claim:{r['claim_id']} -->"
def B(rows):
    o=[]
    for r in rows:
        o.append(f"- {r['claim']} {M(r)}")
        if r.get("falsifiers"): o.append(f"  - **反证条件**：{r['falsifiers'][0]}")
    return "\n".join(o)
fa,mm,hu=C["fact"],C["mental-model"],C["heuristic"]
bo,bl=C["boundary"],C["blind-spot"]
D={}
D["cognitive-os.md"]=f"""# 认知操作系统 · Andreas Vesalius

他处理权威文本与自己观察之间冲突的方式，可以从四十六条源里反复观察到。

{B(mm)}

## 四条如何组合

遇到与旧文本冲突 → **一句一句核，不整块信也不整块弃**（模式一）→
把结论钉到别人能在别的材料上复看的对象与部位（模式二）→
图与文互为证据，不是插图（模式三）→ 该记名的记名（模式四）。

**共同点是「把判断挪到他之外」**：部位别人能看，卷次别人能查，经手人别人能问。
"""
D["decision-policy.md"]=f"""# 决断规则 · Andreas Vesalius

{B(hu)}

## 优先级

先摆原话再指卷次（规则一）优先；表述否定结论时分清「我至今没见过」与「不存在」（规则二）；
**证据不合意时也要看**（规则三，按反面用——他自己在蝶骨之争里被记下拒看过一具标本）；
批评他人方法时同段承认自己也在用退而求其次的材料（规则四）；
日期与人名当场记死（规则五）；先把对方最强处说足再说分歧（规则六）。
"""
D["strategy.md"]=f"""# 策略 · Andreas Vesalius

## 长程做法：把一次论断变成别人能复查的东西

他不是靠宣布结论取胜的。**他把每一处分歧钉到具体的骨、具体的卷、具体的经手人**，
使得三百年后仍可校。代价也真实：Falloppio 说他「如军队被胜利之热与冲力驱使」。

{B([mm[0],mm[1],fa[12],fa[10]])}

## 与之配套的两件长期动作

**一是控制载体**：自费赎回木版、宁可白送印工也不让改小开本。
**二是记录链条**：商行、代理人、印工、御医，逐一写进正文。

{B([fa[2],fa[3],mm[3]])}
"""
D["capabilities.md"]=f"""# 能力 · Andreas Vesalius

## 能做

- **把一条沿袭千年的结论拆到具体部位再逐条核**（下颌、颞肌、咬肌、腘窝肌、眼的葡萄膜）。
- **指出前人错在哪一部哪一卷**，并说明为什么那一卷会错（毁于火、后书自改而不提前书）。
- **组织文字—图版—印制三方协作**，并把每个经手人记进正文。
- **在被公开辱骂时不接受以「年少无知」换和解**。

{B([fa[12],fa[14],fa[3],fa[8]])}

## 不能做

其生理学仍在体液学说框架内；**他并没有推翻心室间隔**。

{B([fa[15],bo[0],bo[1]])}
"""
D["work.md"]=f"""# 工作方式 · Andreas Vesalius

{B([C['work-method'][0],C['value'][0]])}

## 取材与耗时，有数

{B([fa[16],fa[17]])}

## 一条他自己写下的顺序

亲手切 → 与旧文本逐条比 → 记下分歧积成大卷 → 换物种再验（有尾与无尾的猿）→ 才下结论。

{B([fa[18]])}
"""
D["persona.md"]=f"""# 人格 · Andreas Vesalius

## 语体三特征

**一、把过程连同代价一起写出来。** 不是「我完成了图版」，而是「我为了让画师肯画尸体费了多少事」。
**二、对事极具体，对人名极克制地——只有一处例外。** 他写出 Oporinus、Stopius、Danoni 商行、
Florenas、Vertunus、Albius、Baersdorpius，**唯独不写自己画师的名字**。
**三、被攻击时不软化立场，也不升级辱骂。**

{B([mm[3],fa[0],fa[1]])}

## 不要写成的样子

不要写成「推翻了盖伦的人」——他逐条纠正且保留了许多结论。
不要用他的日常口吻说话——训练集里没有那个语体样本。

{B([bo[1],bl[0]])}
"""
D["boundaries.md"]=f"""# 边界 · Andreas Vesalius

{B(bo)}

## 证据强度的自陈

{B(bl)}
"""
D["divergence-map.md"]=f"""# 分歧图谱 · Andreas Vesalius

## 一、他与盖伦派（Sylvius、Puteus）

Sylvius 骂他「Vaesanus quidam…transfuga」并要他把责任推给自己的年少或推给意大利人；
他没有接受。

{B([fa[7],fa[8],fa[9]])}

## 二、他与 Falloppio——**同代最强同行，既赞且责**

{B([fa[10],fa[11]])}

## 三、他与后世（须防压平）

{B([fa[15]])}

## 四、组内使用

**本人物适合担任反证角色**：同期第三人称十四条，骂他的、辩护的、剽窃他的都留下了署名著作。
这与同族的 Galen 恰好相反（后者外部路仅两条、其一约两句，「未发现分歧」在他身上极可能只是「没有独立观察者」）。

{B([bl[1]])}
"""
D["facts.md"]=f"""# 事实底册 · Andreas Vesalius

本册只收**能回原件核对**的条目，每条带可核的专名、数字或逐字引文。
**账本事实（语料有多少部、多少词）一条不收**——那是账本不是知识。

## 一、图版、画师与出版链

{B(fa[0:7])}

## 二、论战：具名对手与他们的原话

{B(fa[7:12])}

## 三、他纠正了什么、没纠正什么

{B(fa[12:16])}

## 四、取材、职位与生平

{B(fa[16:20])}

## 五、身后与传播

{B(fa[20:])}
"""
D["hypotheses.md"]=f"""# 假说 · Andreas Vesalius

**以下为假说，不是事实。**

{B(C['soul-hypothesis'])}

## 并陈项与存疑项

{B([C['contradiction'][0],C['epistemic'][0]])}

## 为什么保留假说层

把「无据但可检验的猜测」与「有据的模式」分开写，
是为了让前者能被后续语料证伪或升级，而不是悄悄混进结论。
本人物的假说层只有一条，且带三条互斥的替代解释——**写不出替代解释的猜测不写**。
"""
def main():
    for n,t in D.items(): (WS/n).write_text(t,encoding="utf-8")
    allids={r["claim_id"] for v in C.values() for r in v}
    orph=allids-used
    print(f"渲染 {len(D)} 份；claim 覆盖 {len(used)}/{len(allids)}")
    if orph:
        print("孤儿:",sorted(orph)); return 1
    for n in D:
        t=(WS/n).read_text(encoding="utf-8"); ln=[l for l in t.splitlines() if l.strip() and not l.lstrip().startswith("#")]
        print(f"  {n:22s} {len(t.strip()):>6} 字符 / {len(ln)} 行" + ("" if len(t.strip())>=500 and len(ln)>=5 else "  ← 不足"))
    return 0
if __name__=="__main__": sys.exit(main())
