#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**归属依据门**：印刷时代之前的人物，靠什么证明「这是他写的」。

## 这个缺口是 Hippocrates 逼出来的（2026-08-02）

v0.0.0.23 的分族配重把 `NEXT` 从材料建工师改成了 0 人的医疗护理师，
队列首位是 **Hippocrates**。探源结论出乎意料：

> **一手源随手可取，而归属不成立。**
> 希波克拉底文集约 60 篇全文在 Perseus 与 Gutenberg 上公开（实测均 HTTP 200），
> 但学界公认**没有任何一篇能确定归到历史上的希波克拉底名下**
> （Craik 2015 书名给「Hippocratic」加引号即为此意）；
> 唯一归属相对确定的《Nature of Man》**确定的是「不是他」**——出自其女婿 Polybus。

抓 45 条源毫无难度。难的是抓完之后 `own_voice_ratio` 的真值是 0。

## `check_authorship.py` 为什么拦不住

它认五种证据：`A-byline` / `A-editorial` / `A-turns` / `A-masthead` / `A-copyright`。
**这五种全部是印刷出版机器的产物**——署名行、编者注、逐字稿轮次、刊头、版权页。
公元前五世纪的希腊一样都没有。

而更糟的是**它可能会「通过」**：现代译本的扉页会印 `GALEN ON THE NATURAL FACULTIES`，
`A-byline` 照样命中。**而 Kühn 版 22 卷里那些今天已知为伪托的篇目，
扉页署名与真作一模一样。** 于是这条判据在最需要它的地方**分辨力为零**。

> 「扉页上印着他的名字」证明的是**编者认为**这是他写的，
> 不是**证据表明**这是他写的。对古代人物，这两件事经常不是同一件事。

## 判据

`subject_origin == "historical"` 时，工作区 `meta.json` 必须声明 `attribution_basis`：

```json
"attribution_basis": {
  "authority": "Galen, De Libris Propriis（本人亲自编纂的真作目录，用以对抗伪托本）",
  "citation": "https://bmcr.brynmawr.edu/2014/2014.08.17/",
  "disputed_policy": "Kühn 版中现代学界判为伪托的篇目一律不计入 P1，逐条列于 disputed_works",
  "disputed_works": ["..."]
}
```

四个字段**缺一即错**。`disputed_works` 允许为空数组，**但 `disputed_policy` 必须写明为何为空**
——「没有争议篇目」与「我没查过争议篇目」在机器眼里长得一样，必须由人写下来区分。

非 historical 人物：本门**只报不判**（印刷时代的署名证据由 `check_authorship.py` 负责）。

## 这个判据的射程（必须一起说）

**它检查的是「有没有写下依据」，不是「依据成不成立」。**
一个人完全可以填一段假的 authority 骗过它。它挡的是**沉默**，不是**说谎**——
而沉默正是 Hippocrates 那一类的失败形态：没有人撒谎，只是没有人问过这个问题。

「依据成不成立」由人读 `authority` 与 `citation` 回答。**两者不可互相替代。**

退出码：0 = 通过；1 = 有问题；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

REQUIRED = ("authority", "citation", "disputed_policy", "disputed_works")

# 太短的声明等于没声明。阈值取得很低——**它挡的是空字符串与「N/A」，不是挡文笔。**
MIN_AUTHORITY = 12
MIN_POLICY = 12


