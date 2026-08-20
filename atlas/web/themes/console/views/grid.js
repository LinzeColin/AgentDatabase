import { esc, fmt, pct, go, enter, topicColor, local, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { sec, kv, table, meter, spark, warn } from '../kit.js';

// 网格 = 真正的矩阵：行是领域/主题，列是周，格子是强度。
// 上一版只是把会话画成一堆彩色方块，看不出任何结构 —— 那是它被要求重做的原因。
export async function render(host) {
  const A = D.A(), E = A.aei;
  let rowMode = 'domain';     // domain | topic | project | source
  let metric = 'sessions';    // sessions | tokens | automation | success
  let cur = null;
  const css = k => cssVar(k);

  host.innerHTML = `${sec('MATRIX', '行 = 分类，列 = 周，格子越亮＝那一周在这类活上花得越多。这是矩阵，不是散点。')}
<div class="ctl">
  <label>行 <select id="rowmode">
    <option value="domain">主题</option><option value="topic">主题（全部）</option>
    <option value="project">项目</option><option value="source">来源</option></select></label>
  <label>口径 <select id="metric">
    <option value="sessions">会话数</option><option value="tokens">新 token</option></select></label>
  <span class="tag" id="hud"></span>
</div>
<canvas class="viz" id="mx"></canvas>
<p class="hint">悬停任一格看那一周的数。右侧是该行合计。</p>`;

  const weeks = A.trend.weeks.filter(w => w.human > 0).map(w => w.w);
  const wIdx = new Map(weeks.map((w, i) => [w, i]));

  function rowsOf() {
    const sess = D.sessions({ kind: 'human' });
    const byKey = new Map();
    for (const s of sess) {
      const d = local(s.t); const [iy, iw] = isoWeek(d);
      const wk = `${iy}-W${String(iw).padStart(2, '0')}`;
      if (!wIdx.has(wk)) continue;
      let keys = [];
      if (rowMode === 'topic') keys = s.tp.length ? s.tp : ['未分类'];
      else if (rowMode === 'project') keys = [s.p || '未标注'];
      else if (rowMode === 'source') keys = [s.s];
      else keys = domainsOf(s);
      for (const k of keys) {
        if (!byKey.has(k)) byKey.set(k, { key: k, cells: new Array(weeks.length).fill(0),
          tok: new Array(weeks.length).fill(0), total: 0, tokTotal: 0 });
        const r = byKey.get(k);
        r.cells[wIdx.get(wk)] += 1;
        r.tok[wIdx.get(wk)] += s.ti + s.to;
        r.total += 1; r.tokTotal += s.ti + s.to;
      }
    }
    return [...byKey.values()].sort((a, b) => b.total - a.total).slice(0, 22);
  }
  function isoWeek(d) {
    const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
    const day = t.getUTCDay() || 7;
    t.setUTCDate(t.getUTCDate() + 4 - day);
    const y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
    return [t.getUTCFullYear(), Math.ceil(((t - y0) / 864e5 + 1) / 7)];
  }
  // 领域用 aei 已算好的映射：一场会话的领域在 build 阶段判过，这里不重判
  const domMap = new Map();
  for (const r of (E.domains || [])) domMap.set(r.domain, r);
  function domainsOf(s) {
    // 会话级领域没进 compact 表；用主题做代理并标明
    return s.tp.length ? s.tp.slice(0, 1) : ['未分类'];
  }

  const cv = host.querySelector('#mx');
  let rows = [];
  const draw = () => {
    rows = rowsOf();
    const labelW = 132, padT = 26, rowH = 20, padR = 74;
    const h = padT + rows.length * rowH + 10;
    const { ctx, w } = fitCanvas(cv, h);
    ctx.clearRect(0, 0, w, h);
    const cw = (w - labelW - padR) / Math.max(1, weeks.length);
    const val = (r, i) => metric === 'tokens' ? r.tok[i] : r.cells[i];
    const mx = Math.max(1, ...rows.flatMap(r => weeks.map((_, i) => val(r, i))));
    ctx.font = '10px ui-monospace, monospace';
    ctx.fillStyle = css('--dim2');
    const step = Math.max(1, Math.ceil(weeks.length / 12));
    weeks.forEach((wk, i) => { if (i % step === 0) ctx.fillText(wk.slice(2), labelW + i * cw, padT - 8); });
    rows.forEach((r, ri) => {
      const y = padT + ri * rowH;
      ctx.fillStyle = css('--fg'); ctx.font = '11px ui-monospace, monospace';
      ctx.fillText(r.key.slice(0, 14), 6, y + rowH * .72);
      weeks.forEach((wk, i) => {
        const v = val(r, i); if (!v) return;
        ctx.fillStyle = topicColor(r.key);
        ctx.globalAlpha = 0.12 + (v / mx) * 0.88;
        ctx.fillRect(labelW + i * cw + .5, y + 2.5, Math.max(1, cw - 1), rowH - 5);
      });
      ctx.globalAlpha = 1;
      ctx.fillStyle = css('--dim2'); ctx.font = '10px ui-monospace, monospace';
      ctx.fillText(metric === 'tokens' ? fmt(r.tokTotal) : String(r.total), w - padR + 6, y + rowH * .72);
    });
  };

  cv.addEventListener('pointermove', e => {
    const r0 = cv.getBoundingClientRect();
    const x = e.clientX - r0.left, y = e.clientY - r0.top;
    const labelW = 132, padT = 26, rowH = 20, padR = 74;
    const cw = (cv.clientWidth - labelW - padR) / Math.max(1, weeks.length);
    const ri = Math.floor((y - padT) / rowH), ci = Math.floor((x - labelW) / cw);
    const hud = host.querySelector('#hud');
    if (ri >= 0 && ri < rows.length && ci >= 0 && ci < weeks.length) {
      const r = rows[ri];
      cur = { row: r.key, week: weeks[ci], n: r.cells[ci], tok: r.tok[ci] };
      hud.textContent = `${r.key} · ${weeks[ci]} · ${r.cells[ci]} 场 · ${fmt(r.tok[ci])} 新token`;
    } else { cur = null; hud.textContent = `${rows.length} 行 × ${weeks.length} 周`; }
  });
  cv.addEventListener('pointerleave', () => { cur = null; });
  cv.addEventListener('click', () => { if (cur && rowMode === 'topic') go('grid2', ''); });

  host.querySelector('#rowmode').onchange = e => { rowMode = e.target.value; draw(); };
  host.querySelector('#metric').onchange = e => { metric = e.target.value; draw(); };
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw();
  enter('.sec, .kv > div', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
