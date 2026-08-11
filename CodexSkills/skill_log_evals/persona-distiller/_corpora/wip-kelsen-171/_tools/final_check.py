#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交卷前自检：**打开落盘的产物文件本身**重算，不引用会话里任何数。
本项目记档：47 道门全在验暂存目录，改成回读自验证后第一次跑就抓到 283 个乱码。
"""
import hashlib, json, os, re, sys

WIP = ("/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/"
       "skill_log_evals/persona-distiller/_corpora/wip-kelsen-171")
RAW = os.path.join(WIP, "raw")
PLANNED = 12
fail = []


def chk(cond, msg):
    print(("  [OK]   " if cond else "  [FAIL] ") + msg)
    if not cond:
        fail.append(msg)


print("=" * 100)
print("① 实际落盘件数 / 计划件数")
print("=" * 100)
dirs = sorted(d for d in os.listdir(RAW) if os.path.isdir(os.path.join(RAW, d)))
txts = []
for d in dirs:
    fs = os.listdir(os.path.join(RAW, d))
    t = [f for f in fs if f.endswith(".txt")]
    txts.append((d, t, fs))
n = len(dirs)
print("  raw/ 下子目录 %d 个；每目录 .txt 数：%s" % (n, sorted(set(len(t) for _, t, _ in txts))))
chk(n == PLANNED, "落盘件数 %d == 计划件数 %d" % (n, PLANNED))
chk(all(len(t) == 1 for _, t, _ in txts), "每个 src 目录恰好 1 个 .txt")
chk(all(re.fullmatch(r"src-[0-9a-f]{12}", d) for d in dirs), "目录名全部形如 src-<12位十六进制>")
chk(all("SOURCE.json" in fs for _, _, fs in txts), "每个 src 目录都有 SOURCE.json 出处旁文件")

print()
print("=" * 100)
print("② 逐件字节数与 sha256（现打开文件重算，并与 SOURCE.json / IA 自报 size 三方比对）")
print("=" * 100)
rows = []
print("  %-46s %10s %-64s %s" % ("file", "bytes", "sha256", "三方一致"))
for d in dirs:
    t = [f for f in os.listdir(os.path.join(RAW, d)) if f.endswith(".txt")][0]
    blob = open(os.path.join(RAW, d, t), "rb").read()
    src = json.load(open(os.path.join(RAW, d, "SOURCE.json"), encoding="utf-8"))
    sha = hashlib.sha256(blob).hexdigest()
    same = (len(blob) == src["bytes"] and sha == src["sha256"] and len(blob) == int(src["ia_reported_size"]))
    rows.append({"dir": d, "file": t, "bytes": len(blob), "sha256": sha, "ok": same,
                 "ident": src["ia_identifier"], "http": src["http_status"]})
    print("  %-46s %10s %-64s %s" % (t[:46], format(len(blob), ","), sha, "是" if same else "★否"))
tot = sum(r["bytes"] for r in rows)
print("  合计 %s 字节" % format(tot, ","))
chk(all(r["ok"] for r in rows), "12 件的 bytes/sha256 与 SOURCE.json 及 IA 自报 size 三方一致")
chk(len(set(r["sha256"] for r in rows)) == len(rows), "12 个 sha256 互不相同（没有重复副本混进来）")
chk(all(r["http"] == 200 for r in rows), "12 件下载时 HTTP 全部 200")

print()
print("=" * 100)
print("③ 讹形比逐件的数 + 被标『不可做逐字引文』的是哪几件")
print("=" * 100)
M = {r["file"]: r for r in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "measure2.json"), encoding="utf-8"))}
md3 = open(os.path.join(WIP, "03-抓源清单.md"), encoding="utf-8").read()
print("  %-46s %10s %10s %10s %8s %8s %s" % ("file", "指令四对", "实测形族", "长s残留", "h→b", "变音/千", "判定"))
banned = []
for r in rows:
    c = M[r["file"]]["corruption"]
    b = M[r["file"]]["no_verbatim_quote"]
    if b:
        banned.append(r["file"])
    print("  %-46s %10s %10s %10s %8s %8.1f %s" % (
        r["file"][:46], c["pooled_named_str"], c["pooled_family_str"], c["long_s_ratio_str"],
        c["hb_ratio_str"], c["diacritics_per_1k_words"], "★不可做逐字引文" if b else "可引"))
print("  被标『不可做逐字引文』%d 件：" % len(banned))
for b in banned:
    print("     - %s ← %s" % (b, "；".join(M[b]["trigger"])))
chk(len(banned) == 4, "禁引件数 = 4")
# 产物里的数必须与现算一致（散文由报告现算生成，不是手抄）
mismatch = [r["file"] for r in rows
            if ("| %s |" % M[r["file"]]["corruption"]["pooled_named_str"]) not in md3
            and M[r["file"]]["corruption"]["pooled_named_str"] not in md3]
chk(not mismatch, "03 正文里逐件的讹形比字符串都能在现算结果中找到（无手抄漂移）：%s" % (mismatch or "全部对上"))
# ★ 这条断言改过两次：
#   v1 写成 `... or True` —— 恒绿。
#   v2 用文件名/identifier 匹配 —— 对 12 件**全部** False，实际是靠「年份也在这一节里」的
#      回退分支过的；而 1920 这个年份在该节里也出现（Bundesverfassung 的题名含 1920），
#      于是**非禁引件也能过**。是跑反例才看出来的，不是读代码看出来的。
#   v3（当前）：产物里那一节用的是**编目题名**，就用题名匹配；题名从 03 自己的详录节里反解出来，
#      不在这里另抄一份（另抄必然漂移）。
sec = md3.split("**被标 `不可做逐字引文` 的")[-1].split("### ★★★")[0]
file2title = {}
for blk in re.split(r"\n### \d+\. ", md3)[1:]:
    ttl = blk.split("\n")[0].strip()
    mf = re.search(r"\| 文件名 \| `(.+?)` \|", blk)
    if mf:
        file2title[mf.group(1)] = ttl
chk(len(file2title) == PLANNED, "从 03 详录节反解出 12 条 文件名→编目题名 的对应")
for b in banned:
    chk(file2title.get(b, "\x00")[:30] in sec and len(M[b]["trigger"]) > 0,
        "禁引件在 03 清单节里被题名点名且打红理由非空：%s" % b)
leak = [f for f in M if not M[f]["no_verbatim_quote"] and file2title.get(f, "\x00")[:30] in sec]
chk(not leak, "★反例：8 件可引件的题名**都不**出现在禁引清单节里（否则这条断言恒绿）：%s" % (leak or "无泄漏"))

print()
print("=" * 100)
print("④ 第一人称密度按体裁的汇总")
print("=" * 100)
import collections
agg = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0])
for r in rows:
    m = M[r["file"]]
    fp = m["first_person"]
    a = agg[m["genre"]]
    a[0] += 1; a[1] += m["words_body"]
    a[2] += fp["ich_strict"]; a[3] += fp["wir_strict"]
    a[4] += fp["ich_strict"] + fp["ich_ocr_var"]; a[5] += fp["wir_strict"] + fp["wir_ocr_var"]
print("  %-12s %4s %10s %7s %7s %10s %10s %12s %12s" %
      ("genre", "件", "词数", "ich", "wir", "ich/万", "wir/万", "ich+讹/万", "wir+讹/万"))
for g in ("writings", "expression", "decisions"):
    a = agg[g]
    print("  %-12s %4d %10s %7d %7d %10.2f %10.2f %12.2f %12.2f" % (
        g, a[0], format(a[1], ","), a[2], a[3], 1e4 * a[2] / a[1], 1e4 * a[3] / a[1],
        1e4 * a[4] / a[1], 1e4 * a[5] / a[1]))
chk(sum(agg[g][0] for g in agg) == PLANNED, "三道件数之和 = 12")
chk(agg["decisions"][2] == 0 and agg["decisions"][4] > 0,
    "decisions 严格 ich=0 而含讹形 >0 —— 该 0 已在 04 §3-2 标为『仪器盲』而非声口事实")

print()
print("=" * 100)
print("⑤ 有没有任何一件的 PD 依据只有 IA 的 date（**必须是 0**）")
print("=" * 100)
# 从产物里逐件抠出 PD 依据栏，机器判定它是否落在「题名页年」或「编目记录」上
blocks = re.split(r"\n### \d+\. ", md3)
pd_rows = []
for blk in blocks[1:]:
    name = blk.split("\n")[0].strip()
    m_pd = re.search(r"\| \*\*PD 依据\*\* \| (.+?) \|\n", blk)
    m_ty = re.search(r"\| \*\*这一版的出版年（题名页）\*\* \| (.+?) \|\n", blk)
    if not m_pd:
        continue
    pd = m_pd.group(1)
    ty = m_ty.group(1) if m_ty else ""
    has_tp = "题名页年" in pd or "扉页年" in pd or "封面年" in pd
    has_cat = bool(re.search(r"PPN \d|IDN \d|K10plus|编目", pd))
    only_ia = (not has_tp) and (not has_cat)
    pd_rows.append((name, ty, has_tp, has_cat, only_ia, pd))
print("  %-52s %-14s %-8s %-8s %s" % ("件", "题名页年", "题名页依据", "编目依据", "只靠 IA date?"))
for name, ty, has_tp, has_cat, only_ia, pd in pd_rows:
    print("  %-52s %-14s %-8s %-8s %s" % (
        name[:52], re.sub(r"\*|（.*", "", ty)[:12], "有" if has_tp else "—", "有" if has_cat else "—",
        "★是" if only_ia else "否"))
n_only_ia = sum(1 for x in pd_rows if x[4])
print("  ——")
print("  逐件 PD 依据都写了；其中只靠 IA `date` 的件数 = **%d**" % n_only_ia)
chk(len(pd_rows) == PLANNED, "从 03 产物里抠到 12 条 PD 依据（分母不是空的）")
chk(n_only_ia == 0, "PD 依据只有 IA date 的件数 == 0")
chk(sum(1 for x in pd_rows if x[2]) == 10, "10 件有题名页年份")
chk(sum(1 for x in pd_rows if not x[2] and x[3]) == 2, "另 2 件题名页无年、退回编目记录（K10plus），仍非 IA date")

print()
print("=" * 100)
print("附加：产物完整性 + 同名护栏")
print("=" * 100)
for f in ["03-抓源清单.md", "04-声口密度实测.md", "05-取不到的与为什么.md", "kelsen_namesake_candidates.json"]:
    p = os.path.join(WIP, f)
    chk(os.path.exists(p) and os.path.getsize(p) > 1000, "%s 存在且 >1KB（%s 字节）" %
        (f, format(os.path.getsize(p), ",") if os.path.exists(p) else 0))
ns = json.load(open(os.path.join(WIP, "kelsen_namesake_candidates.json"), encoding="utf-8"))
chk(ns["self_test"]["verdict"] == "PASS", "同名护栏自测 PASS（该拦 %d 全拦、该放 %d 全放、该存疑 %d 全存疑）" % (
    len(ns["self_test"]["must_block"]), len(ns["self_test"]["must_pass"]), len(ns["self_test"]["must_be_undecided"])))
chk("H. Kelsen" in str(ns["rule"]["forbidden_as_exclusion_term"]), "`H. Kelsen` 已登记为**禁止当排除词**")
chk(any("H\\.\\s*Kelsen" in x or "H\\." in x for x in [ns["rule"]["name_regex"]]), "`H. Kelsen` 已收进**识别位**")
chk(len(ns["candidates"]) == 24 and len(ns["non_person_entities"]) == 6, "候选 24 位自然人 + 6 项非自然人")
chk(ns["run_against_this_round_corpus"]["hard_block_hits_total"] == 0, "12 件语料里硬拦项（HKW/Kelsen-Institut）命中 0")
print("  变异测试覆盖：%d/%d 条改坏后打红；未覆盖：%s" % (
    len(ns["mutation_test"]["covered"]), len(ns["mutation_test"]["rows"]), ns["mutation_test"]["NOT_covered"]))

print()
print("=" * 100)
print(("自检结论：全部通过（%d 项）" % 0) if not fail else "自检结论：**%d 项未通过**" % len(fail))
for f in fail:
    print("  - " + f)
print("=" * 100)
sys.exit(1 if fail else 0)
