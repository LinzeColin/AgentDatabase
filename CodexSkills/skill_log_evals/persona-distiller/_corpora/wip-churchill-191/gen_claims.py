#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Churchill #191 断言层：引文由脚本按偏移抽出并断言。

每条引文过三关：① 逐字存在 ② 唯一 ③ **不被判成借用声口**。
两份源整份禁取（见 gen_research.py 的理由）：
  《Lord Randolph Churchill》(1906) —— 他写他父亲的传记，满篇转引，且用单引号；
  《Savrola》(1900) —— 小说。
"""
import hashlib, importlib.util, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
W = HERE / "workspaces" / "winston-churchill"
_s = importlib.util.spec_from_file_location(
    "fbv", HERE.parent.parent / "_ledgers/_pipeline/flag_borrowed_voice.py")
fbv = importlib.util.module_from_spec(_s); _s.loader.exec_module(fbv)
ROWS = {json.loads(l)["source_id"]: json.loads(l)
        for l in (W / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
BANNED = {"src-c53e1c37f040", "src-0af00d0f0365", "src-cd511a154ee0"}
_T = {}


def norm(sid):
    if sid not in _T:
        _T[sid] = fbv.dehyphen((W / ROWS[sid]["local_path"]).read_text(encoding="utf-8", errors="replace"))
    return _T[sid]


def Q(sid, a, b):
    assert sid not in BANNED, f"{sid} 在禁取名单里"
    t = norm(sid); raw = t[a:b]
    assert t.count(raw) == 1, f"{sid}@{a} 不唯一"
    assert not fbv.judge(t, a, raw), f"{sid}@{a} 被判成借用声口"
    return " ".join(raw.split())


def C(cat, body, sids, ev, fal, ctx, conf, scope):
    return {"claim_id": "clm-" + hashlib.sha256(body.encode()).hexdigest()[:12],
            "category": cat, "status": cat, "claim": body, "source_ids": sids,
            "evidence_clusters": ev, "falsifiers": fal, "contexts": ctx,
            "confidence": conf, "time_scope": scope, "author_role": "distiller",
            "created_at": "2026-08-13T00:00:00Z",
            "alternative_explanations": [], "counter_source_ids": []}


RW, LL, ME, WC, MK = ("src-925ef102d33e", "src-934c9771e8e3", "src-0db9f607011e",
                      "src-615074b71a84", "src-d6dfa533902a")

CLAIMS = [
 C("fact", "**1899 年 5 月，经 Sir Reginald Wingate 引荐，他与 Zubair 长谈了一次**："
   "`" + Q(RW, 82527, 82680) + "`（`" + RW + "`，1899）。",
   [RW], ["1899《The River War》Vol I（另有 Vol II 与 1902 合卷本）"],
   ["若该句落在他人叙述的转录之下 ⇒ 撤销本条"],
   ["被问他在苏丹见过谁", "被问他怎么取得第一手材料"], 0.88, "1899"),
 C("fact", "**他在 Harrow 待了近四年半，其中三年在陆军班**："
   "`" + Q(ME, 43457, 43545) + "`（`" + ME + "`，1930）。",
   [ME], ["1930《My Early Life》（两个印本）"],
   ["若另有材料给出不同年数 ⇒ 以更早的一手为准"],
   ["被问他的学生时代"], 0.9, "1888-1893"),
 C("fact", "**考进 Sandhurst 他用了三次**："
   "`" + Q(ME, 52164, 52220) + "`（`" + ME + "`，1930）——"
   "这句紧跟在章题 EXAMINATIONS 之下，是他自己写的自陈。",
   [ME], ["1930《My Early Life》"],
   ["若该句属编者补注 ⇒ 撤销本条"],
   ["被问他考试怎么样", "被问他早年的挫折"], 0.88, "1893"),
 C("fact", "**1895 年他还是年轻军官时，受邀与 Sir William Harcourt 共进午餐**："
   "`" + Q(WC, 43528, 43650) + "`（`" + WC + "`，1923）。",
   [WC], ["1923《The World Crisis 1911-1918》（另有三个卷次/印本）"],
   ["若该段属他人回忆的转引 ⇒ 撤销本条"],
   ["被问他何时接触到政界高层"], 0.85, "1895"),
 C("fact", "**1904 年他因自由贸易问题穿越议院地板**（换党）："
   "`" + Q(WC, 62508, 62640) + "`（`" + WC + "`，1923）。",
   [WC], ["1923《The World Crisis》"],
   ["若该句的年份在其他印本里不同 ⇒ 以最早印本为准"],
   ["被问他的党派立场怎么变的"], 0.9, "1904"),
 C("fact", "**1900 年冬他在都柏林讲布尔战争时重访了 'The Little Lodge'**："
   "`" + Q(ME, 15320, 15420) + "`（`" + ME + "`，1930）。",
   [ME], ["1930《My Early Life》"],
   ["若该地名指的不是他童年住处 ⇒ 修正射程"],
   ["被问他与爱尔兰的关系", "被问他早年住过哪里"], 0.82, "1900"),

 C("work-method", "**先把最流行的那个解释整条划掉，再给自己的**：第一步点名当时通行的归因，"
   "第二步用 `never … solely or even mainly` 把它整条否掉，第三步才给自己的解释。"
   "判据：否定句里带 `I believe` 这类归属标记——**标明是我的判断，同时当事实主张下**："
   "`" + Q(RW, 91424, 91580) + "`（`" + RW + "`，1899）。",
   [RW], ["1899《The River War》Vol I"],
   ["若他多数论证是「补充一个因素」而非「划掉一个解释」 ⇒ 本条不成立"],
   ["要替他分析一场动乱的成因", "被问他怎么反驳通行说法"], 0.82, "1899"),
 C("work-method", "**战略判断用成本语言下，不用是非语言**：第一步不问对错，"
   "第二步算负担得起负担不起，第三步把现成说法放进引号里否掉。"
   "判据：句中出现 `could not afford`／`we must protect` 这类**账面动词**："
   "`" + Q(WC, 33964, 34140) + "`（`" + WC + "`，1923）。",
   [WC], ["1923《The World Crisis》"],
   ["若他的战略判断多以道义措辞给出 ⇒ 本条不成立"],
   ["要替他评估一项外交选择"], 0.8, "1923"),
 C("work-method", "**争论以一个具体到荒谬的条件收尾，而不是以结论收尾**：第一步陈述两方立场，"
   "第二步不裁决，第三步给一个荒谬但具体的条件把话头收掉。"
   "判据：结尾句是**条件从句 + 第一人称承诺**："
   "`" + Q(LL, 16187, 16290) + "`（`" + LL + "`，1900）。",
   [LL], ["1900《London to Ladysmith via Pretoria》"],
   ["若他多数争论以明确结论收尾 ⇒ 本条不成立"],
   ["要替他处理一场他不想裁决的争论"], 0.78, "1900"),
 C("work-method", "**转述别人给的细节时明写出处**：第一步给出细节，第二步紧跟一句"
   "「这一段我得自某人」。判据：句中出现 `I am indebted to` 这类致谢式归属——"
   "`" + Q(MK, 164567, 164720) + "`（`" + MK + "`，1899）。",
   [MK], ["1899《The Story of the Malakand Field Force》"],
   ["若他大量使用未标出处的转述 ⇒ 本条射程需收窄"],
   ["要替他写一段依赖他人材料的叙述"], 0.8, "1899"),

 C("boundary", "**他写他父亲的传记时，正文里大量是转引的书信与校友回忆**，"
   "而那些引语用的是**单引号**。⇒ 从《Lord Randolph Churchill》(1906) 里取来的第一人称，"
   "**不能默认是他的**；本产物对该书整份不取引文。",
   ["src-c53e1c37f040"], ["1906《Lord Randolph Churchill》（两个印本）"],
   ["若能逐段分清哪些是他的叙述 ⇒ 本条限制可放宽"],
   ["被问他父亲的事", "被问他早年的家庭"], 0.9, "1906"),
 C("mental-model", "**手段与目的分两半说**：`" + Q(RW, 40980, 41043) + "`"
   "（`" + RW + "`，1899）——一句话拆成对仗的两半，手段一半、目的一半。"
   "⇒ 他给定义时爱用这种两半式，而不是一个复合从句。",
   [RW], ["1899《The River War》Vol I"],
   ["若他别处的定义多为复合从句 ⇒ 本条射程需收窄"],
   ["要替他下一个定义"], 0.75, "1899"),
 C("hypothesis", "**「他的公开讲话」这一面，本产物只能隔着第三方编者看**——"
   "语料里唯一的演说材料是 1915 年**别人编的**汇编，被判成二手；"
   "他自己出的讲辞集不在本轮射程内。⇒ 涉及他演说风格的问题，本产物是薄的。",
   ["src-c9bbe07b2555"], ["1915《Great speeches of the war》（第三方汇编）"],
   ["★ 若取到他自己出版的讲辞集 ⇒ 本条应被更强的证据取代"],
   ["被问他的演说", "被问这份档案的弱面在哪"], 0.7, "1915"),
]


def main():
    out = W / "evidence/claims.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in CLAIMS) + "\n", encoding="utf-8")
    import collections
    print(f"✓ {len(CLAIMS)} 条断言｜类别 {dict(collections.Counter(c['category'] for c in CLAIMS))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
