import { esc, fmt, go, local, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas } from '../../../core/g3d.js';
import { sec, lede, p, n, big, aside, figure, rank, table, rate } from '../kit.js';

// 手记版时间轴：一条一条的墨点行。竖着拖能框选一段，立刻给这段的合计。
export async function render(host) {
  const days = D.days(), all = D.A().sessions;
  const byDay = new Map();
  for (const s of all) { if (!byDay.has(s.d)) byDay.set(s.d, []); byDay.get(s.d).push(s); }
  let range = 60, sel = null;

  host.innerHTML = `
${sec('时间轴')}
${lede(`每一行是一天，从左到右是那天的 ${n('00:00')} 到 ${n('24:00')}（悉尼时间）。
  每一个墨点是一场会话，点越大表示你在那场里说得越多。`)}
${aside('在图上竖着拖动可以框选一段区间，双击某一行进那一天。')}
<div class="ctl">
  <select id="range"><option value="30">最近 30 天</option><option value="60" selected>最近 60 天</option>
    <option value="90">最近 90 天</option><option value="0">全部 ${days.length} 天</option></select>
  <button id="clear">清除框选</button><span id="hud"></span>
</div>
${figure('<canvas class="viz" id="cv"></canvas>', '横轴为一天 24 小时，纵轴为日期（新在上）。')}
<div id="sum"></div>`;

  const cv = host.querySelector('#cv'), hud = host.querySelector('#hud');
  let rows = [], drag = null;
  const css = k => getComputedStyle(document.body).getPropertyValue(k).trim();
  const draw = () => {
    rows = (range ? days.slice(-range) : days).slice().reverse();
    const rowH = 14, padL = 74, padT = 20;
    const { ctx, w } = fitCanvas(cv, padT + rows.length * rowH + 10);
    const h = padT + rows.length * rowH + 10;
    ctx.clearRect(0, 0, w, h);
    ctx.font = '10px -apple-system, system-ui, sans-serif';
    ctx.strokeStyle = css('--rule2'); ctx.fillStyle = css('--dim2');
    for (let hh = 0; hh <= 24; hh += 6) {
      const x = padL + (hh / 24) * (w - padL - 12);
      ctx.beginPath(); ctx.moveTo(x, padT - 5); ctx.lineTo(x, h); ctx.stroke();
      ctx.fillText(String(hh).padStart(2, '0') + ':00', x + 3, padT - 9);
    }
    rows.forEach((d, i) => {
      const y = padT + i * rowH;
      const inSel = sel && d.d >= sel[0] && d.d <= sel[1];
      if (inSel) { ctx.fillStyle = css('--rule2'); ctx.fillRect(0, y, w, rowH); }
      ctx.fillStyle = inSel ? css('--fg') : css('--dim2');
      ctx.fillText(d.d.slice(5), 8, y + rowH - 4);
      ctx.fillText(String(d.human).padStart(3), 46, y + rowH - 4);
      for (const s of (byDay.get(d.d) || [])) {
        if (s.k !== 'human') continue;
        const lt = local(s.t);
        const x = padL + ((lt.getUTCHours() + lt.getUTCMinutes() / 60) / 24) * (w - padL - 12);
        const r = Math.min(4.6, 1.2 + Math.sqrt(Math.max(1, s.u)) * .95);
        ctx.globalAlpha = sel && !inSel ? .22 : .82;
        ctx.fillStyle = s.tp[0] ? topicColor(s.tp[0]) : css('--dim2');
        ctx.beginPath(); ctx.arc(x, y + rowH / 2, r, 0, 6.2832); ctx.fill();
      }
      ctx.globalAlpha = 1;
    });
  };
  const rowAt = cy => {
    const r = cv.getBoundingClientRect();
    return rows[Math.max(0, Math.min(rows.length - 1, Math.floor((cy - r.top - 20) / 14)))];
  };
  cv.addEventListener('pointerdown', e => { drag = rowAt(e.clientY); cv.setPointerCapture(e.pointerId);
    sel = [drag.d, drag.d]; draw(); sum(); });
  cv.addEventListener('pointermove', e => { if (!drag) return;
    const b = rowAt(e.clientY);
    sel = [drag.d < b.d ? drag.d : b.d, drag.d < b.d ? b.d : drag.d]; draw(); sum(); });
  cv.addEventListener('pointerup', () => { drag = null; });
  cv.addEventListener('dblclick', e => { const r = rowAt(e.clientY); if (r) go('day', r.d); });
  const sum = () => {
    if (!sel) { hud.textContent = ''; host.querySelector('#sum').innerHTML = ''; return; }
    const list = D.sessions({ kind: 'human', from: sel[0], to: sel[1] });
    const agg = D.aggregate(list);
    const nd = days.filter(d => d.d >= sel[0] && d.d <= sel[1]).length;
    hud.textContent = `${sel[0]} → ${sel[1]}`;
    host.querySelector('#sum').innerHTML = sec('框选的这一段')
      + p(`${n(sel[0])} 到 ${n(sel[1])}，${n(nd)} 天里你开了 ${big(agg.n)} 场会话，
        说话 ${n(agg.turns)} 次，工具被调用 ${n(agg.tools)} 次，
        读进 ${n(agg.input_total)} 个 token，命中率 ${rate(agg.hit)}，其中 ${n(agg.unclassified)} 场未分类。`)
      + figure(rank(agg.topics.map(([t, v]) => ({ k: t, v, label: String(v) }))), '这段区间的主题构成。');
    enter('figure, p.body', host);
  };
  host.querySelector('#range').onchange = e => { range = +e.target.value; draw(); };
  host.querySelector('#clear').onclick = () => { sel = null; draw(); sum(); };
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.sec, p.body, figure, .aside', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
