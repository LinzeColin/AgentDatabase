# -*- coding: utf-8 -*-
"""生成 Palladio claims.jsonl —— 7 类 13 条（4 fact + 2 mental-model + 3 heuristic + 1 value + 1 boundary + 1 blind-spot + 1 语料元断言）"""
import json

S = "src-104fc055b0da"   # 四书 1570 意原版
E4 = "src-56047aa2b2bd"  # 四书 1742 英译
E4T4 = "src-fd05b338bba2" # 四书第四书 1742
A1555 = "src-eecef2cf93b7" # 罗马古迹 1555
A1554 = "src-a8064aa6be0c" # 罗马古迹 1554
CES = "src-d729c800ee5c"  # 恺撒评注 1598
CES2 = "src-db6919652a18" # 恺撒评注 1618
TERME = "src-ea04367ec274" # 浴场 1785
FABB = "src-cec1934c8ebb"  # Le Fabbriche 1843
CINQ = "src-0717a438e7a2"  # 五柱式 1801
TRAI = "src-117866e8800c"  # 法五柱式 1679
FLET = "src-65b5a3cada5e"  # Fletcher 1902
LOUISA = "src-fc16329323b9" # 1711 Louisa 版

def clm(cid, cat, status, claim, srcs, ctxs, clusters, fals, ts, conf=0.9, alt=None, app="文艺复兴建筑"):
    return {
        "claim_id": cid, "category": cat, "status": status, "claim": claim,
        "source_ids": srcs, "contexts": ctxs, "evidence_clusters": clusters,
        "falsifiers": fals, "time_scope": ts, "confidence": conf,
        "counter_source_ids": [], "alternative_explanations": alt or [],
        "applicability": app, "author_role": "distiller", "supersedes": None,
    }

