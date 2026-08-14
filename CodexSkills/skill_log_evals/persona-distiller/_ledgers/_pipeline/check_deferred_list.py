#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""延后名单的守卫 —— **名单自己声称有这件判据，实际不存在。**

2026-08-14 实测：`_延后名单.json` 的 `★ total 口径` 里写着

> 已落成判据 `check_deferred_list.py` 每次现算

而 `_ledgers/_pipeline/` 下**没有这个文件**（全仓 find 也没有）。
`total` 眼下恰好对（185 = 185 条），但那是靠人手数对的，不是靠执行 ——
同一段说明里记着它已经漂过两次（写 31 实 33、写 168 实 187，差 19）。
**注释声称的守卫不是守卫。** [[a-comment-claiming-a-guard-is-not-a-guard]]

查四件：
  ① `total` == 条目数（**不许手写**）
  ② 没有重名（同一人记两次，两条理由会互相矛盾）
  ③ 处置键**分两档**：
       硬错 —— 一个处置键都没有（`处置类`/class/reason_class/defer_class/disposition 全无）
       计数 —— 只是没镜像成 `处置类`
     ★ schema 说明写「`处置类` 是四种历史键名的**规范镜像**……按 `处置类` 计数不会漏」，
       **实测覆盖 90/185 = 48.6%，漏 95 条**（88 条只有 class+disposition）。
       这一档只报数不判错：回填 95 条是动存量，㊸ 已裁存量不动，
       合成一档会让这道门**永远绿不了**。[[a-red-that-can-never-turn-green-is-not-a-signal]]
  ④ 名单里的人不该同时出现在已出货 registry 里

用法
----
    python3 check_deferred_list.py --self-test
    python3 check_deferred_list.py [--ledger <_延后名单.json>] [--registry <team-index.json>]
"""
import argparse
import collections
import json
import pathlib
import re
import sys

DEFAULT_LEDGER = "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_延后名单.json"
DEFAULT_REGISTRY = "CodexSkills/registry/codex/persona-distiller-group/team-index.json"


def key(name):
    """跨中英/连字符/缩写点可比 —— 台账与 registry 的写法不一致是常态
    （`William Paton` vs `William Andrew Paton`、`Alfred Sloan` vs `Alfred P. Sloan`）。"""
    return re.sub(r"[^a-z0-9]", "", str(name or "").lower())


def check(ledger_path, registry_path=None):
    errs = []
    d = json.loads(pathlib.Path(ledger_path).read_text(encoding="utf-8"))
    items = d.get("deferred") or []
    n = len(items)

    # ① total
    total = d.get("total")
    if total != n:
        errs.append("total 写着 %r，实际 %d 条 —— **total 不许手写**" % (total, n))

    # ② 重名
    dup = {k: v for k, v in collections.Counter(key(i.get("name")) for i in items).items() if v > 1}
    if dup:
        names = [i.get("name") for i in items if key(i.get("name")) in dup]
        errs.append("重名 %d 组：%s" % (len(dup), sorted(set(names))[:6]))

    # ③ 必填 —— 分两档，**不许合成一档**
    #    硬错：一个处置键都没有（真缺口，7 条）
    #    计数：只是没镜像成 `处置类`（95 条）——回填是动存量，㊸ 已裁存量不动，
    #          合成一档会让这道门**永远绿不了**。[[a-red-that-can-never-turn-green-is-not-a-signal]]
    ORIG_KEYS = ("class", "reason_class", "defer_class", "disposition")
    miss_name = [i for i in items if not i.get("name")]
    no_mirror = [i.get("name") for i in items if not i.get("处置类")]
    no_any = [i.get("name") for i in items
              if not i.get("处置类") and not any(i.get(k) for k in ORIG_KEYS)]
    if miss_name:
        errs.append("%d 条没有 name" % len(miss_name))
    if no_any:
        errs.append("%d 条**一个处置键都没有**（`处置类`/class/reason_class/defer_class/disposition 全无）：%s"
                    % (len(no_any), no_any[:6]))
    mirror_cov = n - len(no_mirror)
    pct = (mirror_cov / n * 100) if n else 0.0
    if no_mirror:
        # ★ 只在真的有漏的时候才印解释语。第一版无论如何都印「它们只有 class/disposition
        #   等原键」，补齐到 0 之后那句话指着一个空集合说话。**报数的话要跟着数变。**
        print("  ★ `处置类` 覆盖 %d/%d = %.1f%% —— schema 说明写「按 `处置类` 计数不会漏」，"
              "**实测漏 %d 条**（它们只有 class/disposition 等原键）。"
              % (mirror_cov, n, pct, len(no_mirror)))
    else:
        print("  ★ `处置类` 覆盖 %d/%d = %.1f%% —— schema 说明那句「按 `处置类` 计数不会漏」"
              "**现在才成立**（2026-08-15 补齐前是 90/185 = 48.6%%）。" % (mirror_cov, n, pct))

    # ④ 与已出货 registry 的交集
    overlap = []
    if registry_path and pathlib.Path(registry_path).exists():
        prods = json.loads(pathlib.Path(registry_path).read_text(encoding="utf-8")).get("products") or []
        shipped = {}
        for p in prods:
            for f in ("canonical_name", "subject_slug"):
                if p.get(f):
                    shipped[key(p[f])] = p.get("canonical_name")
        for i in items:
            k = key(i.get("name"))
            if k and k in shipped:
                overlap.append((i.get("name"), shipped[k]))
        if overlap:
            errs.append("%d 人**既在延后名单又在已出货 registry**：%s"
                        % (len(overlap), overlap[:5]))

    print("  条目 %d｜total %r｜重名 %d 组｜缺 name %d｜**一个处置键都没有 %d**｜与 registry 重叠 %d"
          % (n, total, len(dup), len(miss_name), len(no_any), len(overlap)))
    for e in errs:
        print("  ✗ %s" % e)
    print("  ⇒ %s" % ("通过" if not errs else "**%d 项不通过**" % len(errs)))
    return 1 if errs else 0


def selftest():
    import tempfile
    bad = 0
    cases = [
        ({"total": 2, "deferred": [{"name": "A", "处置类": "延后"}, {"name": "B", "处置类": "延后"}]}, 0, "全对"),
        ({"total": 3, "deferred": [{"name": "A", "处置类": "延后"}]}, 1, "total 手写漂了"),
        ({"total": 2, "deferred": [{"name": "A", "处置类": "延后"}, {"name": "a-", "处置类": "延后"}]}, 1, "重名（归一后同）"),
        ({"total": 1, "deferred": [{"name": "A"}]}, 1, "一个处置键都没有"),
        ({"total": 1, "deferred": [{"name": "A", "class": "延后"}]}, 0, "只有原键、没镜像 → 不判错，只计数"),
    ]
    with tempfile.TemporaryDirectory() as td:
        for j, want, label in cases:
            p = pathlib.Path(td) / "x.json"
            p.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
            got = check(str(p))
            if got != want:
                print("  ✗ %s：期望 rc=%d 得 %d" % (label, want, got))
                bad += 1
    print("自测 %d/%d" % (len(cases) - bad, len(cases)))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--registry", default=DEFAULT_REGISTRY)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    return check(a.ledger, a.registry)


if __name__ == "__main__":
    sys.exit(main())
