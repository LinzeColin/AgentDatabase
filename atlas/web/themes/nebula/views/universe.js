import { esc, fmt, go, KIND_COLORS, topicColor, reduced, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { makeCamera, project, orbit as orbitCtl, forceLayout, fitCanvas, loop } from '../../../core/g3d.js';
import { sec, bento, orbit, drawer, table, warn, pill } from '../kit.js';

// 星域版的耦合网络：带辉光的加色渲染，边有渐变，节点有光晕。
export async function render(host) {
  const C = D.coupling();
  host.innerHTML = `
${sec('耦合星图', '节点 = 来源 / 项目 / 主题。边 = 同一场会话里共同出现的次数。悬停任一节点，只留它和它的邻居 —— 耦合关系直接看得见。')}
<div class="ctl">
  <button id="spin" aria-pressed="true">自转</button>
  <button id="lbl" aria-pressed="true">标签</button>
  <button id="reset">重置视角</button>
  <span class="pill" id="hud">节点 ${C.nodes.length} · 边 ${C.edges.length}</span>
</div>
<canvas class="viz" id="cv"></canvas>
<p class="hint">${esc(C.note)}${C.dropped_edges ? `　丢弃弱边 ${C.dropped_edges} 条（未画出，不是不存在）。` : ''}</p>
${warn('<b>颜色只是辅助。</b>三类节点在下面的抽屉里都有名字和度数，不靠颜色也能读出来。')}
<div id="near"></div>
${drawer('展开最紧的 40 组耦合', table([{ t: 'A' }, { t: 'B' }, { t: '共同出现', r: true }],
  C.edges.slice(0, 40).map(e => {
    const a = C.nodes.find(n => n.id === e.a), b = C.nodes.find(n => n.id === e.b);
    return [`${pill(a ? a.kind : '')} ${esc(a ? a.label : e.a)}`,
            `${pill(b ? b.kind : '')} ${esc(b ? b.label : e.b)}`, String(e.w)];
  })))}`;

  const cv = host.querySelector('#cv'), hud = host.querySelector('#hud'), nearBox = host.querySelector('#near');
  const nodes = C.nodes.map(n => ({ ...n })), edges = C.edges;
  const adj = new Map();
  for (const e of edges) {
    if (!adj.has(e.a)) adj.set(e.a, new Set());
    if (!adj.has(e.b)) adj.set(e.b, new Set());
    adj.get(e.a).add(e.b); adj.get(e.b).add(e.a);
  }
  const maxW = Math.max(1, ...nodes.map(n => n.w)), maxE = Math.max(1, ...edges.map(e => e.w));
  const cam = makeCamera({ pitch: 0.34, zoom: 0.9, dist: 1250 });
  forceLayout(nodes, edges, { steps: 340, radius: 430, repulsion: 16000 });
  const ctrl = orbitCtl(cv, cam, () => {});
  let hover = null, mouse = { x: -1, y: -1 }, spin = true, labels = true;

  cv.addEventListener('pointermove', e => {
    const r = cv.getBoundingClientRect();
    mouse = { x: e.clientX - r.left, y: e.clientY - r.top };
  });
  cv.addEventListener('pointerleave', () => { mouse = { x: -1, y: -1 }; });
  cv.addEventListener('click', () => {
    if (!hover) return;
    go('grid', (hover.kind === 'topic' ? 't=' : hover.kind === 'project' ? 'p=' : 's=')
      + encodeURIComponent(hover.label));
  });
  const tog = (id, set) => host.querySelector(id).addEventListener('click', e => {
    const on = e.currentTarget.getAttribute('aria-pressed') !== 'true';
    e.currentTarget.setAttribute('aria-pressed', String(on)); set(on);
  });
  tog('#spin', v => { spin = v; }); tog('#lbl', v => { labels = v; });
  host.querySelector('#reset').addEventListener('click', () => {
    Object.assign(cam, makeCamera({ pitch: 0.34, zoom: 0.9, dist: 1250 }));
  });

  const css = k => getComputedStyle(document.body).getPropertyValue(k).trim();
  const draw = () => {
    const { ctx, w } = fitCanvas(cv, Math.max(480, Math.min(780, innerHeight - 250)));
    const h = cv.clientHeight;
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2;
    const P = new Map(nodes.map(n => [n.id, project(n, cam, cx, cy)]));

    hover = null; let best = 16;
    for (const n of nodes) {
      const p = P.get(n.id), d = Math.hypot(p.sx - mouse.x, p.sy - mouse.y);
      if (d < best) { best = d; hover = n; }
    }
    const near = hover ? (adj.get(hover.id) || new Set()) : null;

    ctx.globalCompositeOperation = 'lighter';
    for (const e of edges) {
      const a = P.get(e.a), b = P.get(e.b);
      const on = !hover || e.a === hover.id || e.b === hover.id;
      const g = ctx.createLinearGradient(a.sx, a.sy, b.sx, b.sy);
      const c1 = css('--acc'), c2 = css('--acc2');
      g.addColorStop(0, c1); g.addColorStop(1, c2);
      ctx.strokeStyle = on ? g : css('--line');
      ctx.globalAlpha = on ? 0.10 + 0.55 * (e.w / maxE) : 0.035;
      ctx.lineWidth = on ? 0.7 + 2.6 * (e.w / maxE) : 0.5;
      ctx.beginPath(); ctx.moveTo(a.sx, a.sy); ctx.lineTo(b.sx, b.sy); ctx.stroke();
    }
    for (const n of nodes.slice().sort((a, b) => P.get(b.id).depth - P.get(a.id).depth)) {
      const p = P.get(n.id);
      const on = !hover || n.id === hover.id || (near && near.has(n.id));
      const r = Math.max(1.6, (3.5 + 11 * Math.sqrt(n.w / maxW)) * p.k * cam.zoom);
      const col = n.kind === 'topic' ? topicColor(n.label) : KIND_COLORS[n.kind];
      // 光晕：先画一层大而淡的，再画实心的
      const gg = ctx.createRadialGradient(p.sx, p.sy, 0, p.sx, p.sy, r * 3.4);
      gg.addColorStop(0, col); gg.addColorStop(1, 'transparent');
      ctx.globalAlpha = on ? 0.28 : 0.05;
      ctx.fillStyle = gg;
      ctx.beginPath(); ctx.arc(p.sx, p.sy, r * 3.4, 0, 6.2832); ctx.fill();
      ctx.globalAlpha = on ? 0.95 : 0.12;
      ctx.fillStyle = col;
      ctx.beginPath(); ctx.arc(p.sx, p.sy, r, 0, 6.2832); ctx.fill();
    }
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    if (labels) {
      for (const n of nodes) {
        const p = P.get(n.id);
        const on = !hover || n.id === hover.id || (near && near.has(n.id));
        if (!on || (n.w / maxW < 0.22 && n.id !== (hover && hover.id))) continue;
        ctx.fillStyle = css('--fg');
        ctx.font = '600 11.5px -apple-system, system-ui, sans-serif';
        ctx.fillText(n.label.slice(0, 18), p.sx + 12, p.sy + 4);
      }
    }
    hud.textContent = hover
      ? `${hover.label} · 度数 ${(adj.get(hover.id) || new Set()).size} · 出现 ${hover.w} 场`
      : `节点 ${nodes.length} · 边 ${edges.length}`;
    cv.style.cursor = hover ? 'pointer' : 'grab';
    if (spin && !ctrl.dragging() && !reduced()) cam.yaw += 0.0015;

    if (hover && nearBox.dataset.for !== hover.id) {
      nearBox.dataset.for = hover.id;
      const list = D.neighbours(hover.id).slice(0, 10);
      nearBox.innerHTML = `<p class="hint" style="margin-top:18px"><b style="color:var(--fg)">${esc(hover.label)}</b> 连着这些：</p>`
        + orbit(list.map(x => {
          const nn = nodes.find(z => z.id === x.id);
          return { k: nn ? nn.label : x.id, v: x.w, label: String(x.w),
            c: nn && nn.kind === 'topic' ? topicColor(nn.label) : 'var(--acc)' };
        }));
    }
  };
  const l = loop(draw);
  enter('.sec, .card', host);
  return { dispose() { l.stop(); ctrl.dispose(); } };
}
