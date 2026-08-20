import { esc, fmt, go, local, enter, topicColor, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas } from '../../../core/g3d.js';
import { sec, bento, orbit, drawer, table, pill, rate } from '../kit.js';

// 星域版时间轴：一条带辉光的星河。横拖框选一段，立刻给这段的合计 —— 这是它的功能价值。
export async function render(host) {
  const days = D.days(), all = D.A().sessions;
  const byDay = new Map();
  for (const s of all) { if (!byDay.has(s.d)) byDay.set(s.d, []); byDay.get(s.d).push(s); }
  let range = 60, showMach = false, sel = null;

  host.innerHTML = `
${sec('星河', '每行一天，横轴 00:00→24:00（悉尼）。<b>在图上竖着拖动可以框选一段区间</b>，双击进那一天。')}
<div class="ctl">
  <select id="range"><option value="30">最近 30 天</option><option value="60" selected>最近 60 天</option>
    <option value="90">最近 90 天</option><option value="0">全部 ${days.length} 天</option></select>
  <button id="mach" aria-pressed="false">画上机器扇出</button>
  <button id="clear">清除框选</button>
  <span class="pill" id="hud">未框选</span>
</div>
<canvas class="viz" id="cv"></canvas>
<div id="sum"></div>`;

  const cv = host.querySelector('#cv'), hud = host.querySelector('#hud');
  let rows = [], drag = null;
  const css = k => getComputedStyle(document.body).getPropertyValue(k).trim();

  const draw = () => {
    rows = (range ? days.slice(-range) : days).slice().reverse();
    const rowH = 16, padL = 86, padT = 22;
    const { ctx, w } = fitCanvas(cv, padT + rows.length * rowH + 12);
    const h = padT + rows.length * rowH + 12;
    ctx.clearRect(0, 0, w, h);
    ctx.font = '10.5px -apple-system, system-ui, sans-serif';
    ctx.strokeStyle = css('--line2'); ctx.fillStyle = css('--dim2');
    for (let hh = 0; hh <= 24; hh += 3) {
      const x = padL + (hh / 24) * (w - padL - 16);
      ctx.beginPath(); ctx.moveTo(x, padT - 6); ctx.lineTo(x, h); ctx.stroke();
      ctx.fillText(String(hh).padStart(2, '0') + ':00', x + 3, padT - 10);
    }
    ctx.globalCompositeOperation = S.mode === 'dark' ? 'lighter' : 'source-over';
    rows.forEach((d, i) => {
      const y = padT + i * rowH;
      const inSel = sel && d.d >= sel[0] && d.d <= sel[1];
      if (inSel) { ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = css('--line2');
        ctx.fillRect(0, y, w, rowH); ctx.globalCompositeOperation = S.mode === 'dark' ? 'lighter' : 'source-over'; }
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = inSel ? css('--fg') : css('--dim2');
      ctx.fillText(d.d.slice(5), 8, y + rowH - 5);
      ctx.fillStyle = css('--dim2');
      ctx.fillText(String(d.human).padStart(3), 54, y + rowH - 5);
      ctx.globalCompositeOperation = S.mode === 'dark' ? 'lighter' : 'source-over';
      for (const s of (byDay.get(d.d) || [])) {
        if (!showMach && s.k !== 'human') continue;
        const lt = local(s.t);
        const x = padL + ((lt.getUTCHours() + lt.getUTCMinutes() / 60) / 24) * (w - padL - 16);
        const r = Math.min(5.4, 1.4 + Math.sqrt(Math.max(1, s.u)) * 1.05);
        const c = s.tp[0] ? topicColor(s.tp[0]) : css('--dim2');
        const g = ctx.createRadialGradient(x, y + rowH / 2, 0, x, y + rowH / 2, r * 3.2);
        g.addColorStop(0, c); g.addColorStop(1, 'transparent');
        ctx.globalAlpha = s.k === 'human' ? (sel && !inSel ? .12 : .34) : .1;
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y + rowH / 2, r * 3.2, 0, 6.2832); ctx.fill();
        ctx.globalAlpha = s.k === 'human' ? (sel && !inSel ? .3 : .95) : .25;
        ctx.fillStyle = c; ctx.beginPath(); ctx.arc(x, y + rowH / 2, r, 0, 6.2832); ctx.fill();
      }
    });
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
  };

  const rowAt = cy => {
    const r = cv.getBoundingClientRect();
    return rows[Math.max(0, Math.min(rows.length - 1, Math.floor((cy - r.top - 22) / 16)))];
  };
  cv.addEventListener('pointerdown', e => { drag = rowAt(e.clientY); cv.setPointerCapture(e.pointerId);
    sel = [drag.d, drag.d]; draw(); sum(); });
  cv.addEventListener('pointermove', e => { if (!drag) return;
    const b = rowAt(e.clientY);
    sel = [drag.d < b.d ? drag.d : b.d, drag.d < b.d ? b.d : drag.d]; draw(); sum(); });
  cv.addEventListener('pointerup', () => { drag = null; });
  cv.addEventListener('dblclick', e => { const r = rowAt(e.clientY); if (r) go('day', r.d); });

  const sum = () => {
    if (!sel) { hud.textContent = '未框选'; host.querySelector('#sum').innerHTML = ''; return; }
    const list = D.sessions({ kind: showMach ? 'all' : 'human', from: sel[0], to: sel[1] });
    const agg = D.aggregate(list);
    const nd = days.filter(d => d.d >= sel[0] && d.d <= sel[1]).length;
    hud.textContent = `${sel[0]} → ${sel[1]}　${nd} 天　${agg.n} 场`;
    host.querySelector('#sum').innerHTML = bento([
      { k: '框选区间', v: `<span style="font-size:22px">${sel[0]} → ${sel[1]}</span>`, n: `${nd} 天`, w: 3, tone: 'acc' },
      { k: '会话', v: String(agg.n), n: `你说话 ${agg.turns} 次 · 工具 ${agg.tools} 次`, w: 3, alt: true },
      { k: 'token 输入(含缓存)', v: fmt(agg.input_total), n: `命中率 ${rate(agg.hit)}` },
      { k: '未分类', v: String(agg.unclassified), n: '如实留空' },
    ]) + `${sec('这段区间的主题')}${orbit(agg.topics.map(([t, n]) =>
      ({ k: t, v: n, c: topicColor(t) })))}`;
    enter('.card, .orow', host);
  };

  host.querySelector('#range').onchange = e => { range = +e.target.value; draw(); };
  host.querySelector('#mach').onclick = e => {
    showMach = e.currentTarget.getAttribute('aria-pressed') !== 'true';
    e.currentTarget.setAttribute('aria-pressed', String(showMach)); draw(); sum();
  };
  host.querySelector('#clear').onclick = () => { sel = null; draw(); sum(); };
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.sec', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
