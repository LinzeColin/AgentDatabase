import { esc, fmt, go, enter, topicColor, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { flyToDay } from '../shell.js';
import { hero, sec, grid, orbit, drawer, table, pill, rate } from '../kit.js';

// 时间光谱：横轴是时间，纵向堆的是「那一周在做什么」的成分。
// 看的是**配比怎么变**，不是总量涨没涨 —— 总量在星历那一屏。
export async function render(host) {
  const days = D.days();
  const { weeks, names } = D.topicSeries();
  let stackMode = 'share', range = 0, sel = null;

  host.innerHTML = `
${hero('光谱', '你的注意力是怎么挪的', `一列＝一周。柱子里每一段是一个主题。
  看的是<b>配比</b>：哪一块在长、哪一块在退。横着拖可以框一段时间。`)}
<div class="ctl">
  <button data-sm="share" aria-pressed="true">看配比</button>
  <button data-sm="count" aria-pressed="false">看绝对量</button>
  <select id="range"><option value="0" selected>全部 ${weeks.length} 周</option>
    <option value="26">最近 26 周</option><option value="13">最近 13 周</option>
    <option value="8">最近 8 周</option></select>
  <button id="clear">清掉框选</button>
  <span class="pill" id="hud">没框</span>
</div>
<canvas class="viz" id="cv"></canvas>
<p class="hint">一次对话最多算三个主题，所以配比之和可以超过会话数。一个关键词都没对上的算「没认出来」，
  照实留着，不硬塞进某一类。</p>
<div id="sum"></div>`;

  const cv = host.querySelector('#cv'), hud = host.querySelector('#hud');
  let cols = [], geom = null, drag = null;

  const draw = () => {
    cols = range ? weeks.slice(-range) : weeks;
    const h = Math.max(300, Math.min(520, innerHeight - 420));
    const { ctx, w } = fitCanvas(cv, h);
    const padL = 44, padB = 26, padT = 14;
    const cw = (w - padL - 14) / Math.max(1, cols.length);
    geom = { padL, cw };
    ctx.clearRect(0, 0, w, h);
    const maxN = Math.max(1, ...cols.map(c => names.reduce((a, t) => a + (c.count[t] || 0), 0)));

    ctx.strokeStyle = cssVar('--line2'); ctx.fillStyle = cssVar('--dim2');
    ctx.font = '10px -apple-system, system-ui, sans-serif';
    for (let g = 0; g <= 4; g++) {
      const y = padT + (h - padT - padB) * (g / 4);
      ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w - 14, y); ctx.stroke();
      const v = stackMode === 'share' ? `${100 - g * 25}%` : fmt(Math.round(maxN * (1 - g / 4)));
      ctx.fillText(v, 6, y + 3);
    }

    cols.forEach((c, i) => {
      const tot = names.reduce((a, t) => a + (c.count[t] || 0), 0);
      if (!tot) return;
      const scale = stackMode === 'share' ? (h - padT - padB) / tot : (h - padT - padB) / maxN;
      const inSel = sel && i >= sel[0] && i <= sel[1];
      let y = h - padB;
      for (const t of names) {
        const n = c.count[t] || 0; if (!n) continue;
        const bh = n * scale;
        ctx.globalAlpha = sel && !inSel ? .22 : .92;
        ctx.fillStyle = topicColor(t);
        ctx.fillRect(padL + i * cw + .6, y - bh, Math.max(1.2, cw - 1.6), bh);
        y -= bh;
      }
      ctx.globalAlpha = 1;
      if (cw > 26 || i % Math.ceil(26 / Math.max(1, cw)) === 0) {
        ctx.fillStyle = inSel ? cssVar('--fg') : cssVar('--dim2');
        ctx.save(); ctx.translate(padL + i * cw + cw / 2, h - 8); ctx.rotate(-0.6);
        ctx.fillText(c.w.slice(2), 0, 0); ctx.restore();
      }
    });
  };

  const colAt = cx => {
    const r = cv.getBoundingClientRect();
    if (!geom) return 0;
    return Math.max(0, Math.min(cols.length - 1, Math.floor((cx - r.left - geom.padL) / geom.cw)));
  };
  cv.addEventListener('pointerdown', e => {
    drag = colAt(e.clientX); sel = [drag, drag];
    cv.setPointerCapture(e.pointerId); draw(); sum();
  });
  cv.addEventListener('pointermove', e => {
    if (drag == null) return;
    const b = colAt(e.clientX); sel = [Math.min(drag, b), Math.max(drag, b)]; draw(); sum();
  });
  cv.addEventListener('pointerup', () => { drag = null; });
  cv.addEventListener('dblclick', e => {
    const c = cols[colAt(e.clientX)]; if (c) go('day', c.w);
  });

  const sum = () => {
    if (!sel || !cols.length) { hud.textContent = '没框'; host.querySelector('#sum').innerHTML = ''; return; }
    const a = cols[sel[0]], b = cols[sel[1]];
    const from = a.w, to = days.filter(d => d.d <= addDays(b.w, 6)).slice(-1)[0]?.d || b.w;
    flyToDay(from);
    const list = D.sessions({ kind: 'human', from, to });
    const agg = D.aggregate(list);
    hud.textContent = `${from} → ${to}　${sel[1] - sel[0] + 1} 周　${agg.n} 场`;
    host.querySelector('#sum').innerHTML = grid([
      { k: '框到的区间', v: `<span style="font-size:21px">${from} → ${to}</span>`,
        n: `${sel[1] - sel[0] + 1} 周`, w: 3, tone: 'acc' },
      { k: '你开口', v: String(agg.n), n: `说话 ${agg.turns} 次 · 用工具 ${agg.tools} 次`, w: 3, alt: true },
      { k: '读进 token', v: fmt(agg.input_total), n: `命中缓存 ${rate(agg.hit)}` },
      { k: '没认出来的', v: String(agg.unclassified), n: '照实留空' },
    ]) + sec('这段时间在做什么')
      + orbit(agg.topics.map(([t, n]) => ({ k: t, v: n, c: topicColor(t), attr: `data-topic="${esc(t)}"` })));
    enter('.cell, .orow', host);
  };

  function addDays(iso, n) {
    const t = new Date(iso + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + n);
    return t.toISOString().slice(0, 10);
  }

  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-sm]'); if (!b) return;
    stackMode = b.dataset.sm;
    host.querySelectorAll('[data-sm]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.sm === stackMode)));
    draw();
  });
  host.querySelector('#range').onchange = e => { range = +e.target.value; sel = null; draw(); sum(); };
  host.querySelector('#clear').onclick = () => { sel = null; draw(); sum(); };
  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });

  host.insertAdjacentHTML('beforeend', sec('主题一览') + orbit(names.map(t => ({
    k: t, v: weeks.reduce((a, w) => a + (w.count[t] || 0), 0), c: topicColor(t),
    attr: `data-topic="${esc(t)}"`,
  })).sort((a, b) => b.v - a.v)));

  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.hero, .sec, .orow', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
