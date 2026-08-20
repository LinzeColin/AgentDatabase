import { esc, fmt, go, local, enter, topicColor, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, loop , cssVar } from '../../../core/g3d.js';
import { sec, kv, table, warn, rate } from '../kit.js';

// 之前这一屏只是好看。现在它要能回答问题：拖出一段区间，立刻给这段的合计。
export async function render(host) {
  const days = D.days(), all = D.A().sessions;
  const byDay = new Map();
  for (const s of all) { if (!byDay.has(s.d)) byDay.set(s.d, []); byDay.get(s.d).push(s); }
  let range = 60, showMach = false, sel = null;   // sel = [起日, 止日]

  host.innerHTML = `
${sec('TIMELINE', '每行一天，横轴 00:00→24:00（悉尼）。一竖＝一场会话，高度＝你说了几次。<b>在图上横拖可以框选一段区间</b>。')}
<div class="ctl">
  <select id="range"><option value="30">最近 30 天</option><option value="60" selected>最近 60 天</option>
    <option value="90">最近 90 天</option><option value="0">全部 ${days.length} 天</option></select>
  <label><input type="checkbox" id="mach"> 画上机器扇出</label>
  <button id="clear">清除框选</button>
  <span class="tag" id="hud">未框选</span>
</div>
<canvas class="viz" id="cv"></canvas>
<div id="sum"></div>
<div id="tbl"></div>`;

  const cv = host.querySelector('#cv'), hud = host.querySelector('#hud');
  let rows = [], drag = null;

  const css = k => cssVar(k);
  const draw = () => {
    rows = (range ? days.slice(-range) : days).slice().reverse();
    const rowH = 15, padL = 78, padT = 18;
    const { ctx, w } = fitCanvas(cv, padT + rows.length * rowH + 8);
    const h = padT + rows.length * rowH + 8;
    ctx.clearRect(0, 0, w, h);
    ctx.font = '10px ui-monospace, monospace';

    ctx.strokeStyle = css('--hair'); ctx.fillStyle = css('--dim2');
    for (let hh = 0; hh <= 24; hh += 3) {
      const x = padL + (hh / 24) * (w - padL - 10);
      ctx.beginPath(); ctx.moveTo(x, padT - 4); ctx.lineTo(x, h); ctx.stroke();
      ctx.fillText(String(hh).padStart(2, '0'), x + 2, padT - 7);
    }

    rows.forEach((d, i) => {
      const y = padT + i * rowH;
      const inSel = sel && d.d >= sel[0] && d.d <= sel[1];
      if (inSel) { ctx.fillStyle = css('--sel'); ctx.fillRect(0, y, w, rowH); }
      ctx.fillStyle = inSel ? css('--fg') : css('--dim2');
      ctx.fillText(d.d.slice(5), 6, y + rowH - 4);
      ctx.fillStyle = css('--dim2');
      ctx.fillText(String(d.human).padStart(3), 48, y + rowH - 4);
      for (const s of (byDay.get(d.d) || [])) {
        if (!showMach && s.k !== 'human') continue;
        const lt = local(s.t);
        const x = padL + ((lt.getUTCHours() + lt.getUTCMinutes() / 60) / 24) * (w - padL - 10);
        const bh = Math.min(rowH - 3, 2.5 + Math.sqrt(Math.max(1, s.u)) * 2.6);
        ctx.globalAlpha = s.k === 'human' ? (sel && !inSel ? .25 : .95) : .28;
        ctx.fillStyle = s.tp[0] ? topicColor(s.tp[0]) : css('--dim2');
        ctx.fillRect(x, y + rowH - 2 - bh, 2.4, bh);
      }
      ctx.globalAlpha = 1;
    });
  };

  const rowAt = clientY => {
    const r = cv.getBoundingClientRect();
    const i = Math.floor((clientY - r.top - 18) / 15);
    return rows[Math.max(0, Math.min(rows.length - 1, i))];
  };
  cv.addEventListener('pointerdown', e => {
    drag = rowAt(e.clientY); cv.setPointerCapture(e.pointerId);
    sel = [drag.d, drag.d]; draw(); summarize();
  });
  cv.addEventListener('pointermove', e => {
    if (!drag) return;
    const b = rowAt(e.clientY);
    sel = [drag.d < b.d ? drag.d : b.d, drag.d < b.d ? b.d : drag.d];
    draw(); summarize();
  });
  cv.addEventListener('pointerup', () => { drag = null; });
  cv.addEventListener('dblclick', e => { const r = rowAt(e.clientY); if (r) go('day', r.d); });

  const summarize = () => {
    if (!sel) {
      hud.textContent = '未框选';
      host.querySelector('#sum').innerHTML = '';
      host.querySelector('#tbl').innerHTML = '';
      return;
    }
    const list = D.sessions({ kind: showMach ? 'all' : 'human', from: sel[0], to: sel[1] });
    const agg = D.aggregate(list);
    const nd = days.filter(d => d.d >= sel[0] && d.d <= sel[1]).length;
    hud.textContent = `${sel[0]} → ${sel[1]}　${nd} 天　${agg.n} 场`;
    host.querySelector('#sum').innerHTML = kv([
      ['区间', `${sel[0]} → ${sel[1]}`, 'acc'], ['天数', String(nd), ''],
      ['会话', String(agg.n), ''], ['你说话次数', String(agg.turns), ''],
      ['工具调用', String(agg.tools), ''], ['token 输入(含缓存)', fmt(agg.input_total), ''],
      ['缓存命中率', rate(agg.hit), 'acc'], ['未分类', String(agg.unclassified), agg.unclassified ? 'warn' : ''],
    ]);
    host.querySelector('#tbl').innerHTML = `<div class="sec">这段区间的主题</div>` + table(
      [{ t: '主题' }, { t: '会话', r: true }, { t: '占比', r: true }],
      agg.topics.map(([t, n]) => [
        `<span style="color:${topicColor(t)}">${esc(t)}</span>`, String(n),
        ((n / Math.max(1, agg.topics.reduce((a, b) => a + b[1], 0))) * 100).toFixed(1) + '%']));
    enter('tbody tr', host);
  };

  host.querySelector('#range').addEventListener('change', e => { range = +e.target.value; draw(); });
  host.querySelector('#mach').addEventListener('change', e => { showMach = e.target.checked; draw(); summarize(); });
  host.querySelector('#clear').addEventListener('click', () => { sel = null; draw(); summarize(); });
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw();
  enter('.sec', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
