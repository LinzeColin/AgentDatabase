#!/usr/bin/env python3
"""在 tail_lock 内为 Alberti #146 追加 curate_ia 规则（锁内 diff 增量，不整文件覆盖）。"""

p = "curate_ia.py"
s = open(p, encoding="utf-8").read()

EXCL_RULE = '''    # ★ Leon Battista Alberti #146（1404-1472，文艺复兴人文学家/建筑师）：同名者多为
    #   意大利其他 Alberti 家族成员（Leandro 1490s 多明我会作家、Durante 1538-1613 诗人、
    #   Francesco、Giovanni 等），均无 "leon battista" 词元组合 → 由 REQUIRE 天然挡掉，
    #   EXCLUDE 留空即可；跨作者混编卷（Biblioteca rara 1862 丛、Hypnerotomachia、
    #   Pandolfini 旧题名的 Della famiglia 1802/1811、Leonardo 的 Trattato della pittura）
    #   按题名排（见 EXCLUDE_TITLE）。
    "leon-battista-alberti": [],
'''

TITLE_RULE = '''    # ★ Alberti #146：混编卷/他人著作而 creator 里含 Alberti 的，按题名排：
    #   Biblioteca rara（Daelli 编 1862 多作者丛，非 Alberti 独立著作）、
    #   Hypnerotomachia Poliphili（Colonna 著，署名争议）、
    #   Della famiglia 的 Pandolfini 旧题名印本（1802/1811，题名署 Agnolo Pandolfini）、
    #   Leonardo 的 Trattato della pittura 及其西译（Leonardo 主著，Alberti 仅附 De pictura 译本）。
    "leon-battista-alberti": ["biblioteca rara", "hypnerotomachia",
                               "governo della famiglia d'agnolo pandolfini",
                               "trattato della pittura", "el tratado de la pintura"],
'''

REQ_RULE = '''    # ★ Leon Battista Alberti #146：目标署名形态 `Alberti, Leon Battista, 1404-1472`／
    #   `Leon Battista Alberti`／`Alberti, Leone Battista`（1755 英译 Leoni 题名页）。
    #   REQUIRE 钉 alberti + "leon battista"（词元匹配，不认名序）；
    #   Leone 变体单独列词元。其他 Alberti 家族成员无此组合 → 天然挡掉。
    "leon-battista-alberti": [["alberti", "leon battista"], ["alberti", "leone battista"]],
'''

# 1) EXCLUDE：锚定 kandinsky 最后一行，在其后追加（该行是 EXCLUDE 字典最后一项）
anchor_excl = '    "kandinsky": ["Victor Kandinsky", "Carla Kandinsky", "Nina Kandinsky", "Kandinsky, Nina"],'
assert s.count(anchor_excl) == 1, "EXCLUDE anchor 不唯一"
s = s.replace(anchor_excl, anchor_excl + "\n" + EXCL_RULE, 1)

# 2) EXCLUDE_TITLE：锚定其末尾 franklin 行 + 字典收尾 }
old_title = '    "franklin": [],\n}\n# 目标必须出现在 creator 里的**姓名词元**'
assert s.count(old_title) == 1, "EXCLUDE_TITLE 锚点不唯一"
s = s.replace(old_title, '    "franklin": [],\n' + TITLE_RULE + '}\n# 目标必须出现在 creator 里的**姓名词元**', 1)

# 3) REQUIRE：锚定 REQUIRE 的 franklin 行，在其后追加
anchor_req = '    "franklin": [["franklin", "benjamin"]],'
assert s.count(anchor_req) == 1, "REQUIRE anchor 不唯一"
s = s.replace(anchor_req, anchor_req + "\n" + REQ_RULE, 1)

open(p, "w", encoding="utf-8").write(s)
print("curate_ia.py 已追加 leon-battista-alberti 规则（EXCLUDE/EXCLUDE_TITLE/REQUIRE）")
