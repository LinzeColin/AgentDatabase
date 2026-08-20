import { esc, fmt, go, local, topicColor, enter, reduced } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, loop } from '../../../core/g3d.js';
import { sec, kv, warn } from '../kit.js';

export async function render(host) {
  const days = D.days(), all = D.A().sessions;
  const idx = new Map(days.map((d, i) => [d.d, i]));
  const pts = all.map(s => {
    const lt = local(s.t);
    return { di: idx.get(s.d), x: (idx.get(s.d) || 0) / Math.max(1, days.length - 1),
      y: (lt.getUTCHours() + lt.getUTCMinutes() / 60) / 24,
      r: Math.min(6, 1.8 + Math.sqrt(Math.max(1, s.u)) * 1.05),
      c: s.tp[0] ? topicColor(s.tp[0]) : null, human: s.k === 'human' };
  }).filter(p => p.di != null);

  let i = days.length - 1, timer = null, speed = 140;
  host.innerHTML = `
${sec('REPLAY', `从 ${days[0].d} 推到 ${days[days.length - 1].d}，一帧一天。点会一颗颗落下来，不会消失。`)}
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
    const { ctx, w } = fitCanvas(cv, 400);
    const h = 400, pl = 46, pb = 20, pt = 8;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = css('--hair'); ctx.fillStyle = css('--dim2'); ctx.font = '10px ui-monospace, monospace';
    for (let hh = 0; hh <= 24; hh += 4) {
      const y = pt + (hh / 24) * (h - pt - pb);
      ctx.beginPath(); ctx.moveTo(pl, y); ctx.lineTo(w - 6, y); ctx.stroke();
      ctx.fillText(String(hh).padStart(2, '0'), 6, y + 3);
    }
    for (const p of pts) {
      if (p.di > i) continue;
      ctx.globalAlpha = p.di === i ? 1 : (p.human ? .68 : .18);
      ctx.fillStyle = p.c || css('--dim2');
      const x = pl + p.x * (w - pl - 8), y = pt + p.y * (h - pt - pb);
      ctx.beginPath(); ctx.arc(x, y, p.di === i ? p.r + 1.6 : p.r, 0, 6.2832); ctx.fill();
    }
    ctx.globalAlpha = 1;
    const cx = pl + (i / Math.max(1, days.length - 1)) * (w - pl - 8);
    ctx.strokeStyle = css('--acc'); ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(cx, pt); ctx.lineTo(cx, h - pb); ctx.stroke();

    const d = days[i], upto = days.slice(0, i + 1);
    host.querySelector('#sum').innerHTML = kv([
      ['当前', `<span class="lnk" data-day="${d.d}">${d.d}</span>`, 'acc'],
      ['这天你开口', String(d.human), ''],
      ['累计', String(upto.reduce((a, b) => a + b.human, 0)), ''],
      ['进度', `第 ${i + 1} / ${days.length} 个有记录的日子`, ''],
      ['当天主题', Object.entries(d.topics).sort((a, b) => b[1] - a[1]).slice(0, 3)
        .map(([t, n]) => `${esc(t)} ${n}`).join('、') || '未分类', ''],
    ]);
  };

  // 到头就停。绝不写没有终止条件的循环。
  const stop = () => { if (timer) clearInterval(timer); timer = null; btn.textContent = '▶ 播放'; };
  btn.addEventListener('click', () => {
    if (timer) return stop();
    if (i >= days.length - 1) i = 0;
    btn.textContent = '⏸ 暂停';
    timer = setInterval(() => {
      i++;
      if (i >= days.length - 1) { i = days.length - 1; stop(); }
      scrub.value = i; draw();
    }, speed);
  });
  host.querySelector('#rew').addEventListener('click', () => { stop(); i = 0; scrub.value = 0; draw(); });
  scrub.addEventListener('input', () => { stop(); i = +scrub.value; draw(); });
  host.querySelector('#sp').addEventListener('change', e => { speed = +e.target.value; if (timer) { stop(); btn.click(); } });
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.sec', host);
  return { dispose() { stop(); removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
