#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐字引文必须带**可回原刊的坐标**——否则读者无从复核，引文等于装饰。

## 为什么有这件

`check_quote_integrity` 管的是「这句话在不在语料里」。
它管不了另一半：**读者拿什么去回查。**
一句真的引文，若不写清出自哪一篇、哪一年、哪一页，
读者只能选择信或不信——而这套产物的全部主张就是「你可以不信我，去核」。

Lister #108 第 1 轮，席 E 独立地在四处 note 与 `_overall` 里点了同一件事：

> 「最承重的那段 Pasteur 原话被三个用例当作全套第一前提反复使用，却始终没有年份与卷页」
> 「宣称"能一条条指到卷页"，而三十二问无一处给过卷页」

评委看到的是症状。判据数出范围——**候选答案 11 条英文长引文，6 条同段内无任何坐标线索**。
（席 E 说「无一处」，实际 5 条是有的；**评委的印象偏严，判据给的是数。**）

## 判据形状：规则，不是阈值

**凡长逐字引文，同段内必须出现至少一项坐标线索。** 不设比例阈值——
因为我没有任何实测能支持「八成带坐标就够了」这种数字，
而 v0.0.0.36 的 `METHOD_FLOOR = 3` 已经留了一个「暂定值，无实测支持」的疤。
规则不需要标定，阈值需要。**能写成规则就别写成阈值。**

## 射程边界（本件看不见的）

- **坐标对不对，它不判。** 写个错页码照样过。它挡的是「一个坐标都没有」。
- **同段内出现即算数。** 引文在段首、坐标在段尾，也算——段落是读者的实际检索单位。
- 短引文（去掉非字母后不足 18 字符）不计——那多半是术语而非引文。
- 中文引文不计：本流水线的逐字引文都是原文，中文的是译述。

用法：

    python3 check_quote_locator.py --answers evals/judge_payload.v1.json
    python3 check_quote_locator.py --answers ... --claims evidence/claims.jsonl
    python3 check_quote_locator.py --self-test

退出码：0=每条长引文都带坐标　1=有引文缺坐标　2=自测未过　3=一条引文都没扫到（未检查，不是通过）
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

# ★ 引号形态与切分口径**复用 check_quote_integrity**，不另抄一份。
#   v0.0.0.37 那次的教训是「判据只认中英式引号，法文 «» 一条扫不到」；
#   若这里再抄一份正则，两边迟早分叉，而分叉的那一侧会静悄悄地报绿。
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_quote_integrity import Q, _q  # noqa: E402

MIN_LETTERS = 18

