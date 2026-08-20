import { esc, fmt, go, KIND_COLORS, topicColor, S, reduced } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { makeCamera, project, orbit, forceLayout, fitCanvas, loop } from '../../../core/g3d.js';
import { sec, table, warn, kv } from '../kit.js';

// 之前这一屏只是把点撒开，看不出任何关系 —— 那是它被打 0 分的原因。
// 现在画的是**耦合网络**：节点 = 来源/项目/主题，边 = 同一场会话里共同出现。
// 悬停任一节点，只留它和它的邻居，其余压暗 —— 耦合关系直接看得见。
export async function render(host) {
  const C = D.coupling();
  host.innerHTML = `
${sec('COUPLING GRAPH', '节点 = 来源 / 项目 / 主题。边 = 同一场会话里共同出现的次数。悬停看它连着谁，点进去看明细。')}
<div class="ctl">
  <label><input type="checkbox" id="spin" checked> 自转</label>
  <label><input type="checkbox" id="lbl" checked> 标签</label>
  <span>斥力 <input type="range" id="rep" min="6000" max="40000" step="1000" value="16000"></span>
  <button id="reset">重置视角</button>
  <span class="tag" id="hud">节点 ${C.nodes.length} · 边 ${C.edges.length}</span>
</div>
<canvas class="viz" id="cv"></canvas>
<p class="hint">${esc(C.note)}${C.dropped_edges ? `　丢弃弱边 ${C.dropped_edges} 条（未画出，不是不存在）。` : ''}</p>
${warn(`<b>颜色只是辅助。</b>来源 / 项目 / 主题三类节点在下表里都有名字和度数，
  不靠颜色也能读出来。`)}
${sec('TOP COUPLINGS', '连得最紧的一批，按共同出现次数排。')}
<div id="tbl"></div>`;

  const cv = host.querySelector('#cv');
  const hud = host.querySelector('#hud');
  const nodes = C.nodes.map(n => ({ ...n }));
  const edges = C.edges;
  const byId = new Map(nodes.map(n => [n.id, n]));
  const adj = new Map();
  for (const e of edges) {
    if (!adj.has(e.a)) adj.set(e.a, new Set());
    if (!adj.has(e.b)) adj.set(e.b, new Set());
    adj.get(e.a).add(e.b); adj.get(e.b).add(e.a);
  }
  const maxW = Math.max(1, ...nodes.map(n => n.w));
  const maxE = Math.max(1, ...edges.map(e => e.w));

  let cam = makeCamera({ pitch: 0.36, zoom: 0.92, dist: 1250 });
  let layoutOpts = { steps: 340, radius: 430, repulsion: 16000 };
  forceLayout(nodes, edges, layoutOpts);

  const ctrl = orbit(cv, cam, () => {});
  let hover = null, mouse = { x: -1, y: -1 }, spin = true, showLabels = true;

  cv.addEventListener('pointermove', e => {
    const r = cv.getBoundingClientRect();
    mouse = { x: e.clientX - r.left, y: e.clientY - r.top };
  });
  cv.addEventListener('pointerleave', () => { mouse = { x: -1, y: -1 }; });
  cv.addEventListener('click', () => {
    if (!hover) return;
    const [kind, val] = [hover.kind, hover.label];
    if (kind === 'topic') go('grid', 't=' + encodeURIComponent(val));
    else if (kind === 'project') go('grid', 'p=' + encodeURIComponent(val));
    else go('grid', 's=' + encodeURIComponent(val));
  });
  host.querySelector('#spin').addEventListener('change', e => { spin = e.target.checked; });
  host.querySelector('#lbl').addEventListener('change', e => { showLabels = e.target.checked; });
  host.querySelector('#reset').addEventListener('click', () => {
    cam = Object.assign(cam, makeCamera({ pitch: 0.36, zoom: 0.92, dist: 1250 }));
  });
  host.querySelector('#rep').addEventListener('change', e => {
    layoutOpts = { ...layoutOpts, repulsion: +e.target.value };
    forceLayout(nodes, edges, layoutOpts);
  });

  const css = k => getComputedStyle(document.body).getPropertyValue(k).trim();
  const draw = () => {
    const { ctx, w, h } = fitCanvas(cv, Math.max(460, Math.min(760, innerHeight - 260)));
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2;
    const P = new Map();
    for (const n of nodes) P.set(n.id, project(n, cam, cx, cy));

    // 命中检测：先找最近的节点，才知道要压暗谁
    hover = null;
    let best = 15;
    for (const n of nodes) {
      const p = P.get(n.id);
      const d = Math.hypot(p.sx - mouse.x, p.sy - mouse.y);
      if (d < best) { best = d; hover = n; }
    }
    const near = hover ? adj.get(hover.id) || new Set() : null;

    // 边先画（在节点之下），按深度排序
    const eList = edges.map(e => ({ e, za: P.get(e.a).depth, zb: P.get(e.b).depth }))
      .sort((x, y) => (y.za + y.zb) - (x.za + x.zb));
    for (const { e } of eList) {
      const a = P.get(e.a), b = P.get(e.b);
      const on = !hover || e.a === hover.id || e.b === hover.id;
      ctx.strokeStyle = on ? css('--acc') : css('--hair');
      ctx.globalAlpha = on ? 0.16 + 0.6 * (e.w / maxE) : 0.05;
      ctx.lineWidth = on ? 0.6 + 2.2 * (e.w / maxE) : 0.5;
      ctx.beginPath(); ctx.moveTo(a.sx, a.sy); ctx.lineTo(b.sx, b.sy); ctx.stroke();
    }

    const order = nodes.slice().sort((a, b) => P.get(b.id).depth - P.get(a.id).depth);
    for (const n of order) {
      const p = P.get(n.id);
      const on = !hover || n.id === hover.id || (near && near.has(n.id));
      const r = (3 + 9 * Math.sqrt(n.w / maxW)) * p.k * cam.zoom;
      ctx.globalAlpha = on ? 0.95 : 0.16;
      ctx.fillStyle = n.kind === 'topic' ? topicColor(n.label) : KIND_COLORS[n.kind];
      ctx.beginPath(); ctx.arc(p.sx, p.sy, Math.max(1.4, r), 0, 6.2832); ctx.fill();
      if (n.id === (hover && hover.id)) {
        ctx.strokeStyle = css('--fg'); ctx.lineWidth = 1.5; ctx.globalAlpha = 1;
        ctx.beginPath(); ctx.arc(p.sx, p.sy, Math.max(4, r + 4), 0, 6.2832); ctx.stroke();
      }
      if (showLabels && on && (n.w / maxW > 0.22 || n.id === (hover && hover.id))) {
        ctx.globalAlpha = on ? 0.9 : 0.2;
        ctx.fillStyle = css('--fg');
        ctx.font = '10.5px ui-monospace, monospace';
        ctx.fillText(n.label.slice(0, 20), p.sx + r + 4, p.sy + 3.5);
      }
    }
    ctx.globalAlpha = 1;
    hud.textContent = hover
      ? `${hover.label}　度数 ${(adj.get(hover.id) || new Set()).size}　出现 ${hover.w} 场　点击进网格`
      : `节点 ${nodes.length} · 边 ${edges.length}`;
    cv.style.cursor = hover ? 'pointer' : 'grab';
    if (spin && !ctrl.dragging() && !reduced()) cam.yaw += 0.0016;
  };

  const l = loop(draw);

  host.querySelector('#tbl').innerHTML = table(
    [{ t: 'A' }, { t: 'B' }, { t: '共同出现', r: true }, { t: '' }],
    edges.slice(0, 40).map(e => {
      const a = byId.get(e.a), b = byId.get(e.b);
      return [
        `<span class="tag">${esc(a ? a.kind : '')}</span> ${esc(a ? a.label : e.a)}`,
        `<span class="tag">${esc(b ? b.kind : '')}</span> ${esc(b ? b.label : e.b)}`,
        String(e.w),
        `<span class="meter" style="width:${Math.round(e.w / maxE * 110)}px"></span>`];
    }));

  return { dispose() { l.stop(); ctrl.dispose(); } };
}
