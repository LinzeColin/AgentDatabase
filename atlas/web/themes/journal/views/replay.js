import { esc, go, local, topicColor, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas , cssVar } from '../../../core/g3d.js';
import { sec, lede, p, n, big, aside, figure } from '../kit.js';

export async function render(host) {
  const days = D.days(), all = D.A().sessions;
  const idx = new Map(days.map((d, i) => [d.d, i]));
  const pts = all.filter(s => idx.has(s.d)).map(s => {
    const lt = local(s.t);
    return { di: idx.get(s.d), x: idx.get(s.d) / Math.max(1, days.length - 1),
      y: (lt.getUTCHours() + lt.getUTCMinutes() / 60) / 24,
      r: Math.min(5, 1.3 + Math.sqrt(Math.max(1, s.u)) * .9),
      c: s.tp[0] ? topicColor(s.tp[0]) : null, human: s.k === 'human' };
  });
  let i = days.length - 1, timer = null, speed = 140;
  host.innerHTML = `
${sec('回放')}
${lede(`从 ${n(days[0].d)} 推到 ${n(days[days.length - 1].d)}，一帧一天。
  墨点一颗颗落下来，落下就不再消失 —— 这是这段时间在纸上慢慢显影的样子。`)}
<div class="ctl">
  <button id="play">播放</button><button id="rew">从头</button>
  <input type="range" id="scrub" min="0" max="${days.length - 1}" value="${i}" style="flex:1;min-width:200px">
  <select id="sp"><option value="60">快</option><option value="140" selected>中</option><option value="320">慢</option></select>
</div>
${figure('<canvas class="viz" id="cv"></canvas>', '横轴为日期，纵轴为一天里的时刻。')}
<div id="sum"></div>`;
  const cv = host.querySelector('#cv'), btn = host.querySelector('#play'), scrub = host.querySelector('#scrub');
  const css = k => cssVar(k);
  const draw = () => {
    const { ctx, w } = fitCanvas(cv, 380);
    const h = 380, pl = 48, pb = 20, pt = 10;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = css('--rule2'); ctx.fillStyle = css('--dim2');
    ctx.font = '10px -apple-system, system-ui, sans-serif';
    for (let hh = 0; hh <= 24; hh += 6) {
      const y = pt + (hh / 24) * (h - pt - pb);
      ctx.beginPath(); ctx.moveTo(pl, y); ctx.lineTo(w - 8, y); ctx.stroke();
      ctx.fillText(String(hh).padStart(2, '0') + ':00', 6, y + 4);
    }
    for (const q of pts) {
      if (q.di > i) continue;
      ctx.globalAlpha = q.di === i ? 1 : (q.human ? .55 : .14);
      ctx.fillStyle = q.c || css('--dim2');
      const x = pl + q.x * (w - pl - 10), y = pt + q.y * (h - pt - pb);
      ctx.beginPath(); ctx.arc(x, y, q.di === i ? q.r + 1.2 : q.r, 0, 6.2832); ctx.fill();
    }
    ctx.globalAlpha = 1;
    const cx = pl + (i / Math.max(1, days.length - 1)) * (w - pl - 10);
    ctx.strokeStyle = css('--acc'); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cx, pt); ctx.lineTo(cx, h - pb); ctx.stroke();
    const d = days[i];
    host.querySelector('#sum').innerHTML = p(`现在停在 <span class="lnk" data-day="${d.d}">${d.d}</span>，
      这一天你开了 ${big(d.human)} 场，累计 ${n(days.slice(0, i + 1).reduce((a, b) => a + b.human, 0))} 场，
      是第 ${n(i + 1)} / ${n(days.length)} 个有记录的日子。`);
  };
  const stop = () => { if (timer) clearInterval(timer); timer = null; btn.textContent = '播放'; };
  btn.onclick = () => {
    if (timer) return stop();
    if (i >= days.length - 1) i = 0;
    btn.textContent = '暂停';
    timer = setInterval(() => { i++; if (i >= days.length - 1) { i = days.length - 1; stop(); }
      scrub.value = i; draw(); }, speed);
  };
  host.querySelector('#rew').onclick = () => { stop(); i = 0; scrub.value = 0; draw(); };
  scrub.oninput = () => { stop(); i = +scrub.value; draw(); };
  host.querySelector('#sp').onchange = e => { speed = +e.target.value; if (timer) { stop(); btn.click(); } };
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.sec, p.body, figure', host);
  return { dispose() { stop(); removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
