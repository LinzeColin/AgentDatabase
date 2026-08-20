#!/usr/bin/env python3
"""人物特写墙：一屏几十张，扫过去点掉有缺陷的。

判断标准是用户本人——自动判官三轮都没能复现它（见 build_qa_crops.py 的说明）。
这里唯一的机器工作是把画面裁到人物、排成密网格、把标记结果导成一份 id 清单，
那份清单直接喂给重出流程。

Usage:
    python3 build_qa_page.py --catalog … --out …/qa/index.html [--scores defects.json]
"""

from __future__ import annotations

import argparse
import json
import pathlib

PAGE = """<!doctype html>
<meta charset="utf-8"><title>HarnessUI 缺陷复核 · %(count)d 张</title>
<style>
:root{color-scheme:dark;--bg:#0b0f17;--line:#ffffff1e;--ink:#e8eef7;--dim:#93a4c2;--bad:#ff5f6d}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.5 -apple-system,"PingFang SC",system-ui,sans-serif}
header{position:sticky;top:0;z-index:9;background:#0b0f17f2;backdrop-filter:blur(8px);
 border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:9px;align-items:center;flex-wrap:wrap}
h1{font-size:14px;margin:0 10px 0 0;font-weight:650}
select,input,button{background:#141b28;color:var(--ink);border:1px solid var(--line);
 border-radius:7px;padding:5px 10px;font-size:12px}
button{cursor:pointer}
button.primary{background:#7a2230;border-color:#c0455a}
.count{margin-left:auto;color:var(--dim);font-size:12px;font-variant-numeric:tabular-nums}
main{padding:12px 16px 76px;display:grid;
 grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:9px}
figure{margin:0;position:relative;border:2px solid transparent;border-radius:8px;
 overflow:hidden;background:#141b28;cursor:pointer;line-height:0}
figure[data-bad="1"]{border-color:var(--bad)}
figure[data-bad="1"] img{opacity:.42}
figure img{width:100%%;display:block;aspect-ratio:0.62;object-fit:cover}
figcaption{position:absolute;left:0;right:0;bottom:0;padding:3px 5px;font-size:10px;line-height:1.25;
 background:linear-gradient(transparent,#000000d8 45%%);color:#dce6f7}
figure .sd{position:absolute;right:4px;top:4px;font-size:9px;padding:1px 5px;border-radius:4px;
 background:#000a;color:#ffd479}
figure[data-bad="1"]::after{content:"重做";position:absolute;left:4px;top:4px;font-size:10px;
 padding:1px 6px;border-radius:4px;background:var(--bad);color:#2a0006;font-weight:700}
#out{position:fixed;left:0;right:0;bottom:0;background:#0b0f17f7;border-top:1px solid var(--line);
 padding:9px 16px;display:none;gap:9px;align-items:center}
#out[data-open="1"]{display:flex}
#out textarea{flex:1;height:52px;background:#000;color:#9fe6bb;border:1px solid var(--line);
 border-radius:7px;padding:6px;font:11px/1.35 ui-monospace,Menlo,monospace}
</style>
<header>
  <h1>缺陷复核</h1>
  <select id="game"><option value="">全部游戏</option></select>
  <select id="side"><option value="">昼+夜</option><option value="light">只看昼</option><option value="dark">只看夜</option></select>
  <select id="sort"><option value="ai">可疑度排序</option><option value="name">按角色排序</option></select>
  <input id="q" type="search" placeholder="搜角色…" size="10">
  <button id="mark">只看已标记</button>
  <button id="export" class="primary">导出重做清单</button>
  <span class="count" id="count"></span>
</header>
<main id="grid"></main>
<div id="out"><textarea id="list" readonly></textarea><button id="copy">复制</button><button id="close">关闭</button></div>
<script>
const DATA = %(data)s;
const KEY = "harnessui.qa.bad.v1";
const bad = new Set(JSON.parse(localStorage.getItem(KEY) || "[]"));
const save = () => localStorage.setItem(KEY, JSON.stringify([...bad]));
let onlyBad = false;
const grid = document.getElementById("grid");

function render(){
  const g = document.getElementById("game").value;
  const sd = document.getElementById("side").value;
  const kw = document.getElementById("q").value.trim().toLowerCase();
  const sort = document.getElementById("sort").value;
  let rows = DATA.filter(e => (!g || e.game === g) && (!sd || e.side === sd) &&
    (!onlyBad || bad.has(e.key)) &&
    (!kw || e.character.includes(kw) || (e.label||"").includes(kw) || e.variant.includes(kw)));
  rows.sort(sort === "ai" ? (a,b) => (b.score??-1)-(a.score??-1) || a.key.localeCompare(b.key)
                          : (a,b) => a.key.localeCompare(b.key));
  grid.textContent = "";
  const frag = document.createDocumentFragment();
  for (const e of rows){
    const fig = document.createElement("figure");
    fig.dataset.bad = bad.has(e.key) ? "1" : "0";
    const img = document.createElement("img");
    img.loading = "lazy"; img.src = e.crop; img.alt = e.label || e.character;
    const cap = document.createElement("figcaption");
    cap.textContent = `${e.label || e.character}${e.variant==="default"?"":" · "+e.variant} ${e.side==="dark"?"夜":"昼"}`;
    fig.append(img, cap);
    if (e.score != null){ const s = document.createElement("span"); s.className="sd"; s.textContent=e.score; fig.appendChild(s); }
    fig.onclick = () => { bad.has(e.key) ? bad.delete(e.key) : bad.add(e.key);
      save(); fig.dataset.bad = bad.has(e.key)?"1":"0"; counts(); };
    frag.appendChild(fig);
  }
  grid.appendChild(frag);
  counts(rows.length);
}
function counts(shown){
  document.getElementById("count").textContent =
    `${shown ?? grid.children.length} / ${DATA.length} 张 · 已标记重做 ${bad.size}`;
}
for (const id of ["game","side","sort","q"]) document.getElementById(id).addEventListener("input", render);
document.getElementById("mark").onclick = (ev) => { onlyBad = !onlyBad;
  ev.target.textContent = onlyBad ? "看全部" : "只看已标记"; render(); };
document.getElementById("export").onclick = () => {
  document.getElementById("list").value = [...bad].sort().join("\\n") || "（没有标记任何一张）";
  document.getElementById("out").dataset.open = "1";
};
document.getElementById("copy").onclick = () => { const t=document.getElementById("list"); t.select(); document.execCommand("copy"); };
document.getElementById("close").onclick = () => document.getElementById("out").dataset.open = "0";
const sel = document.getElementById("game");
for (const g of [...new Set(DATA.map(e=>e.game))]) {
  const o = document.createElement("option");
  o.value = g; o.textContent = DATA.find(e=>e.game===g).gameName; sel.appendChild(o);
}
render();
</script>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--scores", type=pathlib.Path,
                        help="screen_defects 的结果，只用来排序，不当判决")
    parser.add_argument("--base", default="http://127.0.0.1:3099")
    args = parser.parse_args()

    scores = {}
    if args.scores and args.scores.exists():
        for row in json.loads(args.scores.read_text(encoding="utf-8")).get("results", []):
            if "error" in row:
                continue
            # 判官不可信到能当判决，但它排出来的顺序还是能让人先看到最可疑的。
            scores[f"{row['id']}|{row['side']}"] = row.get("obviousness") or (
                {"major": 7, "minor": 4}.get(row.get("severity"), 0))

    data = []
    for entry in json.loads(args.catalog.read_text(encoding="utf-8"))["entries"]:
        for side in ("light", "dark"):
            key = f"{entry['id']}|{side}"
            data.append({
                "key": key, "id": entry["id"], "side": side,
                "game": entry["game"], "gameName": entry["gameName"],
                "character": entry["character"], "variant": entry["variant"],
                "label": entry.get("label") or entry["character"],
                "crop": f"{args.base}/qa/crops/{entry['id']}/{side}.webp",
                "score": scores.get(key),
            })
    args.out.write_text(PAGE % {"count": len(data), "data": json.dumps(data, ensure_ascii=False)},
                        encoding="utf-8")
    print(f"复核页已生成：{len(data)} 张（其中 {len(scores)} 张有可疑度分）→ {args.out}")


if __name__ == "__main__":
    main()
