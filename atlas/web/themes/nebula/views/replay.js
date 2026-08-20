import { esc, fmt, go, local, topicColor, enter, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas } from '../../../core/g3d.js';
import { sec, bento, pill } from '../kit.js';

export async function render(host) {
  const days = D.days(), all = D.A().sessions;
  const idx = new Map(days.map((d, i) => [d.d, i]));
  const pts = all.map(s => {
    const lt = local(s.t);
    return { di: idx.get(s.d), x: (idx.get(s.d) || 0) / Math.max(1, days.length - 1),
      y: (lt.getUTCHours() + lt.getUTCMinutes() / 60) / 24,
      r: Math.min(7, 1.9 + Math.sqrt(Math.max(1, s.u)) * 1.1),
      c: s.tp[0] ? topicColor(s.tp[0]) : null, human: s.k === 'human' };
  }).filter(p => p.di != null);
  let i = days.length - 1, timer = null, speed = 140;

  host.innerHTML = `
${sec('回放', `从 ${days[0].d} 推到 ${days[days.length - 1].d}，一帧一天。星星一颗颗亮起来，不会熄灭。`)}
<div class="ctl">
  <button id="play">▶ 播放</button><button id="rew">⟲ 从头</button>
  <input type="range" id="scrub" min="0" max="${days.length - 1}" value="${i}" style="flex:1;min-width:220px">
  <select id="sp"><option value="60">快</option><option value="140" selected>中</option><option value="320">慢</option></select>
</div>
<canvas class="viz" id="cv"></canvas>
<div id="sum"></div>`;

  const cv = host.querySelector('#cv'), btn = host.querySelector('#play'), scrub = host.querySelector('#scrub');
  const css = k => getComputedStyle(document.body).getPropertyValue(k).trim();
  const draw = () => {
    const { ctx, w } = fitCanvas(cv, 420);
    const h = 420, pl = 52, pb = 24, pt = 12;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = css('--line2'); ctx.fillStyle = css('--dim2');
    ctx.font = '10.5px -apple-system, system-ui, sans-serif';
    for (let hh = 0; hh <= 24; hh += 4) {
      const y = pt + (hh / 24) * (h - pt - pb);
      ctx.beginPath(); ctx.moveTo(pl, y); ctx.lineTo(w - 10, y); ctx.stroke();
      ctx.fillText(String(hh).padStart(2, '0') + ':00', 8, y + 4);
    }
    ctx.globalCompositeOperation = S.mode === 'dark' ? 'lighter' : 'source-over';
    for (const p of pts) {
      if (p.di > i) continue;
      const x = pl + p.x * (w - pl - 12), y = pt + p.y * (h - pt - pb);
      const c = p.c || css('--dim2');
      const fresh = p.di === i;
      const g = ctx.createRadialGradient(x, y, 0, x, y, p.r * 3.6);
      g.addColorStop(0, c); g.addColorStop(1, 'transparent');
      ctx.globalAlpha = fresh ? .5 : (p.human ? .2 : .07);
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, p.r * 3.6, 0, 6.2832); ctx.fill();
      ctx.globalAlpha = fresh ? 1 : (p.human ? .62 : .16);
      ctx.fillStyle = c; ctx.beginPath(); ctx.arc(x, y, fresh ? p.r + 1.4 : p.r, 0, 6.2832); ctx.fill();
    }
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
    const cx = pl + (i / Math.max(1, days.length - 1)) * (w - pl - 12);
    ctx.strokeStyle = css('--acc'); ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(cx, pt); ctx.lineTo(cx, h - pb); ctx.stroke();

    const d = days[i];
    host.querySelector('#sum').innerHTML = bento([
      { k: '当前', v: `<span class="lnk" data-day="${d.d}" style="font-size:30px">${d.d}</span>`,
        n: `第 ${i + 1} / ${days.length} 个有记录的日子`, w: 3, tone: 'acc' },
      { k: '这天你开口', v: String(d.human), n: `累计 ${days.slice(0, i + 1).reduce((a, b) => a + b.human, 0)} 场`, w: 3, alt: true },
      { k: '当天主题', v: `<span style="font-size:20px">${Object.entries(d.topics).sort((a,b)=>b[1]-a[1]).slice(0,2).map(([t])=>esc(t)).join('、') || '未分类'}</span>`,
        n: `${d.active_hours} 个钟点里有动静` },
    ]);
  };
  // 到头就停。绝不写没有终止条件的循环。
  const stop = () => { if (timer) clearInterval(timer); timer = null; btn.textContent = '▶ 播放'; };
  btn.onclick = () => {
    if (timer) return stop();
    if (i >= days.length - 1) i = 0;
    btn.textContent = '⏸ 暂停';
    timer = setInterval(() => { i++; if (i >= days.length - 1) { i = days.length - 1; stop(); }
      scrub.value = i; draw(); }, speed);
  };
  host.querySelector('#rew').onclick = () => { stop(); i = 0; scrub.value = 0; draw(); };
  scrub.oninput = () => { stop(); i = +scrub.value; draw(); };
  host.querySelector('#sp').onchange = e => { speed = +e.target.value; if (timer) { stop(); btn.click(); } };
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.sec, .card', host);
  return { dispose() { stop(); removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
