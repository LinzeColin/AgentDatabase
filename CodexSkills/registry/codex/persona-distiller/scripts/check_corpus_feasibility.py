#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**手上这批材料，还有没有可能走完全程？** —— 在研究阶段就把「结构上不可能」判出来。

## 撞出它的那一次（2026-08-10，Shewhart #165）

Shewhart 一手 8 份，`quick` 的 `min_sources` 正好是 8。研究门于是**绿了**。
但 `quality_check` 的两条规则合起来是矛盾的：

- L132：`len(usable) >= min_sources`，而 `usable` **只含 `split == 'train'`**；
- L149：`phase in {synthesis, release}` 且没有 holdout → `source.no-holdout` **报错**。

→ 留 0 份 holdout：研究门过，合成门必错；
   留 1 份 holdout：train 掉到 7 < 8，**三个阶段全错**。
**8 份在结构上无解，而文档里写的下限是 8。真实下限是 9。**

★★ **代价不是「多跑一次门」**：研究门绿了，人就会去写六道研究、几十条断言、
十份产物、一整套用例，**全部做完之后**才在合成门上撞见 `source.no-holdout`，
然后发现无论怎么改都过不去——因为要补的是**材料**，不是文字。
本判据把这一撞提前到抓源刚结束的时候。

## 它判什么

穷举「拿哪一份当 holdout」（至少 1 份），看**有没有任何一种选法**能同时满足
`min_sources` / `min_lanes` / `min_primary_ratio`。

- **有** → `feasible`（现在不一定过，但补文字就能过）
- **没有，且再补材料能救** → `needs-more-material`，并算出**至少还差几份**
- **没有，且补材料也救不了** → 目前只有一种：可用材料总数本身就 < 门+1

★ 为什么要穷举而不是随便扣一份：某一道可能只有 1 份材料撑着，
**恰好把那一份扣成 holdout，道数就掉了**——但换一份扣就没事。
只试一种选法会把「能过的人」误判成「不可能」。

## 它不判什么

- **不判材料好不好**：声口、归属、OCR 质量一概不看，那是别的门的事。
- **不替人决定要不要放弃**：它只给「结构上可不可能」，
  以及「还差几份」——**要不要去补，是人的事**。
- **`min_lanes` 的上限取自台账里已出现过的道**：判据不知道某份材料
  「其实也能算 timeline」。所以它给的是**当前标注下**的结论，
  重新标注属于人的判断，不属于判据。

退出码：0 = 可行；1 = 不可行（含还差几份）；2 = 自测未过；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
try:
    from common import LANES, PROFILE_THRESHOLDS
except Exception:                                             # pragma: no cover
    LANES = ('writings', 'conversations', 'expression', 'external', 'decisions', 'timeline')
    PROFILE_THRESHOLDS = {'quick': {'min_sources': 8, 'min_lanes': 3, 'min_primary_ratio': 0.40}}


def _usable(rows: list[dict]) -> list[dict]:
    """能计进门的行：非 U 档、抽取没失败。**与 quality_check L113 同一口径。**"""
    return [r for r in rows
            if r.get('tier') != 'U' and r.get('extraction_status') != 'failed']


def _meets(train: list[dict], th: dict) -> tuple[bool, list[str]]:
    n = len(train)
    primary = [r for r in train if r.get('tier') in {'P1', 'P2'}]
    ratio = len(primary) / n if n else 0.0
    lanes = {l for r in train for l in set(r.get('dimensions') or []) if l in LANES}
    bad = []
    if n < th['min_sources']:
        bad.append(f"train {n} < min_sources {th['min_sources']}")
    if len(lanes) < th['min_lanes']:
        bad.append(f"道数 {len(lanes)} < min_lanes {th['min_lanes']}（{sorted(lanes)}）")
    if ratio < th['min_primary_ratio']:
        bad.append(f"一手占比 {ratio:.1%} < {th['min_primary_ratio']:.0%}")
    return (not bad), bad


