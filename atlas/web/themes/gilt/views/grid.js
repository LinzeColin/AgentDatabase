import { esc, fmt, go, enter, topicColor, local } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { hero, sec, orbit, drawer, table } from '../kit.js';

// 白昼的网格是一张**印刷表**：行是分类、列是周、格子是深浅。没有辉光，靠密度说话。
export async function render(host, arg) {
  const A = D.A();
  const q = new URLSearchParams((arg || '').replace(/^\?/, ''));
  let rowMode = q.get('p') ? 'project' : q.get('s') ? 'source' : 'topic';
  let metric = 'sessions', cur = null;
  const focus = q.get('t') || q.get('p') || q.get('s') || '';

  const weeks = A.trend.weeks.filter(w => w.human > 0).map(w => w.w);
  const wIdx = new Map(weeks.map((w, i) => [w, i]));

  host.innerHTML = `
${hero('网格', '哪一类活，哪一周在烧', `一行一类，一列一周，${weeks.length} 周全在这一屏里。
  格子越深＝那周在这类活上花得越多。${focus ? `　现在盯着：<b>${esc(focus)}</b>` : ''}`)}
<div class="ctl">
  <select id="rowmode"><option value="topic">按主题</option><option value="project">按项目</option>
    <option value="source">按来源</option></select>
  <select id="metric"><option value="sessions">按会话数</option><option value="tokens">按新 token</option></select>
  <span class="pill" id="hud"></span>
</div>
<canvas class="viz" id="mx" role="img" aria-label="分类 × 周的强度矩阵。合计与逐行明细见下方表格。"></canvas>
<p class="hint">最右一列是整行合计。新 token＝真正读进去的加吐出来的，<b>不含缓存命中</b> ——
  缓存那部分是重复读同一段，算进去会把量吹大十倍以上。</p>
<div id="side"></div>`;
  host.querySelector('#rowmode').value = rowMode;

  function isoWeek(d) {
    const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
    const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day);
    const y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
    return `${t.getUTCFullYear()}-W${String(Math.ceil(((t - y0) / 864e5 + 1) / 7)).padStart(2, '0')}`;
  }
  function rowsOf() {
    const byKey = new Map();
    for (const s of D.sessions({ kind: 'human' })) {
      const wk = isoWeek(local(s.t));
      if (!wIdx.has(wk)) continue;
      const keys = rowMode === 'topic' ? (s.tp.length ? s.tp : ['没认出来'])
        : rowMode === 'project' ? [s.p || '没标项目'] : [s.s];
      for (const k of keys) {
        if (!byKey.has(k)) byKey.set(k, { key: k, cells: new Array(weeks.length).fill(0),
          tok: new Array(weeks.length).fill(0), total: 0, tokTotal: 0 });
        const r = byKey.get(k);
        r.cells[wIdx.get(wk)] += 1; r.tok[wIdx.get(wk)] += s.ti + s.to;
        r.total += 1; r.tokTotal += s.ti + s.to;
      }
    }
    return [...byKey.values()].sort((a, b) => b.total - a.total).slice(0, 22);
  }

  const cv = host.querySelector('#mx'), hud = host.querySelector('#hud');
  const G = { labelW: 142, padT: 30, rowH: 20, padR: 82 };
  let rows = [];

  const draw = () => {
    rows = rowsOf();
    const H = G.padT + rows.length * G.rowH + 14;
    const { ctx, w } = fitCanvas(cv, H);
    ctx.clearRect(0, 0, w, H);
    const cw = (w - G.labelW - G.padR) / Math.max(1, weeks.length);
    const val = (r, i) => metric === 'tokens' ? r.tok[i] : r.cells[i];
    const mx = Math.max(1, ...rows.flatMap(r => weeks.map((_, i) => val(r, i))));

    ctx.font = '9.5px ui-monospace, SF Mono, Menlo, monospace';
    ctx.fillStyle = cssVar('--dim2');
    const step = Math.max(1, Math.ceil(weeks.length / 12));
    weeks.forEach((wk, i) => { if (i % step === 0) ctx.fillText(wk.slice(2), G.labelW + i * cw, G.padT - 10); });
    ctx.strokeStyle = cssVar('--hair'); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, G.padT - 4); ctx.lineTo(w, G.padT - 4); ctx.stroke();

    rows.forEach((r, ri) => {
      const y = G.padT + ri * G.rowH;
      const dim = focus && r.key !== focus;
      ctx.fillStyle = dim ? cssVar('--dim2') : cssVar('--fg');
      ctx.font = (focus && r.key === focus ? '600 ' : '') + '11px -apple-system, system-ui, sans-serif';
      ctx.fillText(r.key.slice(0, 16), 4, y + G.rowH * 0.72);
      weeks.forEach((wk, i) => {
        const v = val(r, i); if (!v) return;
        ctx.globalAlpha = dim ? (0.1 + (v / mx) * 0.3) : (0.14 + (v / mx) * 0.86);
        ctx.fillStyle = rowMode === 'topic' ? topicColor(r.key) : cssVar('--fg');
        ctx.fillRect(G.labelW + i * cw + 0.5, y + 3, Math.max(1.2, cw - 1), G.rowH - 7);
      });
      ctx.globalAlpha = 1;
      ctx.fillStyle = cssVar('--dim2'); ctx.font = '10px ui-monospace, SF Mono, Menlo, monospace';
      ctx.fillText(metric === 'tokens' ? fmt(r.tokTotal) : String(r.total), w - G.padR + 8, y + G.rowH * 0.72);
    });
    hud.textContent = `${rows.length} 行 · ${weeks.length} 周`;
    side();
  };

  const side = () => {
    const tk = metric === 'tokens' ? 'tokTotal' : 'total';
    host.querySelector('#side').innerHTML = sec('整段时间的合计')
      + orbit(rows.map(r => ({ k: r.key, v: r[tk],
          label: metric === 'tokens' ? fmt(r.tokTotal) : String(r.total),
          attr: rowMode === 'topic' ? `data-topic="${esc(r.key)}"` : '' })))
      + drawer('摊开成表', table(
          [{ t: rowMode === 'topic' ? '主题' : rowMode === 'project' ? '项目' : '来源' },
           { t: '会话', r: true }, { t: '新 token', r: true }, { t: '出现过的周', r: true }],
          rows.map(r => [esc(r.key), String(r.total), fmt(r.tokTotal),
            String(r.cells.filter(x => x > 0).length)])));
    enter('.orow', host);
  };

  cv.addEventListener('pointermove', e => {
    const b = cv.getBoundingClientRect();
    const cw = (cv.clientWidth - G.labelW - G.padR) / Math.max(1, weeks.length);
    const ri = Math.floor((e.clientY - b.top - G.padT) / G.rowH);
    const ci = Math.floor((e.clientX - b.left - G.labelW) / cw);
    if (ri >= 0 && ri < rows.length && ci >= 0 && ci < weeks.length) {
      const r = rows[ri];
      cur = { row: r.key, week: weeks[ci] };
      hud.textContent = `${r.key} · ${weeks[ci]} · ${r.cells[ci]} 场 · ${fmt(r.tok[ci])} 新 token`;
      cv.style.cursor = 'pointer';
    } else {
      cur = null; cv.style.cursor = 'default';
      hud.textContent = `${rows.length} 行 · ${weeks.length} 周`;
    }
  });
  cv.addEventListener('pointerleave', () => { cur = null; });
  cv.addEventListener('click', () => {
    if (!cur) return;
    const [y, n] = cur.week.split('-W').map(Number);
    const jan4 = new Date(Date.UTC(y, 0, 4));
    const mon = new Date(jan4);
    mon.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() || 7) - 1) + (n - 1) * 7);
    go('day', mon.toISOString().slice(0, 10));
  });
  host.querySelector('#rowmode').onchange = e => { rowMode = e.target.value; draw(); };
  host.querySelector('#metric').onchange = e => { metric = e.target.value; draw(); };
  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.hero, .sec', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