# 坐标线索：年份 / 页 / 卷 / 期 / 罗马数字纪年 / 篇名与刊名
LOCATOR = re.compile(
    r"\b(?:1[5-9]\d{2}|20\d{2})\b"            # 1867
    r"|\d{4}\s*年"                             # 1867 年
    # ★★★ v0.0.0.155：**中文数字纪年**。中文答案里写「一八七六年」是完全正当的坐标，
    #   而本件此前只认阿拉伯数字——Sorby #133 实测：候选 16 条引文里有 7 条
    #   同段明明写着「一八七六年那篇随笔里」，判据却报「缺坐标」。
    #   ★ 这不是产物的毛病，是判据只会读一种写法。**判据看不懂的写法，不等于人没写。**
    r"|[〇零一二三四五六七八九]{2,4}\s*年"          # 一八七六年 / 二〇〇八年
    r"|\bp{1,2}\.?\s*\d+"                      # p. 645 / pp. 645
    r"|第?\s*\d+\s*页"                          # 第 645 页
    r"|卷\s*[IVXivx0-9]"                       # 卷 II
    r"|\bvol\.?\s*[IVXivx0-9]"                 # vol. II
    r"|\bIss\.?\s*\d+"                         # Iss. 2272
    r"|\bMDCCC[LXVI]*"                         # MDCCCLVIII
    r"|《[^》]{2,60}》"                          # 《The Lancet》
    r"|\bThe\s+Lancet\b|\bLancet\b"
    r"|\bPhilosophical\s+Transactions\b|\bPhil\.\s*Trans\b"
    r"|\bBritish\s+Medical\s+Journal\b|\bBMJ\b"
    r"|\bCollected\s+Papers\b"
    r"|\bProceedings\b"
    # ★★★ v0.0.0.155：**刊名按形状认，不再靠白名单。**
    #   本件自己的注释早就写着这个坑（v0.0.0.62：Fleming 的 `Br J Exp Path` 因为
    #   「清单里没有这本刊」被报缺坐标）。当时的补法是加「卷(期):页」的形状，
    #   **而刊名本身仍是硬编码清单**——于是 Sorby #133 又撞上一次：
    #   `Quarterly Journal of the Geological Society` 明明在同段，判据仍报缺。
    #   ★ 改为认「若干 Title Case 词 + 期刊指示词」这个**形状**，
    #     指示词必须整词出现，避免把随便一串大写词当成刊名。
    r"|(?:[A-Z][a-z]+\s+){1,4}(?:Journal|Transactions|Annals|Magazine|Bulletin|Review|Gazette)\b"
    r"|\b(?:Journal|Transactions|Annals)\s+of\s+(?:the\s+)?[A-Z]"
    # ★ v0.0.0.62：**卷(期):页 是与刊名无关的坐标形式，按形状认，不按刊名认。**
    #   上面那串刊名是 Osler 一批人物留下的硬编码清单（Lancet／BMJ／Phil Trans）。
    #   Fleming #111 第 3 轮实测：`*Br J Exp Path* 10(3):226-236` 明明就在段内，
    #   判据却报「缺坐标」——**清单里没有这本刊**。
    #   每换一个人物就要往清单里加刊名，等于这道判据对新人物默认失灵，
    #   而失灵的方向是**误报**：作者会学会忽略它。
    #   `10(3):226-236` / `93:306-317` 这种形状本身就够读者回查，与刊名叫什么无关。
    r"|\b\d{1,3}\s*\(\d{1,4}\)\s*:\s*\d{1,4}"   # 10(3):226-236
    r"|\b\d{1,3}\s*:\s*\d{1,4}\s*[-–]\s*\d{1,4}"  # 93:306-317
    # ★★★ 2026-08-11：**`@偏移量` 是本流水线自己的坐标写法，此前判据不认。**
    #   Grotius #168 实测：`cognitive-os.md` 那条被报「缺坐标」，
    #   而它同段里明明写着「（同上，@83355。）」——
    #   **我第一遍还把它误判成「坐标落在另一段，要把它搬进来」，
    #   去读原文才发现坐标一直在同一段，缺的是判据的眼睛。**
    #   （`checker-blindspot-read-as-defect` 那一族：判据看不懂的写法，不等于人没写。）
    #   ★ 它比页码更硬：`check_quote_integrity` 就是拿这个偏移量回原文核字的，
    #     读者拿到工作区可以直接定位到那一字节。
    #   ★ 射程：只认 `@` 加 4 位以上数字。裸数字仍不算（见自测⑦），
    #     `@12` 这种也不算——避免把随口的编号读成坐标。
    r"|@\d{4,}",
    re.I)


_FENCE = re.compile(r"^```.*?^```", re.S | re.M)


def strip_code(text: str) -> str:
    """把围栏代码块换成等长空白。

    ★ 2026-08-11：**围栏代码不是逐字引文。** Grotius #168 实测，本件把
    `SKILL.md` / `README.md` 里的 5 段命令报成了「缺坐标的长逐字引文」——
    `bash python3 install.py`、`runtime/invocations.jsonl` 之类。
    那些是给收件人照抄的命令，**本来就不该有卷页坐标**；
    报出来只会让人学会忽略这道判据（与文件头 Fleming #111 那次同一个失效方向）。
    ★ 换成等长空白而不是删除：**段落切分与偏移量不变**，
    否则报文里的引文位置会跟着漂。
    """
    return _FENCE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


