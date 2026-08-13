#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_queue_reflects_reality.py —— **队列有没有把已经结案的人排回去**

## 为什么有这件（同一个病已经犯两次）

| 时间 | 形态 | 后果 |
|---|---|---|
| 2026-08-13 排第 2 批 | Socrates／Confucius／Solon **归属分析早做完了，没喂回队列** | 三人还排在前 8、还是绿灯 |
| 2026-08-13 排第 3 批 | Sloan 刚记延后、Michelangelo 阶段 4 早做完 | 两人排在**第 1、2 位** |

第二次不是漏写，是**写了但名字形式不同**：

    Sloan         延后名单 `Alfred P. Sloan`      ／ 队列 `Alfred Sloan`
    Michelangelo  工作区 meta.json `Michelangelo Buonarroti` ／ 队列 `Michelangelo`

★ 而 `next_person.py` **故意不做名字推断**（注释里写着理由：按词元包含去猜会把
`Charles Coffin` 与 GE 总裁 `Charles A. Coffin` 认成同一个人）。
所以正确的修法是**补 `aliases`**，不是放宽匹配——
但没有任何东西会告诉你「该补 alias 了」。**这件就是那个提醒。**

## 判什么

拿 `next_person.py --show 999` 的 `upcoming`（＝还会被派工的人），逐个问两件：

1. **他是不是已经在延后名单里**（按名字或名单里的 `aliases` 比）？
2. **他是不是已经有工作区**（`_corpora/wip-*/workspaces/*/`，按 slug／meta.json 的
   `name`／`normalized_name`／`aliases` 比）？

任一为真 ⇒ **队列该认出他而没认出**，报出来并给出**该往哪儿补哪个 alias**。

★ 本件**只报不改**：补 alias 是往台账里写数据，要人看一眼再写。

★★ 它**不**判「这个人该不该做」——那是 `worth_starting` 的事。
   本件只问一件：**已经落纸的结论，工具认不认得。**

## 用法

    python3 check_queue_reflects_reality.py
    python3 check_queue_reflects_reality.py --self-test

