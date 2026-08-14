#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流水线产物 → `evidence/source-ledger.jsonl`（判据与研究道真正读的那份台账）。

用法：
    python3 emit_source_ledger.py --raw <raw 目录> --workspace <workspaces/<slug> 目录>

输入：`_fetch-manifest.json`＋`_primary.json`＋`_lanes.json`＋`_dedup.json`
输出：`<workspace>/evidence/source-ledger.jsonl`

**四件不能省的：**

① **`derived_from` 由查重簇填。**
   同一部书的 N 个扫描件必须互相指认，否则下游把它们数成 N 处独立证据
   （[[two-source-ids-is-not-two-evidences]]：落成判据后 11 人里 7 人有塌缩、共 57 条）。
   ★ 簇内取**词数最多**的那份当代表，其余 `derived_from` 指向它。

② **`title` 用真题名，不用文件名。**
   存量里 `title` 一直是文件名（`0001-conv-1907-vxxvi.txt`），
   那是已知缺陷（台账「title=文件名」）。**新做的不重蹈。**

③ **`split` 一律先写 `train`，holdout 由人另行指定。**
   holdout 分错比不分更糟——被判过分的产物无法回退
   （[[a-checker-nothing-calls-is-not-a-checker]]：45 份 holdout 里 18 份从未真隔离）。
   本工具**不猜**，并在输出里印一行提醒。

④ **`rights` 写 `pre<PD分界>`（= `pre1931`）并带上依据年份。**
   PD 分界随年份滚动（2026 年是 ≤1930），**不写死**
   （[[pd-cutoff-rolls-every-january]]：曾写死 1929 陈旧两年）。

