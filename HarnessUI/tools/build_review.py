#!/usr/bin/env python3
"""Build the acceptance page — the one thing the machine gate cannot do.

`runner.py` checks four numbers: aspect, width, brightness, and how much of the
subject spills right of the left third. It has no opinion on whether the face is
the right character, whether the proportions went chibi, or whether the legwear
rule was honoured — and those are exactly the three things this project has been
rejected over before. So acceptance is a human pass, and this page exists to
make that pass cheap: a contact sheet with day/night side by side, filters, and
one click to flag a bad frame.

The flags live in localStorage and export as a plain id list, so a rejection
round is `python3 batch_run.py` over that list rather than a conversation about
which ones looked wrong.

Served from the same local server as the artwork, so clicking a thumbnail opens
the real 3840x2160 master rather than an upscaled preview.

Usage:
    python3 build_review.py --catalog …/catalog.json --out …/review.html
"""

from __future__ import annotations

import argparse
import json
import pathlib

PAGE = """<!doctype html>
<meta charset="utf-8"><title>HarnessUI 验收 · %(count)d 个变体</title>
<style>
:root{color-scheme:dark;--bg:#0b0f17;--panel:#141b28;--line:#ffffff1f;--ink:#e8eef7;--dim:#93a4c2;--bad:#ff6b6b;--ok:#6ee7a8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 -apple-system,"PingFang SC",system-ui,sans-serif}
header{position:sticky;top:0;z-index:9;background:#0b0f17f2;backdrop-filter:blur(8px);
 border-bottom:1px solid var(--line);padding:12px 18px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
h1{font-size:15px;margin:0 12px 0 0;font-weight:650;letter-spacing:.2px}
select,input,button{background:var(--panel);color:var(--ink);border:1px solid var(--line);
 border-radius:8px;padding:6px 11px;font-size:13px}
button{cursor:pointer}
button.primary{background:#2b4a7a;border-color:#4a76b8}
.count{margin-left:auto;color:var(--dim);font-size:12px;font-variant-numeric:tabular-nums}
main{padding:16px 18px 80px}
.char{margin:0 0 26px}
.char h2{font-size:13px;color:var(--dim);font-weight:600;margin:0 0 8px;
 border-bottom:1px solid var(--line);padding-bottom:6px}
.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
figure{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:11px;overflow:hidden}
figure[data-flag="1"]{border-color:var(--bad);box-shadow:0 0 0 1px var(--bad) inset}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line)}
.pair a{display:block;position:relative;background:#000}
.pair img{display:block;width:100%%;aspect-ratio:16/9;object-fit:cover}
.pair span{position:absolute;left:6px;top:6px;font-size:10px;padding:1px 6px;border-radius:4px;
 background:#000000a8;color:#cfe0ff}
figcaption{padding:7px 9px;display:flex;gap:8px;align-items:center;font-size:12px}
figcaption b{font-weight:600}
figcaption em{color:var(--dim);font-style:normal;font-size:11px}
figcaption button{margin-left:auto;padding:3px 9px;font-size:11px}
figure[data-flag="1"] figcaption button{background:var(--bad);border-color:var(--bad);color:#2a0000}
#out{position:fixed;left:0;right:0;bottom:0;background:#0b0f17f5;border-top:1px solid var(--line);
 padding:10px 18px;display:none;gap:10px;align-items:center}
#out[data-open="1"]{display:flex}
#out textarea{flex:1;height:54px;background:#000;color:#9fe6bb;border:1px solid var(--line);
 border-radius:8px;padding:7px;font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace}
</style>
<header>
  <h1>HarnessUI 验收</h1>
  <select id="game"><option value="">全部游戏</option></select>
  <input id="q" type="search" placeholder="搜角色…" size="14">
  <select id="only"><option value="">全部</option><option value="flag">只看已标记</option></select>
  <button id="export" class="primary">导出不合格清单</button>
  <span class="count" id="count"></span>
</header>
<main id="main"></main>
<div id="out"><textarea id="list" readonly></textarea><button id="copy">复制</button><button id="close">关闭</button></div>
<script>
const DATA = %(data)s;
const KEY = "harnessui.review.flags.v1";
const flags = new Set(JSON.parse(localStorage.getItem(KEY) || "[]"));
const save = () => localStorage.setItem(KEY, JSON.stringify([...flags]));
const main = document.getElementById("main");

function render() {
  const game = document.getElementById("game").value;
  const term = document.getElementById("q").value.trim().toLowerCase();
  const only = document.getElementById("only").value;
  const rows = DATA.filter(e =>
    (!game || e.game === game) &&
    (!term || e.character.includes(term) || e.variant.includes(term)) &&
    (only !== "flag" || flags.has(e.id)));
  const byChar = new Map();
  for (const e of rows) {
    const k = e.game + "/" + e.character;
    if (!byChar.has(k)) byChar.set(k, []);
    byChar.get(k).push(e);
  }
  main.textContent = "";
  const frag = document.createDocumentFragment();
  for (const [k, list] of byChar) {
    const box = document.createElement("section");
    box.className = "char";
    const h = document.createElement("h2");
    h.textContent = `${list[0].gameName} · ${list[0].character}  （${list.length} 个变体）`;
    const row = document.createElement("div");
    row.className = "row";
    for (const e of list) {
      const fig = document.createElement("figure");
      fig.dataset.flag = flags.has(e.id) ? "1" : "0";
      const pair = document.createElement("div");
      pair.className = "pair";
      for (const [side, url, full] of [["昼", e.thumb, e.lightFull], ["夜", e.thumbDark, e.darkFull]]) {
        const a = document.createElement("a");
        a.href = full; a.target = "_blank"; a.rel = "noopener";
        const img = document.createElement("img");
        img.loading = "lazy"; img.src = url; img.alt = `${e.character} ${side}`;
        const tag = document.createElement("span"); tag.textContent = side;
        a.append(img, tag); pair.appendChild(a);
      }
      const cap = document.createElement("figcaption");
      const name = document.createElement("b"); name.textContent = e.variant;
      const meta = document.createElement("em"); meta.textContent = e.gameName;
      const btn = document.createElement("button");
      const paint = () => { btn.textContent = flags.has(e.id) ? "已标记不合格" : "标记不合格"; };
      paint();
      btn.addEventListener("click", () => {
        flags.has(e.id) ? flags.delete(e.id) : flags.add(e.id);
        save(); fig.dataset.flag = flags.has(e.id) ? "1" : "0"; paint(); count();
      });
      cap.append(name, meta, btn);
      fig.append(pair, cap); row.appendChild(fig);
    }
    box.append(h, row); frag.appendChild(box);
  }
  main.appendChild(frag);
  count(rows.length);
}
function count(shown) {
  document.getElementById("count").textContent =
    `${shown ?? document.querySelectorAll("figure").length} / ${DATA.length} 个变体 · 已标记 ${flags.size}`;
}
for (const id of ["game", "q", "only"]) document.getElementById(id).addEventListener("input", render);
document.getElementById("export").addEventListener("click", () => {
  document.getElementById("list").value = [...flags].sort().join("\\n") || "（没有标记任何不合格项）";
  document.getElementById("out").dataset.open = "1";
});
document.getElementById("copy").addEventListener("click", () => {
  const t = document.getElementById("list"); t.select(); document.execCommand("copy");
});
document.getElementById("close").addEventListener("click", () => {
  document.getElementById("out").dataset.open = "0";
});
const sel = document.getElementById("game");
for (const g of [...new Set(DATA.map(e => e.game))]) {
  const o = document.createElement("option");
  o.value = g; o.textContent = DATA.find(e => e.game === g).gameName;
  sel.appendChild(o);
}
render();
</script>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--base", default="http://127.0.0.1:3099")
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    data = []
    for entry in catalog["entries"]:
        game, character, variant = entry["id"].split("/")
        data.append({
            **{k: entry[k] for k in ("id", "game", "gameName", "character", "variant", "thumb")},
            "thumbDark": f"{args.base}/thumb/{game}/{character}/{variant}/dark.webp",
            # Click-through goes to the master, not the display derivative — a
            # 2560px re-encode is not what acceptance should be judged on.
            "lightFull": f"{args.base}/master/{game}/{character}/{variant}/light.png",
            "darkFull": f"{args.base}/master/{game}/{character}/{variant}/dark.png",
        })
    args.out.write_text(
        PAGE % {"count": len(data), "data": json.dumps(data, ensure_ascii=False)},
        encoding="utf-8")
    print(f"验收页已生成：{len(data)} 个变体 → {args.out}")


if __name__ == "__main__":
    main()