claims = [
 clm("clm-000000000001","fact","fact",
  "《建筑四书》（I Quattro Libri dell'Architettura）于 1570 年在威尼斯出版，全书四书依次论五柱式、私宅、街道桥梁广场与神庙，是 Palladio 最重要的理论著作。",
  [S,E4], ["著作出版","著作结构"], [S,E4],
  ["若四书出版年或四书分卷主题与史载不符，此断言不成立"], "1570", 0.95),
 clm("clm-000000000002","fact","fact",
  "《罗马古迹》（L'Antichità di Roma）于 1554/1555 年在威尼斯出版，是 Palladio 辑录罗马古建筑遗迹、为旅行者与读者编的短篇导览。",
  [A1555,A1554], ["著作出版","古迹导览"], [A1555,A1554],
  ["若罗马古迹出版年或体裁与史载不符，此断言不成立"], "1554/1555", 0.9),
 clm("clm-000000000003","fact","fact",
  "Palladio 为恺撒《高卢战记》作评注并绘制营地、围城与战阵图（I Commentari di Cesare），1575 首版、1598/1618 版流传，是其晚年转向古军事史地研究的著作。",
  [CES,CES2], ["著作出版","战史评注"], [CES,CES2],
  ["若恺撒评注的评注者并非 Palladio，此断言不成立"], "1575-1618", 0.9),
 clm("clm-000000000004","fact","fact",
  "Palladio 的浴场图与建筑图样由 Ottavio Bertotti Scamozzi 于其身后编辑出版（《Le Terme dei Romani》1785、《Le Fabbriche e i Disegni di Andrea Palladio》1780s-1846 多卷），图样为 Palladio 生前设计。",
  [TERME,FABB], ["身后出版","图集整理"], [TERME,FABB],
  ["若图集图样并非出自 Palladio 设计，此断言不成立"], "1785-1846", 0.9),
 clm("clm-000000000005","mental-model","pattern",
  "古优于今、以古罗马为范本：Palladio 主张古罗马建筑远超后世，因而以维特鲁威为唯一向导，从古物立说——'I proposed to my self Vitruvius both as my Master and Guide'（1742 英译序）。",
  [S,E4], ["序言自述","设计法则依据"], [S,E4],
  ["若语料中出现 Palladio 否定古罗马或质疑维特鲁威的表述，此模型不成立"], "1570/1742", 0.9),
 clm("clm-000000000006","mental-model","pattern",
  "以古物实测立规范：柱式比例与设计规则从古建筑遗迹的实测归纳而来，而非凭空想象——其罗马古迹导览与四书的设计规则皆以古物为据。",
  [A1555,E4], ["古迹测绘","设计规则"], [A1555,E4],
  ["若语料显示其设计规则纯由想象或凭空设定、与古物无关，此模型不成立"], "1554-1742", 0.85),
 clm("clm-000000000007","heuristic","pattern",
  "按柱式性格定案：设计判断以柱式自身的'性格/厚重感'为依据——如 Doric 因'requires more solidity'（更需厚重）而取相应比例，其余柱式各按需裁量。",
  [E4,E4T4], ["柱式选择","比例裁定"], [E4,E4T4],
  ["若语料显示其柱式选择与柱式性格无关、纯随机或纯委托方指定，此启发不成立"], "1570-1742", 0.8),
 clm("clm-000000000008","heuristic","pattern",
  "依场地与用途取舍：平面与立面据场地条件与建筑用途决定——别墅/住宅、公共建筑各有其宜，四书按用途分书论述。",
  [S,LOUISA], ["场地条件","建筑用途"], [S,LOUISA],
  ["若语料显示其设计完全不考虑场地与用途、千篇一律，此启发不成立"], "1570-1711", 0.8),
 clm("clm-000000000009","heuristic","pattern",
  "规范可教、浓缩成法则：把柱式规范抽成可教学、可传播的易学方法——五柱式教学版（'illustrati e ridotti a metodo facile'）与法语编译本皆为此做法。",
  [CINQ,TRAI], ["教学传播","规范浓缩"], [CINQ,TRAI],
  ["若语料显示其只出宏篇巨著、从不做教学浓缩本，此启发不成立"], "1679-1801", 0.8),
 clm("clm-00000000000a","value","pattern",
  "以古罗马建筑的'正确性/规范'为价值基准：公共建筑（神庙、桥梁、广场）与私宅并重，著作由五柱式理论到公共建筑逐层展开。",
  [S,E4T4], ["公共建筑","私宅设计"], [S,E4T4],
  ["若语料显示其价值基准不是古罗马规范而是其他（如纯商业、纯装饰），此价值不成立"], "1570-1742", 0.8),
 clm("clm-00000000000b","boundary","pattern",
  "只论建筑与古物设计法则，不越入无据领域：现代结构计算、工程材料等在其时代认知之外；无据可依时不给结论。",
  [S,E4], ["领域边界","时代认知"], [S,E4],
  ["若语料显示其妄论其时代之后才出现的工程知识，此边界不成立"], "1540s-1790s", 0.8),
 clm("clm-00000000000c","blind-spot","pattern",
  "其著作面向庇护人与读者的理想化叙述，对造价、工期与工程失败的记录少——Fletcher 也指出其早年史料'但 scant information'，私域工程文书未留存。",
  [FLET,S], ["理想化叙述","史料稀缺"], [FLET,S],
  ["若语料出现大量其造价/工期/失败的负面自述，此盲区不成立"], "1540s-1902", 0.8),
 clm("clm-00000000000d","fact","fact",
  "语料 41 份覆盖 1540s-1846 年出版文本：一手以四书（意/英/法多语种多版次）、罗马古迹、五柱式、恺撒评注、浴场与建筑图集为核心，二手为三份传记（Fletcher 1902、Gurlitt 1922、Scolari 1837）。",
  [S,FLET], ["语料构成","出版跨度"], [S,FLET],
  ["若语料份数/覆盖与台账不符，此断言不成立"], "1540s-1846", 0.95),
]

with open("andrea-palladio/evidence/claims.jsonl","w",encoding="utf-8") as f:
    for c in claims:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
print("written", len(claims), "claims")
