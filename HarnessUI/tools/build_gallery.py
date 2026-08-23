#!/usr/bin/env python3
"""从 catalog.json 生成素材总览页。

一条硬规矩：**页面里所有地址必须是相对路径**。
历史上这页写死过 http://127.0.0.1:3099/…，素材服务不跑时 828 张图全碎，
用户拿到手是一片空白 —— 双击打开是唯一验收标准，不许依赖任何服务。
"""
import argparse, html, json, pathlib, sys

def build(root: pathlib.Path, out: pathlib.Path) -> int:
    cat = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    rows, missing = [], []
    for e in cat["entries"]:
        gid = f'{e["game"]}/{e["character"]}/{e["variant"]}'
        rel = {
            "t":  f'qa/crops/{gid}/light.webp',   # 人物特写 460×616，认得出是谁
            "td": f'qa/crops/{gid}/dark.webp',
            "f":  f'display/{gid}/light.webp',
            "fd": f'display/{gid}/dark.webp',
        }
        missing += [v for v in rel.values() if not (root / v).is_file()]
        rows.append({
            "id": gid, "g": e["gameName"], "c": e.get("characterZh") or e["character"],
            "v": e.get("variantZh") or e["variant"], "p": bool(e.get("public", True)), **rel,
        })
    if missing:
        print(f"✗ {len(missing)} 个文件不存在，先跑 make_derivatives / make_crops：{missing[:3]}", file=sys.stderr)
        return 1

    games = sorted({r["g"] for r in rows})
    opts = "".join(f'<option value="{html.escape(g)}">{html.escape(g)}</option>' for g in games)
    out.write_text(TEMPLATE
        .replace("__N__", str(len(rows)))
        .replace("__OPTS__", opts)
        .replace("__DATA__", json.dumps(rows, ensure_ascii=False, separators=(",", ":"))),
        encoding="utf-8")
    print(f"素材总览已生成：{len(rows)} 条 · {out.stat().st_size // 1024}KB → {out}")
    print(f"验收：双击打开，不需要任何服务。相对路径 {len(rows) * 4} 条，缺失 0。")
    return 0

TEMPLATE = r"""<!doctype html>
<meta charset="utf-8"><title>HarnessUI 素材总览 · __N__ 套</title>
<style>
:root{color-scheme:dark;--bg:#0b0f17;--card:#141b28;--line:#ffffff1c;--ink:#e8eef7;
 --dim:#8fa1bf;--warn:#ffb347;--ok:#5ad19a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:13px/1.55 -apple-system,"PingFang SC",system-ui,sans-serif}
header{position:sticky;top:0;z-index:9;background:#0b0f17f2;backdrop-filter:blur(10px);
 border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:9px;align-items:center;flex-wrap:wrap}
h1{font-size:14px;margin:0 8px 0 0;font-weight:650;letter-spacing:.02em}
select,input,button{background:var(--card);color:var(--ink);border:1px solid var(--line);
 border-radius:7px;padding:5px 10px;font-size:12px;font-family:inherit}
button{cursor:pointer}button[data-on="1"]{background:#1d3350;border-color:#3f6ea8}
.count{margin-left:auto;color:var(--dim);font-variant-numeric:tabular-nums}
main{padding:12px 16px 40px;display:grid;grid-template-columns:repeat(auto-fill,minmax(158px,1fr));gap:10px}
figure{margin:0;position:relative;border-radius:9px;overflow:hidden;background:var(--card);
 border:1px solid var(--line);line-height:0;cursor:zoom-in}
figure img{width:100%;display:block;aspect-ratio:.62;object-fit:cover;background:var(--card)}
figcaption{position:absolute;inset:auto 0 0 0;padding:5px 6px;font-size:10.5px;line-height:1.3;
 background:linear-gradient(transparent,#000000e0 55%);color:#dfe8f7}
figcaption b{font-weight:600}figcaption i{font-style:normal;color:#9db2d4;display:block;font-size:9.5px}
.tag{position:absolute;left:5px;top:5px;font-size:9.5px;padding:1px 6px;border-radius:4px;
 background:#7a2230;color:#ffd9df;font-weight:700}
#lb{position:fixed;inset:0;background:#000000ee;display:none;z-index:20;
 align-items:center;justify-content:center;flex-direction:column;gap:10px;padding:20px}
#lb[data-open="1"]{display:flex}
#lb img{max-width:94vw;max-height:82vh;border-radius:10px;box-shadow:0 20px 60px #000}
#lb p{margin:0;color:var(--dim);font-size:12px}
.empty{grid-column:1/-1;color:var(--dim);padding:40px 0;text-align:center}
</style>
<header>
  <h1>HarnessUI 素材总览</h1>
  <select id="g"><option value="">全部作品</option>__OPTS__</select>
  <input id="q" placeholder="搜角色 / 皮肤…" size="16">
  <button id="side">浅色底</button>
  <button id="priv">只看抖音可发</button>
  <span class="count" id="n"></span>
</header>
<main id="m"></main>
<div id="lb"><img id="li" alt=""><p id="lp"></p></div>
<script>
const D=__DATA__;
const m=document.getElementById('m'),n=document.getElementById('n'),
      g=document.getElementById('g'),q=document.getElementById('q'),
      sideB=document.getElementById('side'),privB=document.getElementById('priv'),
      lb=document.getElementById('lb'),li=document.getElementById('li'),lp=document.getElementById('lp');
let dark=false, pubOnly=false;
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function render(){
  const kw=q.value.trim().toLowerCase(), gv=g.value;
  const list=D.filter(r=>(!gv||r.g===gv)&&(!pubOnly||r.p)&&
    (!kw||(r.c+r.v+r.id+r.g).toLowerCase().includes(kw)));
  m.innerHTML = list.length ? list.map(r=>`<figure data-id="${esc(r.id)}">
     ${r.p?'':'<span class="tag">不可发</span>'}
     <img loading="lazy" src="${esc(dark?r.td:r.t)}" alt="${esc(r.c)}">
     <figcaption><b>${esc(r.c)}</b><i>${esc(r.v)} · ${esc(r.g)}</i></figcaption>
   </figure>`).join('') : '<p class="empty">没有匹配的素材</p>';
  n.textContent=`${list.length} / ${D.length} 套 · ${dark?'深色底':'浅色底'}`;
}
m.addEventListener('click',e=>{const f=e.target.closest('figure');if(!f)return;
  const r=D.find(x=>x.id===f.dataset.id);li.src=dark?r.fd:r.f;
  lp.textContent=`${r.c} · ${r.v} · ${r.g}　母版 master/${r.id}/${dark?'dark':'light'}.png`;
  lb.dataset.open='1';});
lb.addEventListener('click',()=>lb.dataset.open='0');
addEventListener('keydown',e=>{if(e.key==='Escape')lb.dataset.open='0';});
sideB.onclick=()=>{dark=!dark;sideB.textContent=dark?'深色底':'浅色底';sideB.dataset.on=dark?'1':'0';render();};
privB.onclick=()=>{pubOnly=!pubOnly;privB.dataset.on=pubOnly?'1':'0';render();};
g.onchange=render;q.oninput=render;render();
</script>
"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(pathlib.Path.home() / ".harness-ui"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    r = pathlib.Path(a.root).expanduser()
    sys.exit(build(r, pathlib.Path(a.out).expanduser() if a.out else r / "review.html"))