# ★ 2026-08-11：路径 / 标识符形状——不含任何空白，且带 `/`、`.`、`_` 或 `::`。
#   Grotius #168 实测：`SKILL.md` 里的 `runtime/invocations.jsonl`、
#   `memory/episodic.jsonl` 被报成「缺坐标的长逐字引文」。
#   那是**给收件人照抄的文件路径**，本来就不该有卷页坐标。
#   ★ 判据卡的是「不含空白」而不是「短」：一句真引文总有词间空格，
#     哪怕是拉丁文折行的 `ha- berent` 也有。**不靠长度猜，靠形状认。**
_PATHY = re.compile(r"^(?=\S+$).*(?:[/\\._]|::)")


def long_quotes(text: str):
    """产出 (引文, 所在段落)。段落 = 以空行分隔的块，读者的实际检索单位。"""
    text = strip_code(text)
    for m in Q.finditer(text):
        q = _q(m)
        if len(re.sub(r"[^A-Za-zÀ-ÿͰ-Ͽ]", "", q)) < MIN_LETTERS:
            continue
        if _PATHY.match(q.strip()):
            continue
        s = text.rfind("\n\n", 0, m.start())
        s = 0 if s < 0 else s
        e = text.find("\n\n", m.end())
        e = len(text) if e < 0 else e
        yield q, text[s:e]


def scan(unit_id: str, text: str, acc, extra: str = ""):
    """`text` 是**扫描面**（哪些算引文），`extra` 只是**坐标搜索面**。

    ★ 2026-08-11：两者必须分开。我第一版把 `evidence_clusters` 直接拼进 `text`，
    结果那些字段里本来就带引号的字串（`「Solution des objections contre…」`）
    也被数成了逐字引文——**总数从 44 涨到 45，而多出来的 3 条不是产物里的引文。**
    放宽坐标搜索面的同时把分母一起放宽，等于自己给自己灌水；
    `ratio-gates-can-be-passed-by-shrinking` 的镜像版本。
    """
    for q, para in long_quotes(text):
        acc["total"] += 1
        if LOCATOR.search(para) or (extra and LOCATOR.search(extra)):
            acc["ok"] += 1
        else:
            acc["bad"].append((unit_id, re.sub(r"\s+", " ", q).strip()[:76]))


def scan_claims(path: pathlib.Path, acc) -> None:
    """扫断言台账。**已被替代（superseded）的条目跳过。**

    ★ 2026-08-11：被替代的那条往往正是因为不够好才被换掉的（缺来源、缺坐标），
    继续报它等于让人去修一条已经不生效的东西。
    Grotius #168 实测：12 条命中里 2 条是 superseded 的旧条。
    ★ 同族缺口当天在 `ledger.py` 也修了一处（`--supersedes` 只记链接、
    不翻转旧条状态）——**「废掉的东西还在参与计数」不止一处。**

    ★ 单独成函数，是为了让自测能打**这一段真代码**。
    先前那版自测把这个循环在测里重抄了一遍，于是它保证的是抄件不是原件
    ——`a-checker-nothing-calls-is-not-a-checker` 那一族。
    """
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") == "superseded":
            continue
        scan(f"断言/{r['claim_id']}",
             re.sub(r"\n{2,}", "\n", str(r.get("claim", ""))),   # 扫描面：只有 claim
             acc,
             extra=claim_locators(r))                            # 搜索面：多一个字段


def claim_locators(row: dict) -> str:
    """台账一行里**只用来找坐标**的补充字段：`evidence_clusters`。

    ★ 2026-08-11：本件先前只读 `claim` 字段，于是把两条断言报成「缺坐标」，
    而坐标其实一直在 `evidence_clusters` 里躺着——
    `"DJBP 1853 拉丁 vol1，Prolegomena，@83307（前半）与 @83355（收回）"`。
    **台账一行没有段落，行本身就是读者的检索单位**；
    只读其中一个字段，等于替读者把另一个字段捂上。

    ★ 只取 `evidence_clusters`（这个字段的全部职责就是「证据在哪」），
      不取 `falsifiers` / `alternative_explanations`——
      那两个字段里出现坐标是顺带，靠它们放行会把门开大。
      本例的 falsifier 里恰好也写着 `@83355`，**正因为恰好，才不能算。**

    ★ 返回值**不参与「哪些算引文」的判定**（见 `scan` 的 `extra` 形参）。
    """
    ev = row.get("evidence_clusters") or []
    if isinstance(ev, str):
        ev = [ev]
    return "\n".join(str(x) for x in ev)