★ 退出码：0=写出；2=输入缺；3=一条都没写出。
"""
import argparse
import datetime
import json
import pathlib
import re
import sys

THIS_YEAR = 2026
# ★★ 与仓内判据同名同值：`check_filename_year_vs_ledger.py` 写的是
#   `PD_CUTOFF = 1931  # 公有领域 = 出版于 ≤1930，即「1931 年以前」`
#   —— **分界值是 1931，而「可用的最晚出版年」是 1930**。这两个数差 1，
#   我第一版把 rights 印成 `pre1932`、依据写成「≤1931」，**两处都差一年**
#   （[[pd-cutoff-rolls-every-january]] 点名的正是这个坑）。
PD_CUTOFF = THIS_YEAR - 95            # 2026 → 1931（「1931 年以前」）
LATEST_PD_YEAR = PD_CUTOFF - 1        # 2026 → 1930（可用的最晚出版年）

# ★ 没有 IA 编目年时的兜底顺序：**正文里的版权页 > 题名页年份最大值**。
#   实测（2026-08-12）20 条没有编目年的里，有两条正文里写得清清楚楚：
#     `Berlin Druck und Verlag von Georg Reimer 1913`
#     `Copyright, 1919, by Yale University Press`
#   ——先前只取「题名页年份最大值」，把这类确切线索白白丢掉了。
# ★★ 「全集」里常常装着**第三方的东西**。实例：
#   `completeworksofa11linco` 题名页写
#   `With a General Introduction by Richard Watson Gilder, and Special Articles
#    by Other Eminent Persons`，**开篇就是林肯身后别人的一篇布道**
#   （`WHILE I speak to you to-day, the body of the President … is lying honored and loved`）。
#   ⇒ 那一层里的第一人称**是编者/悼念者的，不是他的**。
#   全库实测：**611 份一手里 89 份（15%）前置页含第三方**，Lincoln 高达 51%。
#   本字段**不改 tier**（编者本整册仍是他的文集），只把这件事**标出来**，
#   供研究道取引文时逐条核说话人（[[gates-count-sources-not-voice]]）。
# ★ 匹配前必须**归一空白**：OCR 的词间是双空格＋换行
#   （`Special  Articles \n\nby  Other  Eminent  Persons`），
#   按单空格写的正则**一份都匹配不到**——我第一版就这样，报出「只有 2 份」。
THIRD_PARTY_RE = re.compile(
    r"(special articles by other eminent persons|general introduction by|"
    r"with an introduction by|edited,? with|introduction and notes by|"
    r"herausgegeben von|mit einer einleitung von|avec une introduction de|"
    r"con introduzione di|a cura di)")

IMPRINT_RE = [
    re.compile(r"[Cc]opyright,?\s+(?:by\s+[^\n,]{0,40},?\s*)?((?:1[5-9]|20)\d{2})"),
    re.compile(r"(?:Verlag|Druck und Verlag|Press|PRESS|& Co\.|Sons|Company)[^\n]{0,60}?"
               r"\b((?:1[5-9]|20)\d{2})\b"),
]


# ★ 这几个字段本工具是**按规则重算**的，而它们同时也是人会去改的地方。
#   重跑一次就把人的裁定覆盖回规则值 —— 所以要在写盘前拦一次。
#   `split` 尤其要命：工具无条件写 `train`，而它自己的输出里印着
#   「holdout 由人另行指定，本工具不猜」—— **重跑会抹掉每一个 holdout 标记**。
def locator_for(ident, url):
    """出处从 `source_url` **现推**，不许写死站名。

    原来这里硬写 `f"archive.org item {i}"` —— 抓取侧早已不止一个通道
    （同目录就有 `fetch_kramerius.py`，台账里已有 MZK/MDZ、Wikisource/Gutenberg
    的源），拿它跑一份捷克 NDK 的语料就会给对方的馆藏盖上 archive.org 的出处，
    **凭空造一个出处**。

    ★ 实测：现有 19 份 manifest 的 source_url **全部**是 archive.org，
      所以今天 0 条是错的 —— 这是**预防**，不是在修既发生的错。
      archive.org 那一支的输出与旧版**逐字节相同**，存量台账不会churn。
    ★ 取不到 url 时**不替它假设一个站**，明写未证实。[[empty-default-swallows-unknown]]
    """
    m = re.match(r"https?://([^/]+)", str(url or ""))
    if not m:
        return "item %s（**source_url 缺失，站点未证实**）" % ident
    host = m.group(1).lower()
    if host.startswith("www."):
        host = host[4:]
    return "%s item %s" % (host, ident)


PROTECTED_FIELDS = (
    "tier", "rights", "tier_reason", "extraction_status",
    "attribution", "split", "language", "dimensions",
)


def human_verdicts_at_risk(existing, generated, expected_gone=()):
    """→ [(source_id, 字段, 现值, 重跑后的值)]，空列表表示重跑不会覆盖任何人工裁定。

    两类算「人工痕迹」：
      ① `PROTECTED_FIELDS` 里现值与重算值不同的
      ② 键名以 `★` 开头的字段（本仓记人工裁定的既定写法），重跑后会整个消失

    `expected_gone`：**有人明写要剔**的 source_id（manifest 里 `status=剔除`
    且写了 `剔除理由`）。整行消失分两种，**不能一刀切**：
      · 有人写了理由要剔 → 这正是 `drop_source.sh` 的本意，放行
      · 没人说过要剔却没了 → **无声丢行，照拦**
    """
    gen = {g.get("source_id"): g for g in generated}
    gone_ok = set(expected_gone)
    out = []
    for row in existing:
        s = row.get("source_id")
        g = gen.get(s)
        if g is None:
            if s not in gone_ok:
                out.append((s, "<整行>", "在册", "**重跑后不存在，且没人说过要剔**"))
            continue
        for k in PROTECTED_FIELDS:
            if k in row and row.get(k) != g.get(k):
                out.append((s, k, row.get(k), g.get(k)))
        for k in row:
            # ★ 要问「新行里还在不在」，不能见 ★ 就报 ——
            #   否则 `--preserve` 接续完了它照样报「会被删掉」，
            #   接续与拒跑互相打架，rc 永远是 3。自测第 19 条就是抓这个的。
            if str(k).startswith("★") and g.get(k) != row[k]:
                out.append((s, k, str(row[k])[:50] + "…",
                            "**会被删掉**" if k not in g else g.get(k)))
    return out


def carry_forward(existing, generated):
    """把现有台账里的人工裁定**接续**到新生成的行上（按 source_id 对齐）。

    → (新的 generated, 接续明细)。已不在册的行不接（源被剔掉了，裁定随之作废）。

    ★ 为什么要有它：`drop_source.sh` 剔一份语料要重出台账，
      而它自己第 52 行写着「**若已切过密封集，重跑 assign_holdout**」——
      作者知道 holdout 会被抹掉，处置办法却是**一句叮嘱人记得的散文**。
      [[a-rule-in-a-doc-has-no-enforcer]]
    """
    old = {o.get("source_id"): o for o in existing}
    moved = []
    for g in generated:
        o = old.get(g.get("source_id"))
        if not o:
            continue
        for k in PROTECTED_FIELDS:
            if k in o and o.get(k) != g.get(k):
                moved.append((g["source_id"], k, g.get(k), o.get(k)))
                g[k] = o[k]
        for k, v in o.items():
            if str(k).startswith("★"):
                moved.append((g["source_id"], k, "<新行没有>", "接续"))
                g[k] = v
    return generated, moved


def _selftest() -> int:
    bad = 0
    base = {"source_id": "src-a", "tier": "S1", "split": "train",
            "attribution": "OTHER", "extraction_status": "raw"}
    gen = [dict(base)]
    cases = [
        ([dict(base)], 0, "一字不差 → 不拦"),
        ([dict(base, tier="P1")], 1, "人工改过 tier → 拦"),
        ([dict(base, split="holdout")], 1, "**holdout 标记 → 必须拦**"),
        ([dict(base, extraction_status="failed")], 1, "抽取失败标记 → 拦"),
        ([dict(base, attribution="HIS-OWN")], 1, "归属订正 → 拦"),
        ([dict(base, **{"★ 归属订正-2026-08-15": "题名页是别人"})], 1, "★ 说明字段 → 拦"),
        ([{"source_id": "src-gone", "tier": "S1"}], 1, "整行消失、没人说过要剔 → 拦"),
        ([], 0, "空台账（新工作区）→ 不拦"),
    ]
    for existing, want, label in cases:
        got = len(human_verdicts_at_risk(existing, gen))
        if (got > 0) != (want > 0):
            print("  ✗ %s：期望 %s 得 %d 处" % (label, "拦" if want else "不拦", got))
            bad += 1

    # 整行消失的两面：明写要剔 → 放行；没人说过 → 拦。**两面都要测**，
    # 只测一面会让「一刀切放行」也满分。[[zero-hit-gates-must-prove-they-can-hit]]
    gone = [{"source_id": "src-gone", "tier": "S1"}]
    for exp, want, label in [((), 1, "没人说要剔 → 拦"), (("src-gone",), 0, "明写要剔 → 放行")]:
        got = len(human_verdicts_at_risk(gone, gen, exp))
        if (got > 0) != (want > 0):
            print("  ✗ 整行消失·%s：期望 %s 得 %d 处" % (label, "拦" if want else "放行", got))
            bad += 1

    # ── 出处不许写死 ──
    loc_cases = [
        ("https://archive.org/download/abc/abc_djvu.txt", "abc",
         "archive.org item abc", "archive.org 与旧版逐字节相同"),
        ("https://kramerius5.nkp.cz/uuid/xyz", "xyz",
         "kramerius5.nkp.cz item xyz", "**捷克 NDK 不许盖成 archive.org**"),
        ("https://www.gallica.bnf.fr/ark:/1/2", "g1",
         "gallica.bnf.fr item g1", "去掉 www."),
        ("", "n1", "item n1（**source_url 缺失，站点未证实**）", "**取不到就不许假设一个站**"),
        (None, "n2", "item n2（**source_url 缺失，站点未证实**）", "None 同上"),
    ]
    for url, ident, want_s, label in loc_cases:
        got_s = locator_for(ident, url)
        if got_s != want_s:
            print("  ✗ %s：期望 %r 得 %r" % (label, want_s, got_s))
            bad += 1
    # ── 接续：接完之后**必须已无可失**（两件互为对方的验收）──
    cf = [
        ([dict(base, split="holdout", extraction_status="failed",
               **{"★ 理由": "天城文噪声"})], "holdout", 3),
        ([dict(base)], "train", 0),
        ([], "train", 0),
    ]
    for existing, want_split, want_moved in cf:
        g2, moved = carry_forward(existing, [dict(base)])
        if len(moved) != want_moved or g2[0].get("split") != want_split:
            print("  ✗ 接续：期望 %d 处/split=%s，得 %d 处/split=%s"
                  % (want_moved, want_split, len(moved), g2[0].get("split")))
            bad += 1
        if human_verdicts_at_risk(existing, g2):
            print("  ✗ **接续之后仍有可失** —— 接续没接干净")
            bad += 1
    n = len(cases) + 2 + len(loc_cases) + 2 * len(cf)
    print("自测 %d/%d" % (n - bad, n))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw")
    ap.add_argument("--workspace")
    ap.add_argument("--preserve", action="store_true",
                    help="按 source_id 把现有台账里的人工裁定**接续**到新行上"
                         "（剔源重出台账时用这个，不要用 --force）。")
    ap.add_argument("--force", action="store_true",
                    help="**覆盖**已有台账里的人工裁定（tier/rights/split/归属/抽取状态）。"
                         "默认拒跑。用之前先把现有台账备份出去。")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if not (a.raw and a.workspace):
        ap.error("要 --raw 和 --workspace（或只跑 --self-test）")
    raw, ws = pathlib.Path(a.raw), pathlib.Path(a.workspace)
    need = ["_fetch-manifest.json", "_primary.json", "_lanes.json", "_dedup.json"]
    missing = [n for n in need if not (raw / n).exists()]
    if missing:
        print("缺输入：" + "、".join(missing) + "——先跑完流水线", file=sys.stderr)
        return 2

    mf = json.loads((raw / "_fetch-manifest.json").read_text(encoding="utf-8"))
    prim = {o["identifier"]: o for o in json.loads((raw / "_primary.json").read_text(encoding="utf-8"))["明细"]}
    lanes = {o["identifier"]: o["道"] for o in json.loads((raw / "_lanes.json").read_text(encoding="utf-8"))["明细"]}
    dedup = json.loads((raw / "_dedup.json").read_text(encoding="utf-8"))

    recs = [r for r in mf["记录"] if r["status"] == "已取回"]
    words = {r["identifier"]: r.get("words", 0) for r in recs}

    # ① 簇 → derived_from
    rep, parent = {}, {}
    for cl in dedup.get("重复簇", []):
        head = max(cl, key=lambda i: words.get(i, 0))
        rep[head] = cl
        for i in cl:
            if i != head:
                parent[i] = head

    def sid(ident):
        r = next((x for x in recs if x["identifier"] == ident), None)
        return "src-" + (r["sha256"][:12] if r else ident[:12])

    out, skipped = [], 0
    for r in recs:
        i = r["identifier"]
        lane = lanes.get(i, "")
        if lane == "未分道":
            skipped += 1
            continue
        p = prim.get(i, {})
        is_primary = p.get("档") == "一手"
        ti = r.get("ia_title"); ti = "; ".join(ti) if isinstance(ti, list) else str(ti or "")
        au = r.get("ia_creator"); au = "; ".join(au) if isinstance(au, list) else str(au or "")
        # ★★ 出版年**不取 `min(titlepage_years)`**。
        #   第一版这么取，于是 Bismarck（1815–1898）的书信集被标成
        #   **出版年 1647 / 1761 / 1815** —— 正文前几页里最早那个四位数
        #   往往是**文中提到的年份**（或藏书章、OCR 噪声），不是版次年。
        #   ⇒ 优先用 IA 的编目年（图书馆说的），题名页年份留作**佐证与交叉核对**。
        #   ★ 仍要记住 `ia_date` 可能是原作年不是版次年
        #     （`_IA的date是原作年不是版次年-2026-08-11.md`），所以两者不一致时**印出来**。
        yrs = sorted(int(y) for y in (r.get("titlepage_years") or []) if y.isdigit())
        cat = ""
        for fld in ("ia_date", "ia_year"):
            v = str(r.get(fld, "") or "")
            m = re.search(r"\b(1[5-9]\d{2}|20[0-2]\d)\b", v)
            if m:
                cat = m.group(1)
                break
        third = False
        f_all = raw / r["file"]
        if f_all.exists():
            h8 = re.sub(r"\s+", " ",
                        f_all.read_text(encoding="utf-8", errors="replace")[:8000]).lower()
            third = bool(THIRD_PARTY_RE.search(h8))
        imp = ""
        if not cat:
            f = raw / r["file"]
            if f.exists():
                h = "\n".join(f.read_text(encoding="utf-8", errors="replace").splitlines()[:200])
                for rx in IMPRINT_RE:
                    m2 = rx.search(h)
                    if m2:
                        imp = m2.group(1)
                        break
        if cat:
            pub, basis = cat, "IA 编目年"
        elif imp:
            pub, basis = imp, "正文版权页／出版者行的年份"
        elif yrs:
            pub, basis = str(yrs[-1]), "**题名页年份取最大，未经编目确认**"
        else:
            pub, basis = "", "**取不到**"
        out.append({
            "source_id": sid(i),
            "title": ti or i,                       # ② 真题名，不用文件名
            "author": au,
            "published_at": pub,
            "url": r.get("source_url", ""),
            "locator": locator_for(i, r.get("source_url")),
            "local_path": f"raw/{i}.txt",
            "original_name": f"{i}.txt",
            "checksum": r.get("sha256", ""),
            "source_type": "document",
            "language": None,
            "dimensions": [lane],
            "tier": "P1" if is_primary else "S1",
            "split": "train",                       # ③ holdout 由人另指
            "attribution": "HIS-OWN" if is_primary else "OTHER",
            "authorship_evidence": ["ia-creator-field"],
            "authorship_detail": {"code": "ia-creator-field",
                                  "evidence": (p.get("依据") or "")[:200]},
            "rights": f"pre{PD_CUTOFF}",            # ④ 随年份滚动；= pre1931
            "published_at_basis": basis,
            # ★ 前置页里有第三方编者/导言/文章 —— **不改 tier，只标出来**
            "front_matter_third_party": third,
            "titlepage_years": [str(y) for y in yrs],
            "rights_basis": (f"公有领域 = 出版于 ≤{LATEST_PD_YEAR}"
                             f"（分界 {PD_CUTOFF} = {THIS_YEAR} − 95）；"
                             f"出版年 {pub or '**未取到**'}（{basis}）；"
                             f"题名页年份 {yrs or '无'}"),
            "extraction_status": "raw",
            "normalized_path": None,
            "normalized_checksum": None,
            "abstract": None,
            "redactions": None,
            "derived_from": ([sid(parent[i])] if i in parent else []),
            "accessed_at": r.get("fetched_at", ""),
            "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        })

    if not out:
        print("**一条都没写出** —— 不是「没有源」，是全部落在未分道", file=sys.stderr)
        return 3

    ev = ws / "evidence"; ev.mkdir(parents=True, exist_ok=True)
    led = ev / "source-ledger.jsonl"

    # ★★ 重跑前先 diff，有人工痕迹就拒跑（任务 #120）
    #   本工具是**纯重生成**：它一个字都不读现有台账，
    #   `split` 无条件写 `train`、`attribution`/`tier`/`rights`/`extraction_status`
    #   全部按规则重算。于是重跑一次就**静默撤销**：
    #     · 所有 holdout 标记（工具自己印着「holdout 由人另行指定，本工具不猜」，
    #       却又把每一行都写回 train）
    #     · 归属订正（HIS-OWN → OTHER）
    #     · 抽取失败标记（raw → failed）
    #     · 人工定的 tier / rights / tier_reason
    #   2026-08-14 真发生过：Burbank 的 tier=U→P1、rights=未定→pre1931、
    #   tier_reason→None 被一次重跑抹掉，靠备份逐字节还原。
    #   [[regenerating-a-file-silently-reverts-human-decisions]]
    existing = ([json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
                if led.exists() else [])

    if a.preserve and existing:
        out, moved = carry_forward(existing, out)
        print("  接续人工裁定 %d 处（%d 行受影响）"
              % (len(moved), len({m[0] for m in moved})), file=sys.stderr)
        for m in moved[:10]:
            print("    %s｜%s：%r → %r" % m, file=sys.stderr)
        if len(moved) > 10:
            print("    …… 另有 %d 处" % (len(moved) - 10), file=sys.stderr)

    # 有人明写理由要剔的，整行消失是本意，不算丢裁定；没写理由的照拦。
    dropped_ok = {"src-" + str(rec.get("sha256") or "")[:12]
                  for rec in mf["记录"]
                  if rec.get("status") == "剔除" and rec.get("剔除理由")}

    if existing and not a.force:
        losses = human_verdicts_at_risk(existing, out, dropped_ok)
        if losses:
            print(f"✗ **拒跑**：重跑会覆盖 {len(losses)} 处人工裁定。", file=sys.stderr)
            for sidv, field, old, new in losses[:20]:
                print(f"    {sidv}｜{field}：{old!r} → {new!r}", file=sys.stderr)
            if len(losses) > 20:
                print(f"    …… 另有 {len(losses) - 20} 处", file=sys.stderr)
            print("  想留住它们：加 `--preserve`（按 source_id 接续过去）。", file=sys.stderr)
            print("  确认要丢掉：加 `--force`（**先把现有台账备份出去**）。", file=sys.stderr)
            return 3

    led.write_text(
        "\n".join(json.dumps(o, ensure_ascii=False) for o in out) + "\n", encoding="utf-8")

    lane_n = len({o["dimensions"][0] for o in out})
    pn = sum(1 for o in out if o["tier"] == "P1")
    dn = sum(1 for o in out if o["derived_from"])
    print(f"→ {ev / 'source-ledger.jsonl'}｜{len(out)} 条"
          + (f"（**未分道跳过 {skipped} 条**）" if skipped else ""))
    print(f"  一手 P1 {pn}｜二手 S1 {len(out) - pn}｜道 {lane_n}"
          f"｜**derived_from 已填 {dn} 条**（{len(rep)} 个重复簇）")
    print(f"  ★ `split` 全部写作 `train` —— **holdout 由人另行指定，本工具不猜**")
    print(f"  ★ `rights` = pre{PD_CUTOFF}（出版年 ≤{LATEST_PD_YEAR}；{THIS_YEAR} − 95，随年份滚动）")
    noc = [o for o in out if "未经编目确认" in o["published_at_basis"]]
    if noc:
        print(f"  ⚠️ **{len(noc)} 条没有编目年**，出版年取自题名页最大值——**这些要人核**")
    odd = [o for o in out if o["published_at"].isdigit() and o["titlepage_years"]
           and int(o["published_at"]) < min(int(y) for y in o["titlepage_years"]) - 60]
    if odd:
        print(f"  ⚠️ 编目年比题名页最早年份还早 60 年以上的 {len(odd)} 条（**原作年 vs 版次年**）："
              + "、".join(f'{o["source_id"]}({o["published_at"]})' for o in odd[:5]))
    late = [o for o in out if o["published_at"].isdigit() and int(o["published_at"]) > LATEST_PD_YEAR]
    if late:
        print(f"  ⚠️ **题名页年份 >{LATEST_PD_YEAR} 的有 {len(late)} 条**，逐条核："
              + "、".join(f'{o["source_id"]}({o["published_at"]})' for o in late[:6]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
