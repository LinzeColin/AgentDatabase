#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两席盲判 → 真 delta。★ 算法在看到分数之前写定，看到之后不许改。"""
import json, pathlib, sys, collections
WS = pathlib.Path("workspaces/william-osler/william-osler")
SP = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "round1")
KEY = json.loads((pathlib.Path("round1") / "wo_blind_key.json").read_text(encoding="utf-8"))
# ★ 载荷改用不透明编号 q-01… 之后，套组要**经 key 回查真 case_id** 才拿得到。
#   直接拿 q-01 去 cases.jsonl 查会全部落空，而那会让每个套组都变成 None——
#   套组 delta 全归到一个桶里，看上去还「有数」。
_S = {json.loads(l)["case_id"]: json.loads(l)["suite"]
      for l in pathlib.Path("cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
SUITE = {q: _S[v["case_id"]] for q, v in KEY.items() if v.get("case_id") in _S}
assert len(SUITE) == len(KEY), f"套组回查失败：{len(SUITE)}/{len(KEY)}"
rows, win, tie, lose = [], 0, 0, 0
by = collections.defaultdict(lambda: [0.0, 0.0, 0]); n_seat = 0
for seat, fn in (("seat-D-score-v1", "wo_judge_D.json"), ("seat-E-strict-v1", "wo_judge_E.json")):
    f = SP / fn
    if not f.is_file(): print(f"⚠ {fn} 不在"); continue
    n_seat += 1
    for cid, v in json.loads(f.read_text(encoding="utf-8")).items():
        if cid.startswith("_") or cid not in KEY: continue
        k = KEY[cid]
        c = float(v["A"]) if k["A"] == "candidate" else float(v["B"])
        b = float(v["B"]) if k["A"] == "candidate" else float(v["A"])
        rows.append({"case_id": cid, "seat": seat, "candidate": c, "baseline": b,
                     "suite": SUITE.get(cid), "note": v.get("note", "")})
        win += c > b; tie += c == b; lose += c < b
        s = by[SUITE.get(cid)]; s[0] += c; s[1] += b; s[2] += 1
if not rows: raise SystemExit("没有任何一席落盘")
mc = sum(r["candidate"] for r in rows)/len(rows); mb = sum(r["baseline"] for r in rows)/len(rows)
delta = (mc - mb)/10.0
(WS/"evals").mkdir(parents=True, exist_ok=True)
# ★ 写进工作区的那份**必须用真 case_id**，不是载荷里的不透明编号。
#   第一版直接把 q-01… 写了进去，发布门拿它去 cases.jsonl 查一条都对不上，
#   于是 **overall / delta / boundary / fact 四项全部报 0.000**——
#   看上去像产物彻底失败，实际是判据在跟一份对不上号的文件说话。
#   「判据指错了文件」第六次，也是后果最重的一次。
REAL = {q: v["case_id"] for q, v in KEY.items()}
flat=[{"case_id":REAL[r["case_id"]],"system":s,"overall_score":round(r[s]/10.0,4),
       "judge_id":r["seat"],"suite":r["suite"]} for r in rows for s in ("candidate","baseline")]
_want = {json.loads(l)["case_id"] for l in pathlib.Path("cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
_got = {x["case_id"] for x in flat}
assert _got <= _want, f"**写出的 case_id 有 {len(_got - _want)} 个不在 cases.jsonl 里**：{sorted(_got - _want)[:3]}"
(WS/"evals/results.jsonl").write_text("\n".join(json.dumps(r,ensure_ascii=False,sort_keys=True) for r in flat)+"\n",encoding="utf-8")
pathlib.Path("results.jsonl").write_text("\n".join(json.dumps(r,ensure_ascii=False,sort_keys=True) for r in rows)+"\n",encoding="utf-8")
pos = sum(1 for s,v in by.items() if v[2] and (v[0]-v[1])>0)
print(f"席数 {n_seat}　逐对 {len(rows)} 对")
print(f"候选均分 {mc:.3f}　基线均分 {mb:.3f}")
print(f"**真 delta = {delta:+.4f}**")
print(f"逐对：胜 {win} / 平 {tie} / 负 {lose}")
print(f"为正的套组：{pos} / {len(by)}")
for name, th in (("deep",0.07),("standard",0.05),("quick",0.03)):
    print(f"  {name:9} {'✅ 过' if delta>=th else '❌ 不过'}")
print("\n各套组 delta：")
for s,v in sorted(by.items(), key=lambda x: -(x[1][0]-x[1][1])/max(x[1][2],1)):
    if v[2]: print(f"  {s:24} {(v[0]-v[1])/v[2]/10:+.4f}  ({v[2]} 对)")