退出码：0＝队列与结论一致；1＝有认不出的；4＝跑不了 next_person（**未判**）
"""
import argparse
import glob
import json
import os
import pathlib
import re
import subprocess
import sys
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
LEDGERS = HERE.parent
CORPORA = LEDGERS.parent / "_corpora"
DEFER = LEDGERS / "_延后名单.json"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    return re.sub(r"[^a-z0-9]", "", s)


def deferred_keys():
    """→ {归一名: 名单里那一条的 name}。**只认显式写下的 name 与 aliases。**"""
    out = {}
    if not DEFER.is_file():
        return out
    for item in json.loads(DEFER.read_text(encoding="utf-8")).get("deferred", []):
        nm = item.get("name", "")
        for k in [nm] + list(item.get("aliases") or []):
            if k:
                out[norm(k)] = nm
    return out


def worked_keys():
    """→ {归一名: 工作区路径}。slug ＋ meta.json 声明的 name/normalized_name/aliases。"""
    out = {}
    for ws in glob.glob(str(CORPORA / "wip-*" / "workspaces" / "*")):
        if not os.path.isdir(ws):
            continue
        out[norm(os.path.basename(ws))] = ws
        mj = os.path.join(ws, "meta.json")
        if os.path.isfile(mj):
            try:
                md = json.load(open(mj, encoding="utf-8"))
            except Exception:                                    # noqa: BLE001
                continue
            for k in ("name", "normalized_name", "slug"):
                if md.get(k):
                    out[norm(md[k])] = ws
            for al in (md.get("aliases") or []):
                out[norm(al)] = ws
    return out


def upcoming():
    r = subprocess.run([sys.executable, str(HERE / "next_person.py"), "--show", "999"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, f"next_person.py rc={r.returncode}：{(r.stderr or '')[:200]}"
    try:
        return json.loads(r.stdout).get("upcoming", []), ""
    except ValueError as e:
        return None, f"输出不是 JSON：{e}"


def tokens(s: str) -> set:
    """姓名 → 词元集合（丢掉单字母中间名，`Alfred P. Sloan` → {alfred, sloan}）。"""
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    return {w for w in re.split(r"[^a-z0-9]+", s) if len(w) > 1}


# 名单/工作区那一侧的键是**归一串**，这里要按词元比，所以另存一份词元。
_TOKS = {}


def _kin(toks: set, key: str) -> bool:
    """两个名字的词元集合互为子集 ⇒ 疑似同一人（**只作提示，不据此判定**）。"""
    other = _TOKS.get(key)
    if not other or not toks:
        return False
    return toks <= other or other <= toks


def evaluate(up, defer, worked):
    # 每次 evaluate 重建词元表，**不留跨调用的状态**（自测要能独立跑两次）
    _TOKS.clear()
    for kk, v in list(defer.items()):
        _TOKS[kk] = tokens(v if isinstance(v, str) else kk)
    for kk, v in list(worked.items()):
        _TOKS.setdefault(kk, tokens(os.path.basename(str(v)).replace("-", " ")))
    """★ 纯函数，好让自测不依赖磁盘。"""
    bad = []
    for p in up:
        nm = p.get("name") if isinstance(p, dict) else str(p)
        k = norm(nm)
        if k in defer:
            bad.append({"name": nm, "为什么": "**已在延后名单里**",
                        "名单里叫": defer[k], "怎么修": "队列名与名单名不同 ⇒ 已能认出（本条不该报）"})
        elif k in worked:
            bad.append({"name": nm, "为什么": "**已经有工作区**",
                        "工作区": os.path.basename(worked[k]), "怎么修": "已能认出（本条不该报）"})
        else:
            # 认不出——找找「像是同一个人」的候选，**只作提示**。
            # ★ 用**词元子集**，不用子串：`Alfred Sloan` 与 `Alfred P. Sloan`
            #   归一成 alfredsloan / alfredpsloan，**互不包含**（中间多个 p），
            #   子串法一条都找不到。第一版就栽在这儿，自测当场抓到。
            toks = tokens(nm)
            cands = [v for kk, v in defer.items() if _kin(toks, kk)][:2]
            cands += [os.path.basename(v) for kk, v in worked.items() if _kin(toks, kk)][:2]
            if cands:
                bad.append({"name": nm, "为什么": "★★ **队列仍在派工，而它看起来已经结案**",
                            "疑似对应": cands,
                            "怎么修": "往 `_延后名单.json` 那一条或工作区 `meta.json` 的 "
                                    "`aliases` 里加上队列用的写法 —— **加数据，不放宽匹配**"})
    return bad


def self_test() -> int:
    """★ 反例逐字取自 2026-08-13 真实撞到的两条。"""
    up = [{"name": "Alfred Sloan"}, {"name": "Michelangelo"}, {"name": "Winston Churchill"}]
    # 修之前：名单写全名、工作区写全名，队列写简名 ⇒ 两条都该报
    d0 = {norm("Alfred P. Sloan"): "Alfred P. Sloan"}
    w0 = {norm("Michelangelo Buonarroti"): "/x/michelangelo-buonarroti"}
    r0 = evaluate(up, d0, w0)
    ok1 = len(r0) == 2 and {x["name"] for x in r0} == {"Alfred Sloan", "Michelangelo"}
    print(f"  {'✓' if ok1 else '✗'} 修之前：Sloan 与 Michelangelo 两条都必须报出"
          f"（实得 {[x['name'] for x in r0]}）")
    # 修之后：补了 alias ⇒ 一条都不该报
    d1 = dict(d0); d1[norm("Alfred Sloan")] = "Alfred P. Sloan"
    w1 = dict(w0); w1[norm("Michelangelo")] = "/x/michelangelo-buonarroti"
    r1 = [x for x in evaluate(up, d1, w1) if "不该报" not in x.get("怎么修", "")]
    ok2 = len(r1) == 0
    print(f"  {'✓' if ok2 else '✗'} 补 alias 之后：一条都不该报（实得 {len(r1)}）")
    # ★ 反方向：真正没结案的人**不许**被报
    ok3 = all(x["name"] != "Winston Churchill" for x in r0)
    print(f"  {'✓' if ok3 else '✗'} 没结案的 Churchill **不许**被报——"
          "防止它其实是在报「名字长得像」")
    bad = 3 - sum([ok1, ok2, ok3])
    print(f"\n{'✓ 正负对照全过' if bad == 0 else f'✗ {bad} 项不符'}"
          "（反例逐字取自 2026-08-13 真实撞到的两条）")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    up, why = upcoming()
    if up is None:
        print(f"★★ **未判，不是通过**：{why}")
        return 4
    bad = [x for x in evaluate(up, deferred_keys(), worked_keys())
           if "不该报" not in x.get("怎么修", "")]
    if a.json:
        print(json.dumps({"upcoming": len(up), "认不出的": len(bad), "逐条": bad},
                         ensure_ascii=False, indent=1))
        return 1 if bad else 0
    print(f"队列还会派工的 {len(up)} 人")
    if bad:
        print(f"\n✗ **{len(bad)} 人已经结案，而队列还在派工**：")
        for x in bad:
            print(f"  · {x['name']}　{x['为什么']}")
            print(f"      疑似对应：{x.get('疑似对应')}")
            print(f"      怎么修：{x['怎么修']}")
    else:
        print("\n✓ 队列里没有已结案的人")
    print("\n★ 射程：只比**显式写下的**名字与 aliases，**不做名字推断**"
          "（按词元包含去猜会把 `Charles Coffin` 与 `Charles A. Coffin` 认成一个人）。"
          "疑似对应那一栏只作提示，**要人看一眼再补**。")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