def feasibility(rows: list[dict], profile: str = 'quick') -> dict:
    """→ {'可行': bool, '结论': str, '还差': int|None, '最优选法': ..., '拦路的': [...]}"""
    th = PROFILE_THRESHOLDS.get(profile) or PROFILE_THRESHOLDS['quick']
    usable = _usable(rows)
    N = len(usable)
    out = {
        'profile': profile,
        '可用材料总数': N,
        'min_sources': th['min_sources'],
        'min_lanes': th['min_lanes'],
        'min_primary_ratio': th['min_primary_ratio'],
        '★ 真实下限': th['min_sources'] + 1,
        '★ 口径': ('`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，'
                   'holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，'
                   '而文档写的是 min_sources**。'),
    }

    # ① 总数就不够 → 结构上不可能，且能算出还差几份
    if N < th['min_sources'] + 1:
        out.update({
            '可行': False,
            '结论': 'impossible-without-more-material',
            '还差': th['min_sources'] + 1 - N,
            '拦路的': [f"可用材料总数 {N} < **真实下限 {th['min_sources'] + 1}**"
                       f"（{th['min_sources']} 份 train + 至少 1 份 holdout）"],
        })
        return out

    # ② 穷举扣哪一份当 holdout —— ★ 只试一种选法会误判
    ok_any, best_bad, ok_pick = False, None, None
    for i in range(N):
        train = usable[:i] + usable[i + 1:]
        ok, bad = _meets(train, th)
        if ok:
            ok_any, ok_pick = True, (usable[i].get('source_id') or f'#{i}')
            break
        if best_bad is None or len(bad) < len(best_bad):
            best_bad = bad
    if ok_any:
        out.update({'可行': True, '结论': 'feasible', '还差': 0,
                    '最优选法': f'把 {ok_pick} 扣作 holdout 即满足三项门',
                    '拦路的': []})
        return out

    out.update({'可行': False, '结论': 'needs-more-material', '还差': None,
                '拦路的': best_bad or ['未知'],
                '★ 说明': '**扣任何一份当 holdout 都过不了**——差的是材料，不是文字。'})
    return out


