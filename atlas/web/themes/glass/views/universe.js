import { esc, fmt, go, KIND_COLORS, topicColor, reduced, enter, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { forceLayout, loop } from '../../../core/g3d.js';
import { buildGraphScene } from '../../../core/scene3d.js';
import { sec, orbit, drawer, table, warn, pill } from '../kit.js';

// 真 WebGL 3D：three.js 本地 vendor（CSP 的 script-src 'self' 只挡 CDN，vendor 完全合法）。
// 实例化网格 + 光照 + 雾 + 加色辉光，材质按主题给不同配置 —— 同一份几何，三种质感。
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

  host.innerHTML = `${sec('耦合星图', '真 WebGL 场景：实例化网格 + 光照 + 加色辉光。悬停任一节点，只留它和它的邻居 —— 耦合关系直接看得见。')}
<div class="ctl">
  <button id="spin" aria-pressed="true">自转</button>
  <button id="reset">重置视角</button>
  <span class="pill" id="hud">节点 ${C.nodes.length} · 边 ${C.edges.length}</span>
</div>
<canvas class="viz" id="cv" role="img" aria-label="来源、项目、主题的关联网络图。连得最紧的组合见下方表格。"></canvas>
<p class="hint">拖动转视角，滚轮推拉，点一个节点进网格。${esc(C.note)}${C.dropped_edges ? `　丢弃弱边 ${C.dropped_edges} 条。` : ''}</p>
${warn('<b>颜色只是辅助。</b>三类节点在下面的抽屉里都有名字和度数，不靠颜色也能读出来。')}
<div id="near"></div>
${drawer('展开最紧的 40 组耦合', table([{ t: 'A' }, { t: 'B' }, { t: '共同出现', r: true }],
  edges.slice(0, 40).map(e => {
    const a = byId.get(e.a), b = byId.get(e.b);
    return [`${pill(a ? a.kind : '')} ${esc(a ? a.label : e.a)}`,
            `${pill(b ? b.kind : '')} ${esc(b ? b.label : e.b)}`, String(e.w)];
  })))}`;

  const cv = host.querySelector('#cv');
  cv.style.height = Math.max(460, Math.min(760, innerHeight - 250)) + 'px';
  const hud = host.querySelector('#hud'), nearBox = host.querySelector('#near');
  let spin = true, last = performance.now(), dragging = null, cur = -1;

  const S3 = buildGraphScene(cv, nodes, edges, { theme: S.theme });

  cv.addEventListener('pointerdown', e => {
    dragging = { x: e.clientX, y: e.clientY, yaw: S3.orbit.yaw, pitch: S3.orbit.pitch };
    cv.setPointerCapture(e.pointerId);
  });
  cv.addEventListener('pointermove', e => {
    S3.setPointer(e.clientX, e.clientY);
    if (!dragging) return;
    S3.orbit.yaw = dragging.yaw - (e.clientX - dragging.x) * 0.006;
    S3.orbit.pitch = Math.max(-1.4, Math.min(1.4, dragging.pitch + (e.clientY - dragging.y) * 0.005));
  });
  cv.addEventListener('pointerup', () => { dragging = null; });
  cv.addEventListener('pointerleave', () => { dragging = null; S3.clearPointer(); });
  cv.addEventListener('wheel', e => {
    e.preventDefault();
    S3.orbit.dist = Math.max(280, Math.min(3200, S3.orbit.dist * (e.deltaY > 0 ? 1.09 : 0.92)));
  }, { passive: false });
  cv.addEventListener('click', () => {
    const i = S3.hovered();
    if (i < 0) return;
    const n = nodes[i];
    go('grid', (n.kind === 'topic' ? 't=' : n.kind === 'project' ? 'p=' : 's=') + encodeURIComponent(n.label));
  });

  const btn = (id, fn) => { const b = host.querySelector(id); if (b) b.addEventListener('click', e => {
    const on = e.currentTarget.getAttribute('aria-pressed') !== 'true';
    e.currentTarget.setAttribute('aria-pressed', String(on)); fn(on); }); };
  btn('#spin', v => { spin = v; });
  const rst = host.querySelector('#reset');
  if (rst) rst.addEventListener('click', () => { S3.orbit.yaw = -0.6; S3.orbit.pitch = 0.30; S3.orbit.dist = 820; });

  const l = loop(now => {
    const dt = Math.min(64, now - last); last = now;
    const i = S3.tick(dt, spin && !dragging && !reduced());
    cv.style.cursor = i >= 0 ? 'pointer' : 'grab';
    if (i === cur) return;
    cur = i;
    if (i < 0) { hud.textContent = `节点 ${nodes.length} · 边 ${edges.length}`; return; }
    const n = nodes[i];
    hud.textContent = `${n.label} · 度数 ${(adj.get(n.id) || new Set()).size} · 出现 ${n.w} 场`;
    if (nearBox) {
      nearBox.innerHTML = `<p class="hint" style="margin-top:18px"><b style="color:var(--fg)">${esc(n.label)}</b> 连着这些：</p>` +
        orbit(D.neighbours(n.id).slice(0, 10).map(x => {
          const nn = byId.get(x.id);
          return { k: nn ? nn.label : x.id, v: x.w, label: String(x.w),
                   c: nn && nn.kind === 'topic' ? topicColor(nn.label) : 'var(--acc)' };
        }));
    }
  });

  const onR = () => {
    cv.style.height = Math.max(460, Math.min(760, innerHeight - 250)) + 'px';
    S3.resize();
  };
  addEventListener('resize', onR);
  enter('.sec, .card', host);
  return { dispose() { l.stop(); S3.dispose(); removeEventListener('resize', onR); } };
}