def self_test() -> int:
    """负对照 + 反向对照。任何一条不合即判本检查器失效。"""
    print("══ 负对照 ══")
    fail = 0
    # ★ 2026-08-11：**通过条数现算，不写死。**
    #   这里原本印的是「负对照通过（9/9）」——一个手写的常数。
    #   同一天我在本文件加用例时，先把用例插到了 `sys.exit(main())` 之后
    #   （死代码，而且调用了本文件根本没有的 `chk()`，真跑起来是 NameError），
    #   **而屏幕上照样印出 9/9**——我差点把它读成「新用例过了」。
    #   写死的分母不会因为分子没跑而变，于是它对「用例没被执行」完全无感。
    n = [0]

    def note(label: str, ok) -> None:
        n[0] += 1
        print(f"  {'✓' if ok else '✗'} {label}")

    QUOTE = ('「an irregular wound, which has probably been exposed to '
             'the air for hours before it comes under treatment」')

    a = {"total": 0, "ok": 0, "bad": []}
    scan("无坐标", QUOTE + "\n\n这一段里没有任何年份、页码或刊名。", a)
    caught = a["total"] == 1 and len(a["bad"]) == 1
    note("抓到同段无任何坐标线索的长引文", caught)
    fail += not caught

    print("\n══ 反向对照 ══")
    # ① 同段有坐标 → 必须放行。否则本件只是「凡引文皆报」，等于没判据。
    b = {"total": 0, "ok": 0, "bad": []}
    scan("有坐标", QUOTE + "（《The Lancet》1867 年，p. 326）", b)
    ok1 = b["total"] == 1 and not b["bad"]
    note("同段带刊名年份页码的同一条引文 → 放行", ok1)
    fail += not ok1

    # ② 坐标在**另一段** → 仍须抓出。证明窗口真的起作用，不是全文一搜了事。
    c = {"total": 0, "ok": 0, "bad": []}
    scan("坐标隔段", QUOTE + "\n\n另起一段才写：《The Lancet》1867 年，p. 326。", c)
    ok2 = len(c["bad"]) == 1
    note("坐标落在另一段 → 仍抓出（窗口有效）", ok2)
    fail += not ok2

    # ③ 短引文不计——否则术语加引号会被当成引文，把分母灌水。
    d = {"total": 0, "ok": 0, "bad": []}
    scan("短引文", '他把这叫做「antiseptic」。', d)
    ok3 = d["total"] == 0
    note(f"短引文（不足 {MIN_LETTERS} 字母）不计入", ok3)
    fail += not ok3

    # ④ 一条引文都没有时，**不得报通过**——这是「未检查」。
    e = {"total": 0, "ok": 0, "bad": []}
    scan("无引文", "整段中文，没有任何引号。", e)
    ok4 = e["total"] == 0
    note("无引文 → total=0（调用方须据此报「未检查」而非「通过」）", ok4)
    fail += not ok4

    # ⑥ **卷(期):页 按形状认，不按刊名认**（v0.0.0.62，Fleming #111 第 3 轮实测）
    f6 = {"total": 0, "ok": 0, "bad": []}
    scan("卷期页", "**题名后半截**（同上，*Br J Exp Path* 10(3):226-236）" + QUOTE, f6)
    ok6 = f6["total"] == 1 and not f6["bad"]
    note("`10(3):226-236` 认得出（刊名不在硬编码清单里也算）", ok6)
    fail += not ok6

    f6b = {"total": 0, "ok": 0, "bad": []}
    scan("卷页", "见 *Proc R Soc B* 93:306-317。" + QUOTE, f6b)
    ok6b = f6b["total"] == 1 and not f6b["bad"]
    note("`93:306-317` 也认得出", ok6b)
    fail += not ok6b

    # ⑦ 反向对照：**光有数字不算坐标**——否则这条通用式会把判据整个架空。
    f7 = {"total": 0, "ok": 0, "bad": []}
    scan("裸数字", "我做过 10 次，成功 3 次。" + QUOTE, f7)
    ok7 = len(f7["bad"]) == 1
    note("段里只有散落数字（无卷期页形状）→ 仍报缺坐标", ok7)
    fail += not ok7

    f7b = {"total": 0, "ok": 0, "bad": []}
    scan("纯引文", QUOTE, f7b)
    ok7b = len(f7b["bad"]) == 1
    note("段里只有引文本身 → 仍报缺坐标", ok7b)
    fail += not ok7b

    # ⑧ ★ 2026-08-11：**围栏代码不是逐字引文**（Grotius #168 实测 5 处误报）
    print("\n══ ★ 围栏代码与已废断言（2026-08-11 新增）══")
    CODE = ("装好之后这样跑：\n\n```bash\n"
            "python3 install.py --target ~/.codex/skills/hugo-grotius\n```\n\n照抄即可。\n")
    g8 = {"total": 0, "ok": 0, "bad": []}
    scan("围栏", CODE, g8)
    ok8 = g8["total"] == 0
    note("围栏代码块整段跳过（不再报成缺坐标的长引文）", ok8)
    fail += not ok8

    # ⑧′ **反对照**：同一份文件里，围栏之外的真引文必须照抓不误。
    #     否则「跳过代码」会退化成「跳过带反引号的一切」，把判据整个架空。
    MIX = ("```bash\npython3 install.py --target somewhere\n```\n\n"
           "他写道：`Up to the present time no one has treated it in a "
           "comprehensive manner`\n")
    g8b = {"total": 0, "ok": 0, "bad": []}
    scan("围栏外", MIX, g8b)
    ok8b = g8b["total"] == 1 and len(g8b["bad"]) == 1
    note(f"**反对照**：围栏外的真引文仍被抓到且报缺坐标（扫到 {g8b['total']} 条）", ok8b)
    fail += not ok8b

    # ⑧″ 反对照的另一头：给它补上坐标就该放行——证明抓它的理由是「缺坐标」，
    #     而不是「它挨着一个代码块」。
    g8c = {"total": 0, "ok": 0, "bad": []}
    scan("围栏外补坐标", MIX.replace("manner`\n", "manner`（1925 年英译本 @120282）\n"), g8c)
    ok8c = g8c["total"] == 1 and not g8c["bad"]
    note("**反对照**：同一条补上坐标后放行（抓它的理由确是缺坐标）", ok8c)
    fail += not ok8c

    # ⑧‴ **段落偏移不许漂**：strip_code 换的是等长空白，不是删除。
    #     若改成删除，引文所在段的切分会跟着移位，报文里的上下文就指错地方。
    ok8d = len(strip_code(CODE)) == len(CODE)
    note("strip_code 保持长度不变（段落切分与偏移量不漂）", ok8d)
    fail += not ok8d

    # ⑨ ★ 已废断言不参与计数。同日在 `ledger.py` 修的是同一族缺口：
    #    `--supersedes` 只写链接、不翻转旧条状态，于是废掉的东西还在被数。
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        cj = pathlib.Path(td) / "claims.jsonl"
        rows = [
            {"claim_id": "clm-old", "status": "superseded",
             "claim": "旧条：" + QUOTE},
            {"claim_id": "clm-new", "status": "fact",
             "claim": "新条：" + QUOTE},
        ]
        cj.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                      encoding="utf-8")
        acc9 = {"total": 0, "ok": 0, "bad": []}
        scan_claims(cj, acc9)   # ← 打的是 main() 用的同一段代码，不是抄件
        ok9 = acc9["total"] == 1 and [u for u, _ in acc9["bad"]] == ["断言/clm-new"]
        note("已废断言（superseded）不计入，未废的照报", ok9)
        fail += not ok9

    # ⑩ **路径不是引文**（Grotius #168 实测：SKILL.md 两处）
    print("\n══ ★ 路径形状与 @偏移量坐标（2026-08-11 新增）══")
    h = {"total": 0, "ok": 0, "bad": []}
    scan("路径", "摘要写进 `runtime/invocations.jsonl` 和 `memory/episodic.jsonl`。", h)
    ok10 = h["total"] == 0
    note("行内代码里的文件路径不计入（不是逐字引文）", ok10)
    fail += not ok10

    # ⑩′ **反对照**：不含 `/._::` 的普通长引文不许被这条顺手滤掉。
    hb = {"total": 0, "ok": 0, "bad": []}
    scan("非路径", QUOTE, hb)
    ok10b = hb["total"] == 1
    note("**反对照**：普通长引文不受路径规则影响", ok10b)
    fail += not ok10b

    # ⑩″ **反对照的边界**：带空格就不是路径，哪怕含点号——
    #     否则任何以句点结尾的引文都会被误滤。
    hc = {"total": 0, "ok": 0, "bad": []}
    scan("带点句子", "他说：`Up to the present time no one has treated it. Yet men demand it.`", hc)
    ok10c = hc["total"] == 1
    note("**反对照**：含句点但有空格的句子仍算引文（路径规则要求无空白）", ok10c)
    fail += not ok10c

    # ⑪ **`@偏移量` 是坐标**（本流水线自己的写法，`check_quote_integrity` 据此回核）
    i1 = {"total": 0, "ok": 0, "bad": []}
    scan("偏移量", QUOTE + "（同上，@83355。）", i1)
    ok11 = i1["total"] == 1 and not i1["bad"]
    note("`@83355` 认作坐标 → 放行", ok11)
    fail += not ok11

    # ⑪′ **反对照**：位数不够的不算，否则「@3」这种随手编号会把门架空。
    i2 = {"total": 0, "ok": 0, "bad": []}
    scan("短偏移", QUOTE + "（见 @12。）", i2)
    ok11b = len(i2["bad"]) == 1
    note("**反对照**：`@12`（不足 4 位）不算坐标 → 仍报缺", ok11b)
    fail += not ok11b

    # ⑫ **台账窗口并入 evidence_clusters**——坐标本来就该写在那个字段里。
    with tempfile.TemporaryDirectory() as td:
        cj2 = pathlib.Path(td) / "c.jsonl"
        rows2 = [
            {"claim_id": "clm-ev", "status": "pattern", "claim": "他写道：" + QUOTE,
             "evidence_clusters": ["DJBP 1853 拉丁 vol1，Prolegomena，@83307"]},
            {"claim_id": "clm-noev", "status": "pattern", "claim": "他写道：" + QUOTE,
             "evidence_clusters": []},
        ]
        cj2.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows2) + "\n",
                       encoding="utf-8")
        acc12 = {"total": 0, "ok": 0, "bad": []}
        scan_claims(cj2, acc12)
        ok12 = acc12["total"] == 2 and [u for u, _ in acc12["bad"]] == ["断言/clm-noev"]
        note("`evidence_clusters` 里的坐标算数；该字段为空的**仍抓出**", ok12)
        fail += not ok12

    # ⑫″ **反对照：搜索面放宽了，分母不许跟着涨。**
    #     `evidence_clusters` 里本来就带引号的字串（书名、章题）不算逐字引文。
    #     实测：第一版把它拼进扫描面，Grotius 总数从 44 虚涨到 45。
    with tempfile.TemporaryDirectory() as td:
        cj4 = pathlib.Path(td) / "c.jsonl"
        cj4.write_text(json.dumps(
            {"claim_id": "clm-den", "status": "pattern", "claim": "他写道：" + QUOTE,
             "evidence_clusters": [
                 "1853 年拉丁本卷一，章题「Solution des objections contre la doctrine」@83307"]},
            ensure_ascii=False) + "\n", encoding="utf-8")
        acc14 = {"total": 0, "ok": 0, "bad": []}
        scan_claims(cj4, acc14)
        ok14 = acc14["total"] == 1 and not acc14["bad"]
        note(f"**反对照**：证据字段里的引号字串不计入分母（total={acc14['total']}，应为 1）", ok14)
        fail += not ok14

    # ⑫′ **反对照**：`falsifiers` 里的坐标**不算**——那是顺带出现，不是证据定位。
    with tempfile.TemporaryDirectory() as td:
        cj3 = pathlib.Path(td) / "c.jsonl"
        cj3.write_text(json.dumps(
            {"claim_id": "clm-fals", "status": "pattern", "claim": "他写道：" + QUOTE,
             "evidence_clusters": [], "falsifiers": ["若 @83355 起那句不存在，本条作废。"]},
            ensure_ascii=False) + "\n", encoding="utf-8")
        acc13 = {"total": 0, "ok": 0, "bad": []}
        scan_claims(cj3, acc13)
        ok13 = len(acc13["bad"]) == 1
        note("**反对照**：坐标只出现在 `falsifiers` 里 → 不放行", ok13)
        fail += not ok13

    print(f"\n  ✓ 负对照通过（{n[0]}/{n[0]}）" if not fail
          else f"\n  ✗ {fail}/{n[0]} 项未过——本检查器已失效，其「通过」不构成证据")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", type=pathlib.Path, nargs="*", default=[],
                    help="候选答案 JSON（id→文本）或盲判载荷（[{case_id,A,B}]）")
    ap.add_argument("--claims", type=pathlib.Path, help="断言层 claims.jsonl")
    #   ★★★★ 2026-08-11（Shewhart #165 撞出）：**产物从来没被扫过。**
    #     本件此前只收 `--answers`（盲判载荷）与 `--claims`，
    #     而 `quality_check` 传进来的也只有这两样——
    #     **十份 Markdown 产物，也就是用户真正读的那一份，一次都没被检查过。**
    #     后果：缺陷坐在产物里，直到有人生成盲判载荷才冒出来，
    #     那时它看着还像是「答题方没写坐标」——**根因被移了位**。
    #   ★ 全库实测（424 条 ≥30 字符的逐字引文）：**176 条缺坐标（41.5%）**，
    #     17 个工作区只有 4 个干净；**Adams 27/27、Thomson 19/19 全缺，
    #     而这两人都已经判过分、delta 已入账**。
    #   [[gates-cover-json-not-the-prose-users-read]]
    ap.add_argument("--products", type=pathlib.Path, nargs="*", default=[],
                    help="产物 Markdown（十份），逐份扫其中的长逐字引文")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test and not (a.answers or a.claims or a.products):
        return 2 if self_test() else 0
    if not (a.answers or a.claims or a.products):
        ap.error("--answers / --claims / --products 至少给一个（除非只跑 --self-test）")

    acc = {"total": 0, "ok": 0, "bad": []}

    if a.claims:
        scan_claims(a.claims, acc)

    for path in a.answers:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):           # 盲判载荷
            for row in data:
                for side in ("A", "B"):
                    if isinstance(row.get(side), str):
                        scan(f"答案/{row.get('case_id')}:{side}", row[side], acc)
        elif isinstance(data, dict):         # id → 文本
            for k, v in data.items():
                if isinstance(v, str) and not k.startswith("_"):
                    scan(f"答案/{k}", v, acc)

    for path in a.products:
        if path.is_file():
            scan(f"产物/{path.name}", path.read_text(encoding="utf-8", errors="replace"), acc)

    if not acc["total"]:
        print("一条长逐字引文都没扫到——**本次未检查（不是通过）**")
        return 3

    print(f"长逐字引文 {acc['total']} 条，同段带坐标 {acc['ok']} 条，"
          f"**缺坐标 {len(acc['bad'])} 条**")
    for uid, q in acc["bad"]:
        print(f"  ⚠ {uid}: 「{q}…」")
    if acc["bad"]:
        print("\n  ⚠ 缺坐标不等于引文是假的——`check_quote_integrity` 才管真假。"
              "\n    这一件管的是**读者能不能回查**：引文若无从复核，它对读者就只是装饰。")
    else:
        print("  ✓ 每条长引文同段内都能找到坐标线索")
    return 1 if acc["bad"] else 0


if __name__ == "__main__":
    sys.exit(main())