def evaluate(target: pathlib.Path, profile: str | None = None) -> tuple[list[str], dict]:
    led = target / 'evidence' / 'source-ledger.jsonl'
    if not led.is_file():
        return [], {'状态': f'没有 {led}，**未核验**（不是通过）'}
    rows = [json.loads(l) for l in led.read_text(encoding='utf-8').splitlines() if l.strip()]
    if profile is None:
        meta = target / 'meta.json'
        profile = 'quick'
        if meta.is_file():
            try:
                profile = json.loads(meta.read_text(encoding='utf-8')).get('profile') or 'quick'
            except Exception:
                pass
    info = feasibility(rows, profile)
    problems = []
    if not info['可行']:
        head = ('**这批材料在结构上走不完全程**' if info['结论'] == 'impossible-without-more-material'
                else '**扣任何一份当 holdout 都满足不了 profile 门**')
        tail = (f"——**至少还要 {info['还差']} 份**才有可能" if info.get('还差') else '——差的是材料，不是文字')
        problems.append(f"{head}：{'；'.join(info['拦路的'])}{tail}")
    return problems, info


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(('  ✓ ' if cond else '  ✗ ') + msg)

    def S(i, tier='P1', dims=('writings',), **kw):
        return {'source_id': f'src-{i:04d}', 'tier': tier, 'dimensions': list(dims), **kw}

    TH = PROFILE_THRESHOLDS['quick']            # 8 / 3 / 0.40

    # ① 9 份、3 道 → 可行（扣 1 份还剩 8）
    rows = [S(i, dims=('writings',)) for i in range(6)] + \
           [S(6, dims=('decisions',)), S(7, dims=('timeline',)), S(8, dims=('external',))]
    r = feasibility(rows)
    chk('① 9 份 3+ 道 → 可行', r['可行'] and r['结论'] == 'feasible')

    # ② ★ Shewhart 真实局面：8 份、2 道 → 不可行，且**还差 1 份**
    rows = [S(i, dims=('writings',)) for i in range(5)] + [S(i, dims=('decisions',)) for i in range(5, 8)]
    r = feasibility(rows)
    chk('② **8 份（= min_sources）→ 不可行，还差 1 份**（真实下限是 9）',
        (not r['可行']) and r['结论'] == 'impossible-without-more-material' and r['还差'] == 1)

    # ③ ★★ 只试一种选法会误判：第 3 道只有 1 份材料撑着
    rows = ([S(i, dims=('writings',)) for i in range(7)]
            + [S(7, dims=('decisions',)), S(8, dims=('timeline',))])
    #   扣掉 src-0008 → 只剩 2 道，不合格；但扣掉 src-0000 → 8 份 3 道，合格
    r = feasibility(rows)
    chk('③ **第 3 道只有 1 份撑着 → 换一份扣就行，必须判「可行」**（只试一种选法会误判死）',
        r['可行'])

    # ④ 9 份里有 1 份是 U 档 → 可用只剩 8 → 不可行
    rows = [S(i, dims=('writings',)) for i in range(6)] + \
           [S(6, dims=('decisions',)), S(7, dims=('timeline',)), S(8, tier='U', dims=('external',))]
    r = feasibility(rows)
    chk('④ 9 份里 1 份 U 档 → 可用 8 → 不可行（口径与 quality_check L113 一致）',
        (not r['可行']) and r['可用材料总数'] == 8)

    # ⑤ 份数道数都够，但一手占比不够 → needs-more-material（不是 impossible）
    rows = [S(i, tier='S1', dims=('writings',)) for i in range(6)] + \
           [S(6, tier='P1', dims=('decisions',)), S(7, tier='P1', dims=('timeline',)),
            S(8, tier='P1', dims=('external',))]
    r = feasibility(rows)                                    # 扣 1 后最好 3/8 = 37.5% < 40%
    chk('⑤ 一手占比不够 → 归 needs-more-material，**不归 impossible**',
        (not r['可行']) and r['结论'] == 'needs-more-material')

    # ⑥ ★ 正例必须真绿：10 份、3 道均匀、全 P1
    rows = [S(i, dims=('writings',)) for i in range(4)] + \
           [S(i, dims=('decisions',)) for i in range(4, 7)] + \
           [S(i, dims=('timeline',)) for i in range(7, 10)]
    r = feasibility(rows)
    chk('⑥ **正例：10 份 3 道全 P1 → 必须判可行**（反例红了可能是红得凑巧）', r['可行'])

    # ⑦ ★ 边界：9 份、3 道、全 P1 —— 恰好等于真实下限，必须绿
    rows = [S(i, dims=('writings',)) for i in range(5)] + \
           [S(i, dims=('decisions',)) for i in range(5, 7)] + \
           [S(i, dims=('timeline',)) for i in range(7, 9)]
    r = feasibility(rows)
    chk('⑦ **恰好 9 份（= 真实下限）→ 必须判可行**（差一份就是 ②，两边都要对）',
        r['可行'] and len(rows) == TH['min_sources'] + 1)

    # ⑧ 空台账 → 不可行且还差 9，不能报「通过」
    r = feasibility([])
    chk('⑧ 空台账 → 不可行、还差 9（**空不等于通过**）',
        (not r['可行']) and r['还差'] == TH['min_sources'] + 1)

    # ⑨ deep 档：下限应是 46 而不是 45
    r = feasibility([S(i) for i in range(45)], profile='deep')
    chk('⑨ deep 45 份 → 不可行（真实下限 46）',
        (not r['可行']) and r['★ 真实下限'] == 46)

    print('\n' + ('✓ 自测全过' if ok else '✗ 自测未过'))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('workspace', nargs='?')
    ap.add_argument('--profile', choices=sorted(PROFILE_THRESHOLDS))
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace:
        ap.error('要么 --self-test，要么给 workspace')
    problems, info = evaluate(pathlib.Path(a.workspace), a.profile)
    if a.json:
        print(json.dumps({'problems': problems, 'info': info}, ensure_ascii=False, indent=2))
    else:
        print(f"{pathlib.Path(a.workspace).name}｜profile {info.get('profile')}"
              f"｜可用 {info.get('可用材料总数')}"
              f"｜**真实下限 {info.get('★ 真实下限')}**（文档写的是 {info.get('min_sources')}）")
        if not problems:
            print(f"  ✓ 可行 —— {info.get('最优选法')}")
        for p in problems:
            print('  ✗ ' + p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
