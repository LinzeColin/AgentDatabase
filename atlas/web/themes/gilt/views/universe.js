import { esc, fmt, go, KIND_COLORS, topicColor, reduced, enter, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { forceLayout, loop } from '../../../core/g3d.js';
import { buildGraphScene } from '../../../core/scene3d.js';
import { hero, sec, orbit, drawer, table, warn, pill } from '../kit.js';

// 背景已经是整片星云；这一屏是它的**结构图** —— 谁和谁总是一起出现。
export async function render(host) {
  const C = D.coupling();
  const nodes = C.nodes.map(n => ({ ...n,
    color: n.kind === 'topic' ? topicColor(n.label) : KIND_COLORS[n.kind] }));
  const edges = C.edges;
  forceLayout(nodes, edges, { steps: 340, radius: 430, repulsion: 16000 });
  const byId = new Map(nodes.map(n => [n.id, n]));
  const adj = new Map();
  for (const e of edges) {
    if (!adj.has(e.a)) adj.set(e.a, new Set());
    if (!adj.has(e.b)) adj.set(e.b, new Set());
    adj.get(e.a).add(e.b); adj.get(e.b).add(e.a);
  }

  host.innerHTML = `
${hero('结构', '谁总是和谁一起出现', 
  `背景那片星云是「有多少」，这一屏是「怎么连的」。一个点是一个来源、项目或主题；
   一条线表示它们在同一次对话里同时出现过。`)}
<div class="ctl">
  <button id="spin" aria-pressed="true">自转</button>
  <button id="reset">回到正面</button>
  <span class="pill" id="ghud">${nodes.length} 个点 · ${edges.length} 条线</span>
</div>
<canvas class="viz" id="cv" role="img" aria-label="来源、项目、主题的关联网络图。连得最紧的组合见下方表格。"></canvas>
<p class="hint">拖动转视角，滚轮推拉。停在一个点上，只留它和它连着的；点一下进明细。
  ${C.dropped_edges ? `另有 ${C.dropped_edges} 条太弱的线没画出来 —— 不是没有。` : ''}</p>
<div id="near"></div>
${drawer('连得最紧的 40 组', table([{ t: '一头' }, { t: '另一头' }, { t: '同时出现', r: true }],
  edges.slice(0, 40).map(e => {
    const a = byId.get(e.a), b = byId.get(e.b);
    return [`${pill(a ? a.kind : '')} ${esc(a ? a.label : e.a)}`,
            `${pill(b ? b.kind : '')} ${esc(b ? b.label : e.b)}`, String(e.w)];
  })))}`;

  const cv = host.querySelector('#cv');
  cv.style.height = Math.max(440, Math.min(720, innerHeight - 300)) + 'px';
  const ghud = host.querySelector('#ghud'), nearBox = host.querySelector('#near');
  let spin = true, last = performance.now(), drag = null, cur = -1;
  const S3 = buildGraphScene(cv, nodes, edges, { theme: 'gilt' });

  cv.addEventListener('pointerdown', e => {
    drag = { x: e.clientX, y: e.clientY, yaw: S3.orbit.yaw, pitch: S3.orbit.pitch };
    cv.setPointerCapture(e.pointerId);
  });
  cv.addEventListener('pointermove', e => {
    S3.setPointer(e.clientX, e.clientY);
    if (!drag) return;
    S3.orbit.yaw = drag.yaw - (e.clientX - drag.x) * 0.006;
    S3.orbit.pitch = Math.max(-1.4, Math.min(1.4, drag.pitch + (e.clientY - drag.y) * 0.005));
  });
  cv.addEventListener('pointerup', () => { drag = null; });
  cv.addEventListener('pointerleave', () => { drag = null; S3.clearPointer(); });
  cv.addEventListener('wheel', e => { e.preventDefault();
    S3.orbit.dist = Math.max(280, Math.min(3200, S3.orbit.dist * (e.deltaY > 0 ? 1.09 : 0.92))); },
    { passive: false });
  cv.addEventListener('click', () => {
    const i = S3.hovered(); if (i < 0) return;
    const n = nodes[i];
    go('grid', (n.kind === 'topic' ? 't=' : n.kind === 'project' ? 'p=' : 's=') + encodeURIComponent(n.label));
  });
  host.querySelector('#spin').onclick = e => {
    spin = e.currentTarget.getAttribute('aria-pressed') !== 'true';
    e.currentTarget.setAttribute('aria-pressed', String(spin));
  };
  host.querySelector('#reset').onclick = () => { S3.orbit.yaw = -0.6; S3.orbit.pitch = 0.30; S3.orbit.dist = 820; };

  const l = loop(now => {
    const dt = Math.min(64, now - last); last = now;
    const i = S3.tick(dt, spin && !drag && !reduced());
    cv.style.cursor = i >= 0 ? 'pointer' : 'grab';
    if (i === cur) return;
    cur = i;
    if (i < 0) { ghud.textContent = `${nodes.length} 个点 · ${edges.length} 条线`; return; }
    const n = nodes[i];
    ghud.textContent = `${n.label} · 连着 ${(adj.get(n.id) || new Set()).size} 个 · 出现 ${n.w} 次`;
    nearBox.innerHTML = `<p class="hint" style="margin-top:18px"><b style="color:var(--fg)">${esc(n.label)}</b> 连着这些：</p>`
      + orbit(D.neighbours(n.id).slice(0, 10).map(x => {
        const nn = byId.get(x.id);
        return { k: nn ? nn.label : x.id, v: x.w, label: String(x.w),
          c: nn && nn.kind === 'topic' ? topicColor(nn.label) : 'var(--acc)' };
      }));
  });
  const onR = () => { cv.style.height = Math.max(440, Math.min(720, innerHeight - 300)) + 'px'; S3.resize(); };
  addEventListener('resize', onR);
  enter('.hero, .sec', host);
  return { dispose() { l.stop(); S3.dispose(); removeEventListener('resize', onR); } };
}
