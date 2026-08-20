import { esc, go, KIND_COLORS, topicColor, enter, reduced } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { makeCamera, project, orbit as orbitCtl, forceLayout, fitCanvas, loop } from '../../../core/g3d.js';
import { sec, lede, p, n, big, aside, note, figure, rank, table } from '../kit.js';

// 手记版：钢笔线稿。没有辉光、没有加色混合 —— 细墨线 + 空心节点。
export async function render(host) {
  const C = D.coupling();
  const nodes = C.nodes.map(x => ({ ...x })), edges = C.edges;
  const adj = new Map();
  for (const e of edges) {
    if (!adj.has(e.a)) adj.set(e.a, new Set());
    if (!adj.has(e.b)) adj.set(e.b, new Set());
    adj.get(e.a).add(e.b); adj.get(e.b).add(e.a);
  }
  const byId = new Map(nodes.map(x => [x.id, x]));
  const top = edges.slice(0, 3).map(e => {
    const a = byId.get(e.a), b = byId.get(e.b);
    return `<b>${esc(a ? a.label : e.a)}</b> 与 <b>${esc(b ? b.label : e.b)}</b>（${e.w} 次）`;
  });

  host.innerHTML = `
${sec('耦合')}
${lede(`把每一场会话看成一次「同时提到」，就能把来源、项目、主题连成一张网。
  连得最紧的三对是 ${top.join('、')}。整张网有 ${n(nodes.length)} 个节点、${n(edges.length)} 条边。`)}
${aside(esc(C.note) + (C.dropped_edges ? `<br>另有 ${C.dropped_edges} 条弱边未画出 —— 不是不存在。` : ''))}
<div class="ctl">
  <button id="spin" aria-pressed="true">自转</button>
  <button id="reset">重置视角</button>
  <span id="hud"></span>
</div>
${figure('<canvas class="viz" id="cv"></canvas>',
  '拖动可以转视角，滚轮缩放。悬停任一节点，只留它和它的邻居 —— 其余淡去。点击进网格。')}
<div id="near"></div>
${figure(table([{ t: 'A' }, { t: 'B' }, { t: '共同出现', r: true }],
  edges.slice(0, 30).map(e => {
    const a = byId.get(e.a), b = byId.get(e.b);
    return [esc(a ? a.label : e.a), esc(b ? b.label : e.b), String(e.w)];
  })), '连得最紧的三十组。')}`;

  const cv = host.querySelector('#cv'), hud = host.querySelector('#hud'), nearBox = host.querySelector('#near');
  const maxW = Math.max(1, ...nodes.map(x => x.w)), maxE = Math.max(1, ...edges.map(e => e.w));
  const cam = makeCamera({ pitch: 0.3, zoom: 0.86, dist: 1300 });
  forceLayout(nodes, edges, { steps: 340, radius: 400, repulsion: 15000 });
  const ctrl = orbitCtl(cv, cam, () => {});
  let hover = null, mouse = { x: -1, y: -1 }, spin = true;

  cv.addEventListener('pointermove', e => {
    const r = cv.getBoundingClientRect(); mouse = { x: e.clientX - r.left, y: e.clientY - r.top };
  });
  cv.addEventListener('pointerleave', () => { mouse = { x: -1, y: -1 }; });
  cv.addEventListener('click', () => {
    if (!hover) return;
    go('grid', (hover.kind === 'topic' ? 't=' : hover.kind === 'project' ? 'p=' : 's=') + encodeURIComponent(hover.label));
  });
  host.querySelector('#spin').onclick = e => {
    spin = e.currentTarget.getAttribute('aria-pressed') !== 'true';
    e.currentTarget.setAttribute('aria-pressed', String(spin));
  };
  host.querySelector('#reset').onclick = () => Object.assign(cam, makeCamera({ pitch: 0.3, zoom: 0.86, dist: 1300 }));

  const css = k => getComputedStyle(document.body).getPropertyValue(k).trim();
  const draw = () => {
    const { ctx, w } = fitCanvas(cv, Math.max(420, Math.min(620, innerHeight - 300)));
    const h = cv.clientHeight;
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2;
    const P = new Map(nodes.map(x => [x.id, project(x, cam, cx, cy)]));
    hover = null; let best = 15;
    for (const x of nodes) {
      const q = P.get(x.id), d = Math.hypot(q.sx - mouse.x, q.sy - mouse.y);
      if (d < best) { best = d; hover = x; }
    }
    const near = hover ? (adj.get(hover.id) || new Set()) : null;
    // 细墨线
    for (const e of edges) {
      const a = P.get(e.a), b = P.get(e.b);
      const on = !hover || e.a === hover.id || e.b === hover.id;
      ctx.strokeStyle = css('--fg');
      ctx.globalAlpha = on ? 0.07 + 0.32 * (e.w / maxE) : 0.02;
      ctx.lineWidth = on ? 0.4 + 1.1 * (e.w / maxE) : 0.35;
      ctx.beginPath(); ctx.moveTo(a.sx, a.sy); ctx.lineTo(b.sx, b.sy); ctx.stroke();
    }
    // 空心节点，只有悬停的那个填实
    for (const x of nodes.slice().sort((a, b) => P.get(b.id).depth - P.get(a.id).depth)) {
      const q = P.get(x.id);
      const on = !hover || x.id === hover.id || (near && near.has(x.id));
      const r = Math.max(1.6, (2.6 + 8 * Math.sqrt(x.w / maxW)) * q.k * cam.zoom);
      const col = x.kind === 'topic' ? topicColor(x.label) : KIND_COLORS[x.kind];
      ctx.globalAlpha = on ? 0.9 : 0.12;
      ctx.strokeStyle = col; ctx.lineWidth = 1.3;
      ctx.beginPath(); ctx.arc(q.sx, q.sy, r, 0, 6.2832); ctx.stroke();
      if (x.id === (hover && hover.id)) { ctx.fillStyle = col; ctx.globalAlpha = 1; ctx.fill(); }
      if (on && (x.w / maxW > 0.24 || x.id === (hover && hover.id))) {
        ctx.globalAlpha = on ? 0.85 : 0.15;
        ctx.fillStyle = css('--fg');
        ctx.font = 'italic 11.5px "Iowan Old Style", Palatino, Georgia, serif';
        ctx.fillText(x.label.slice(0, 18), q.sx + r + 5, q.sy + 4);
      }
    }
    ctx.globalAlpha = 1;
    hud.textContent = hover ? `${hover.label} · 度数 ${(adj.get(hover.id) || new Set()).size} · 出现 ${hover.w} 场` : '';
    cv.style.cursor = hover ? 'pointer' : 'grab';
    if (spin && !ctrl.dragging() && !reduced()) cam.yaw += 0.0012;
    if (hover && nearBox.dataset.for !== hover.id) {
      nearBox.dataset.for = hover.id;
      nearBox.innerHTML = p(`<b>${esc(hover.label)}</b> 连着：`) + rank(
        D.neighbours(hover.id).slice(0, 8).map(x => {
          const nn = byId.get(x.id);
          return { k: nn ? nn.label : x.id, v: x.w, label: String(x.w) };
        }));
    }
  };
  const l = loop(draw);
  enter('.sec, p.body, figure, .aside', host);
  return { dispose() { l.stop(); ctrl.dispose(); } };
}