def check_meta(meta: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """返回 (问题列表, 指标)。非 historical 人物不产生问题，只产生指标。"""
    origin = str(meta.get("subject_origin") or "").strip()
    info: dict[str, Any] = {"subject_origin": origin or "(未声明)"}
    if origin != "historical":
        info["状态"] = "非 historical，本门只报不判（署名证据归 check_authorship.py）"
        return [], info

    basis = meta.get("attribution_basis")
    if not isinstance(basis, dict):
        # ★ v0.0.0.30：措辞按时代分开。原文一律说「印刷时代的署名证据对他不适用」——
        #   那是照着 Hippocrates／Galen 写的，**对 1543 年的 Vesalius 是错的**：
        #   他有扉页、有具名印工、有版次。**门该拦他（historical 都要声明依据），
        #   但拦的理由不一样**：他要写的是「哪些版次算真、哪些托名件不算」，
        #   不是「在没有署名的时代靠什么认定」。
        #   一条对某一类人成立的说明文字，套到另一类人身上就是错的。
        return ([
            "historical 人物未声明 attribution_basis —— **必须写明靠什么证明这是他写的**。"
            "前印刷时代人物：A-byline 等五种署名证据结构上不存在，须另找权威（如作者自著目录）；"
            "印刷时代人物：扉页与印工可用，但**须写明哪些版次／托名件不算**"
        ], info)

    problems: list[str] = []
    for key in REQUIRED:
        if key not in basis:
            problems.append(f"attribution_basis 缺字段 `{key}`")
    if problems:
        return problems, info

    authority = str(basis.get("authority") or "").strip()
    citation = str(basis.get("citation") or "").strip()
    policy = str(basis.get("disputed_policy") or "").strip()
    disputed = basis.get("disputed_works")

    if len(authority) < MIN_AUTHORITY:
        problems.append(f"`authority` 过短（{len(authority)} 字符），等于没声明")
    if not citation:
        problems.append("`citation` 为空 —— 依据必须可查证，不能只是一句断言")
    if len(policy) < MIN_POLICY:
        problems.append(
            f"`disputed_policy` 过短（{len(policy)} 字符）—— "
            "**「没有争议篇目」与「我没查过」必须由人写下来区分**")
    if not isinstance(disputed, list):
        problems.append("`disputed_works` 必须是数组（可以为空数组，但不能缺）")

    info["authority"] = authority[:80]
    info["citation"] = citation[:80]
    info["争议篇目数"] = len(disputed) if isinstance(disputed, list) else "**格式错**"
    return problems, info


def check_sources(sources: list[dict[str, Any]], subject_surname: str) -> tuple[list[str], dict[str, Any]]:
    """P1 且声称本人所著的源，必须逐条挂 `attribution`（指向已声明的依据）。"""
    claimed, missing = 0, []
    for rec in sources:
        if rec.get("tier") != "P1":
            continue
        author = str(rec.get("author") or "")
        if subject_surname and subject_surname.lower() not in author.lower():
            continue
        claimed += 1
        if not str(rec.get("attribution") or "").strip():
            missing.append(str(rec.get("source_id") or "?"))
    info = {"P1 声称本人所著": claimed, "未挂 attribution": len(missing)}
    if not missing:
        return [], info
    return ([
        f"{len(missing)} 条 P1 源未挂 `attribution` 字段："
        f"{', '.join(missing[:8])}{' …' if len(missing) > 8 else ''}"
        " —— 每条声称是他写的源，都要说清是按哪一条依据认定的"
    ], info)


# ── 负对照 ────────────────────────────────────────────────────────────
def self_test() -> int:
    fails = []
    good = {
        "subject_origin": "historical",
        "attribution_basis": {
            "authority": "Galen, De Libris Propriis（本人亲自编纂的真作目录）",
            "citation": "https://bmcr.brynmawr.edu/2014/2014.08.17/",
            "disputed_policy": "Kühn 版中现代学界判为伪托的篇目一律不计入 P1",
            "disputed_works": ["De Historia Philosopha"],
        },
    }

    # 正对照 1：声明齐全 → 0 问题
    p, _ = check_meta(good)
    if p:
        fails.append(f"正对照 1 被误杀：声明齐全却报 {p}")

    # 正对照 2：非 historical → 本门不判
    p, i = check_meta({"subject_origin": "public"})
    if p or "只报不判" not in i.get("状态", ""):
        fails.append("正对照 2 失败：非 historical 人物不该被本门判错")

    # ★ 负对照 1（Hippocrates 那一类）：historical 而完全没声明
    #   断言只查**实质**（有没有报错、报的是不是「没声明依据」），不钉死措辞——
    #   v0.0.0.30 改措辞时这条曾因钉死短语而误红，那是判据脆而不是产物错。
    p, _ = check_meta({"subject_origin": "historical"})
    if not p or "attribution_basis" not in p[0]:
        fails.append("负对照 1 未抓出：historical 人物完全没声明归属依据")
    # 且措辞必须**同时覆盖两类时代**——这是 v0.0.0.30 的实质改动
    if p and not ("前印刷时代" in p[0] and "印刷时代人物" in p[0]):
        fails.append("负对照 1 措辞失职：未同时说明前印刷时代与印刷时代两类该写什么")

    # 负对照 2：四字段各缺其一，都要抓出
    for key in REQUIRED:
        bad = {"subject_origin": "historical",
               "attribution_basis": {k: v for k, v in good["attribution_basis"].items() if k != key}}
        p, _ = check_meta(bad)
        if not any(key in x for x in p):
            fails.append(f"负对照 2 未抓出：缺字段 `{key}`")

    # ★ 负对照 3：disputed_works 为空**且** policy 敷衍 → 必须抓出
    #   这一条是本门的核心——「没有争议」与「没查过」不许长得一样。
    bad = {"subject_origin": "historical",
           "attribution_basis": {**good["attribution_basis"],
                                 "disputed_works": [], "disputed_policy": "无"}}
    p, _ = check_meta(bad)
    if not any("没查过" in x for x in p):
        fails.append("负对照 3 未抓出：争议篇目为空而政策敷衍")

    # 正对照 3：disputed_works 为空但 policy 写清楚了 → 放行
    ok = {"subject_origin": "historical",
          "attribution_basis": {**good["attribution_basis"], "disputed_works": [],
                                "disputed_policy": "已逐篇比对现代校勘目录，本次所选篇目全部在真作之列，无争议篇目"}}
    p, _ = check_meta(ok)
    if p:
        fails.append(f"正对照 3 被误杀：空数组但政策写清楚了却报 {p}")

    # 负对照 4：citation 空字符串（**不是缺字段**，是填了空）
    bad = {"subject_origin": "historical",
           "attribution_basis": {**good["attribution_basis"], "citation": "  "}}
    p, _ = check_meta(bad)
    if not any("citation" in x for x in p):
        fails.append("负对照 4 未抓出：citation 填了空白")

    # 源层：正对照 —— 挂了 attribution 的 P1 不报
    p, _ = check_sources([{"tier": "P1", "author": "Galen", "source_id": "src-1",
                           "attribution": "De Libris Propriis"}], "Galen")
    if p:
        fails.append("源层正对照被误杀：已挂 attribution 的 P1")

    # ★ 源层负对照 —— 这一条对应 Kühn 版伪托篇目：署名与真作一模一样
    p, _ = check_sources([{"tier": "P1", "author": "Galen", "source_id": "src-2"}], "Galen")
    if not p:
        fails.append("源层负对照未抓出：P1 声称本人所著却没说按什么认定的")

    # 源层边界：账本明说是别人写的 → 不在射程内，不许误伤
    p, _ = check_sources([{"tier": "P1", "author": "Polybus", "source_id": "src-3"}], "Galen")
    if p:
        fails.append("源层边界失败：账本已明说是他人所著，本门不该管")

    # ══ ★★★★ 2026-08-07：**姓要取最后一段，不是第一段** ══
    #   `main()` 原先写 `str(meta.get("name")).split()[0]`——`Joseph Whitworth` → `Joseph`。
    #   与 `check_authorship` 文件头记过的那个坑一模一样
    #   （`Justus von Liebig` → surname='Justus' → 归属 1/30）。**同一个错在另一个文件里又长了一遍。**
    for _full, _want in (("Joseph Whitworth", "Whitworth"),
                         ("Justus von Liebig", "Liebig"),
                         ("Charles L. Coffin", "Coffin"),
                         ("Galen", "Galen")):
        _got = [t for t in _full.split() if t][-1]
        if _got != _want:
            fails.append(f"姓取错：{_full!r} → {_got!r}，应为 {_want!r}")
    #   ★ 反向：按**名**匹配会把别人的东西收进来。
    p, _ = check_sources([{"tier": "P1", "author": "Joseph Priestley", "source_id": "src-x"}],
                         "Whitworth")
    if p:
        fails.append("按姓匹配失败：`Joseph Priestley` 不该被 `Whitworth` 收进来")
    p, _ = check_sources([{"tier": "P1", "author": "Joseph Priestley", "source_id": "src-x"}],
                         "Joseph")   # ← 这就是修之前的口径
    if not p:
        fails.append("★ 反证不成立：按名 `Joseph` 匹配本该把 Priestley 收进来（用来说明旧口径为何错）")

    # ══ ★★★★ **它读的那个文件此前一直是空脚手架** ══
    #   `main()` 原先读 `research/source-universe.json`——那是 `init_target` 生成的
    #   覆盖轴脚手架（只有 `coverage_axes` 之类）。
    #   **归档 26 个工作区实测：有来源的 0 份、空的 26 份。**
    #   于是 `rows=[]` → `claimed=0`、`missing=[]` → 永远报「未挂 attribution: 0」。
    #   **1174 份 P1 声称本人所著，一份都没被这道检查看过。**
    #   修成读 `evidence/source-ledger.jsonl` 之后，实测 **231 份未挂 attribution**
    #   （Godin 196、Steinhardt 28、Semmelweis 7；其余 23 个工作区是 0）——
    #   那三个人物的 `attribution` **键根本不存在**，它们早于该字段被加进 `ingest.py`。
    print("── ★★★★ 源层：读到 0 行必须说「未核」，不许当成「都挂好了」 ──")
    _sc = {"coverage_axes": ["identity", "role", "period"]}      # 逐字就是那个脚手架的形状
    _rows = _sc if isinstance(_sc, list) else _sc.get("sources", [])
    if _rows:
        fails.append("脚手架样本不该解析出来源")
    _p, _i = check_sources(_rows, "Whitworth")
    if _p or _i.get("P1 声称本人所著") != 0:
        fails.append("空来源时不该报问题（问题在于**别把这个 0 当成通过**）")
    print(f"  ✓ 空来源 → 问题 {len(_p)} 条、claimed {_i.get('P1 声称本人所著')}"
          f"　★ **所以 main() 必须把「读了哪个文件、几行」打出来**，否则这个 0 无法判读")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：historical 无声明被抓出，四字段各缺其一全抓出，"
          "**「争议为空」与「没查过」被分开**，citation 填空白被抓出；"
          "非 historical 未被误判，账本明说他人所著的源未被误伤")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="归属依据门：印刷时代之前的人物靠什么证明这是他写的")
    ap.add_argument("target", nargs="?", type=pathlib.Path, help="工作区目录")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.target:
        print("用法错误：需要工作区路径（或 --self-test）", file=sys.stderr)
        return 3
    meta_path = a.target / "meta.json"
    if not meta_path.is_file():
        print(f"用法错误：{meta_path} 不存在", file=sys.stderr)
        return 3

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    problems, info = check_meta(meta)

    # ★★★★ 2026-08-07：**这一段此前从来没有检查过任何一份来源，对任何人，一次都没有。**
    #   两个 bug 叠在一起：
    #
    #   ① **读错了文件。** 原先读 `research/source-universe.json`——那是 `init_target`
    #      生成的**覆盖轴脚手架**，里面只有 `coverage_axes` 之类，
    #      **归档 26 个工作区里「有来源的 0 份、空的 26 份」**。
    #      真台账在 `evidence/source-ledger.jsonl`。
    #      于是 `rows=[]` → `claimed=0`、`missing=[]` → **永远报「未挂 attribution: 0」**。
    #      [[empty-default-swallows-unknown]]：`0` 被读成「都挂好了」。
    #
    #   ② **姓取成了名。** `str(meta.get("name")).split()[0]` ——
    #      `Joseph Whitworth` → `Joseph`。这与 `check_authorship` 文件头记过的那个坑
    #      **一模一样**（`Justus von Liebig` → surname='Justus' → 归属 1/30），
    #      **同一个 `split()[0]` 在另一个文件里又长了一遍**。
    #
    #   ★ 修完必须把**读了哪个文件、读到几行**打出来——否则下次「0」还是分不清
    #     「都挂好了」与「一份都没读到」。
    _led_new = a.target / "evidence" / "source-ledger.jsonl"
    _led_old = a.target / "research" / "source-universe.json"
    rows, _src = [], None
    if _led_new.is_file():
        rows = [json.loads(l) for l in _led_new.read_text(encoding="utf-8").splitlines()
                if l.strip()]
        _src = "evidence/source-ledger.jsonl"
    elif _led_old.is_file():
        data = json.loads(_led_old.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else data.get("sources", [])
        _src = "research/source-universe.json（旧口径）"
    if _src is None:
        info["★ 来源层未核（不是通过）"] = "两个台账路径都不存在"
    else:
        # ★★★ 2026-08-11：**不再在这里自己推姓**，改为复用 `check_authorship.build_patterns`。
        #   本文件头部记着「`split()[0]` 在另一个文件里又长了一遍」——
        #   而这次是**世代后缀**：`Oliver Wendell Holmes Jr.` 取最后一段得 **`Jr.`**，
        #   于是 `check_sources` 会拿 `jr.` 去匹配 author 字段，**一份都对不上**。
        #   （同一个病根的第三次：`split()[0]` → `[-1]` → 后缀。**复制一份逻辑就会再长一遍**，
        #   所以这次直接借同一把尺子，不再维护第二份。）
        surname = ""
        _nm = str(meta.get("name") or "").strip()
        if _nm:
            try:
                import importlib.util as _ilu
                _sp = _ilu.spec_from_file_location(
                    "_pd_ca_ab", pathlib.Path(__file__).resolve().parent / "check_authorship.py")
                _m = _ilu.module_from_spec(_sp)
                _sp.loader.exec_module(_m)
                surname = _m.build_patterns(_nm)["surname"]
            except Exception as _e:                                  # noqa: BLE001
                # ★ 借不到就**说出来**，不要静默退回旧算法
                info["★ 姓氏推导降级（不是通过）"] = (
                    "借不到 check_authorship.build_patterns（%s），"
                    "退回「取最后一段」——**对带 Jr./Sr./II 的人名会取错**" % _e)
                _tok = [x for x in _nm.split() if x]
                surname = _tok[-1] if _tok else ""
        sp, si = check_sources(rows, surname)
        problems += sp
        info.update(si)
        info["来源层读的是"] = f"{_src}，{len(rows)} 行；按姓 `{surname}` 匹配"
        if not rows:
            info["★ 来源层读到 0 行（不是通过）"] = _src

    if a.json:
        print(json.dumps({"problems": problems, "metrics": info}, ensure_ascii=False, indent=1))
        return 1 if problems else 0
    if not problems:
        print("✓ 归属依据完备：", json.dumps(info, ensure_ascii=False))
        return 0
    print(f"\n✗ 归属依据 {len(problems)} 条问题：\n")
    for x in problems:
        print(f"  - {x}")
    print("\n  ↑ **印刷时代的署名证据对古代人物不适用。**"
          "扉页印着他的名字，证明的是编者这么认为，不是证据这么表明。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
