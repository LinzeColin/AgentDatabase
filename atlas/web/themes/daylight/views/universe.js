import { esc, fmt, go, enter, topicColor, KIND_COLORS } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { hero, sec, orbit, drawer, table, pill } from '../kit.js';

// 白昼不画 3D。同一份耦合数据在这里摊成**邻接矩阵**：
// 行和列是同一批点，格子越黑＝这两样越常一起出现。
// 点线图好看但会重叠、会打结；矩阵不会 —— 三个主题各用各的强项，不是同一张图换皮。
export async function render(host) {
  const C = D.coupling();
  const byId = new Map(C.nodes.map(n => [n.id, n]));
  let kindFilter = 'all', order = 'weight', hov = null;

  host.innerHTML = `
${hero('耦合', '谁和谁总是一起出现', `行和列是同一批东西：来源、项目、主题。
  格子越黑，说明这两样在同一次对话里同时出现得越多。<b>3D 星图在「星云宇宙」主题里</b> ——
  白昼把它摊成矩阵，因为矩阵不会打结。`)}
<div class="ctl">
  <select id="kind"><option value="all">全部三类</option><option value="topic">只看主题</option>
    <option value="project">只看项目</option><option value="source">只看来源</option></select>
  <select id="order"><option value="weight">按出现次数排</option><option value="name">按名字排</option>
    <option value="cluster">按抱团排</option></select>
  <span class="pill" id="hud">${C.nodes.length} 个点 · ${C.edges.length} 条边</span>
</div>
<canvas class="viz" id="mx"></canvas>
<p class="hint">停在任一格看这两样同时出现了几次；点一下进那一边的明细。
  ${C.dropped_edges ? `另有 ${C.dropped_edges} 组太弱的关联没画出来 —— 是弱，不是没有。` : ''}</p>
<div id="near"></div>
${drawer('连得最紧的 40 组', table([{ t: '一头' }, { t: '另一头' }, { t: '同时出现', r: true }],
  C.edges.slice(0, 40).map(e => {
    const a = byId.get(e.a), b = byId.get(e.b);
    return [`${pill(a ? a.kind : '')} ${esc(a ? a.label : e.a)}`,
            `${pill(b ? b.kind : '')} ${esc(b ? b.label : e.b)}`, String(e.w)];
  })))}`;

  const cv = host.querySelector('#mx'), hud = host.querySelector('#hud');
  let rows = [], G = null;
  const W = new Map();
  const key = (a, b) => a < b ? a + ' ' + b : b + ' ' + a;
  for (const e of C.edges) W.set(key(e.a, e.b), e.w);

  const build = () => {
    let ns = C.nodes.filter(n => kindFilter === 'all' || n.kind === kindFilter);
    if (order === 'name') ns.sort((a, b) => a.label.localeCompare(b.label, 'zh'));
    else if (order === 'cluster') {
      // 抱团排：贪心地把「和已排好的那些连得最紧」的点接在后面。
      // 这会把互相咬合的一簇挤到对角线附近 —— 矩阵能看出结构，全靠这一步。
      const pool = ns.slice().sort((a, b) => b.w - a.w);
      const out = [pool.shift()].filter(Boolean);
      while (pool.length) {
        let best = 0, bs = -1;
        pool.forEach((c, i) => {
          const s = out.reduce((a, o) => a + (W.get(key(o.id, c.id)) || 0), 0);
          if (s > bs) { bs = s; best = i; }
        });
        out.push(pool.splice(best, 1)[0]);
      }
      ns = out;
    } else ns.sort((a, b) => b.w - a.w);
    rows = ns.slice(0, 34);
  };

  const draw = () => {
    build();
    const n = rows.length;
    const labelW = 128, top = 108, pad = 10;
    const availW = Math.max(240, cv.clientWidth || 900) - labelW - pad;
    const cell = Math.max(9, Math.min(24, availW / Math.max(1, n)));
    const H = top + n * cell + pad;
    const { ctx, w } = fitCanvas(cv, H);
    G = { labelW, top, cell, n };
    ctx.clearRect(0, 0, w, H);
    const mx = Math.max(1, ...C.edges.map(e => e.w));

    ctx.font = '10px ui-monospace, SF Mono, Menlo, monospace';
    rows.forEach((c, j) => {                       // 列标题竖排
      ctx.save();
      ctx.translate(labelW + j * cell + cell * 0.72, top - 6);
      ctx.rotate(-Math.PI / 2);
      ctx.fillStyle = hov && hov.j === j ? cssVar('--acc') : cssVar('--dim2');
      ctx.fillText(c.label.slice(0, 12), 0, 0);
      ctx.restore();
    });
    rows.forEach((r, i) => {
      const y = top + i * cell;
      ctx.fillStyle = hov && hov.i === i ? cssVar('--acc') : cssVar('--fg');
      ctx.font = '11px -apple-system, system-ui, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(r.label.slice(0, 14), labelW - 8, y + cell * 0.74);
      ctx.textAlign = 'left';
      rows.forEach((c, j) => {
        if (i === j) {                              // 对角线：这一样自己出现了多少次
          ctx.fillStyle = cssVar('--hair');
          ctx.fillRect(labelW + j * cell + 0.5, y + 0.5, cell - 1, cell - 1);
          return;
        }
        const v = W.get(key(r.id, c.id)) || 0;
        if (!v) return;
        ctx.globalAlpha = 0.16 + (v / mx) * 0.84;
        ctx.fillStyle = r.kind === 'topic' ? topicColor(r.label) : (KIND_COLORS[r.kind] || cssVar('--fg'));
        ctx.fillRect(labelW + j * cell + 0.5, y + 0.5, cell - 1, cell - 1);
        ctx.globalAlpha = 1;
      });
    });
    if (hov) {                                      // 十字准星：发丝线，不是高亮块
      ctx.strokeStyle = cssVar('--acc'); ctx.lineWidth = 1;
      ctx.strokeRect(labelW + hov.j * cell - 0.5, top - 0.5, cell + 1, n * cell + 1);
      ctx.strokeRect(labelW - 0.5, top + hov.i * cell - 0.5, n * cell + 1, cell + 1);
    }
  };

  let nearId = null;
  const near = n => {
    if (nearId === n.id) return;
    nearId = n.id;
    host.querySelector('#near').innerHTML = sec(`${n.label} 连着这些`)
      + orbit(D.neighbours(n.id).slice(0, 10).map(x => {
        const nn = byId.get(x.id);
        return { k: nn ? nn.label : x.id, v: x.w, label: String(x.w) };
      }));
  };

  cv.addEventListener('pointermove', e => {
    if (!G) return;
    const b = cv.getBoundingClientRect();
    const i = Math.floor((e.clientY - b.top - G.top) / G.cell);
    const j = Math.floor((e.clientX - b.left - G.labelW) / G.cell);
    if (i >= 0 && i < G.n && j >= 0 && j < G.n) {
      hov = { i, j };
      const v = i === j ? rows[i].w : (W.get(key(rows[i].id, rows[j].id)) || 0);
      hud.textContent = i === j
        ? `${rows[i].label} 自己出现 ${rows[i].w} 次`
        : `${rows[i].label} 和 ${rows[j].label} 同时出现 ${v} 次`;
      cv.style.cursor = 'pointer';
      near(rows[i]);
    } else {
      hov = null; cv.style.cursor = 'default';
      hud.textContent = `${C.nodes.length} 个点 · ${C.edges.length} 条边`;
    }
    draw();
  });
  cv.addEventListener('pointerleave', () => { hov = null; draw(); });
  cv.addEventListener('click', () => {
    if (!hov) return;
    const n = rows[hov.i];
    go('grid', (n.kind === 'topic' ? 't=' : n.kind === 'project' ? 'p=' : 's=') + encodeURIComponent(n.label));
  });

  host.querySelector('#kind').onchange = e => { kindFilter = e.target.value; draw(); };
  host.querySelector('#order').onchange = e => { order = e.target.value; draw(); };
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.hero, .sec', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
