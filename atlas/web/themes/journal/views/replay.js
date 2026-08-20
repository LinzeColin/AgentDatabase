import { esc, fmt, pct, go, enter, topicColor, reduced, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar, loop } from '../../../core/g3d.js';
import { sec, lede, p, n as num, aside, figure, rank, table } from '../kit.js';

// 回放 = 竞速条：主题份额一周一周赛跑。
// 上一版只是让点一颗颗亮起来，看不出「什么在变」—— 那是它被要求重做的原因。
export async function render(host) {
  const A = D.A(), W = A.trend.weeks.filter(w => w.human > 0);
  const names = A.topic_names.filter(t => W.some(w => (w.count[t] || 0) > 0));
  const dl = (A.delivery && A.delivery.state === '通') ? A.delivery.days : [];
  const commitsByWeek = {};
  for (const r of dl) {
    const d = new Date(r.d + 'T00:00:00Z');
    const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
    const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day);
    const y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
    const wk = `${t.getUTCFullYear()}-W${String(Math.ceil(((t - y0) / 864e5 + 1) / 7)).padStart(2, '0')}`;
    commitsByWeek[wk] = (commitsByWeek[wk] || 0) + r.commits;
  }
  const css = k => cssVar(k);

  // 累计值 —— 竞速条比的是「到这一周为止累计了多少」
  const cum = [];
  const acc = {};
  for (const w of W) {
    for (const t of names) acc[t] = (acc[t] || 0) + (w.count[t] || 0);
    cum.push({ w: w.w, n: w.human, snap: { ...acc }, commits: commitsByWeek[w.w] || 0 });
  }

  let i = cum.length - 1, playing = false, speed = 900, tAcc = 0, last = performance.now();
  const shown = {};   // 平滑插值用

  host.innerHTML = `${sec('赛跑')}
${lede(`主题的累计场次一周一周往前跑。谁在追上谁、什么时候被反超 —— 一眼能看出来。`)}
<div class="ctl">
  <button id="play">播放</button><button id="rew">从头</button>
  <input type="range" id="scrub" min="0" max="${cum.length - 1}" value="${cum.length - 1}" style="flex:1;min-width:180px">
  <select id="sp"><option value="450">快</option><option value="900" selected>中</option><option value="1600">慢</option></select>
</div>
${figure('<canvas class="viz" id="race"></canvas>', '横条长度＝到该周为止的累计场次。')}
<div id="capt"></div>`;

  const cv = host.querySelector('#race');
  const btn = host.querySelector('#play'), scrub = host.querySelector('#scrub');
  const capt = host.querySelector('#capt');

  const draw = () => {
    const rowH = 26, padT = 14, padL = 118, padR = 92, top = 10;
    const target = cum[i].snap;
    for (const t of names) {
      const v = target[t] || 0;
      shown[t] = shown[t] == null ? v : shown[t] + (v - shown[t]) * 0.22;
    }
    const order = names.slice().sort((a, b) => (shown[b] || 0) - (shown[a] || 0)).slice(0, top);
    const h = padT + order.length * rowH + 12;
    const { ctx, w } = fitCanvas(cv, h);
    ctx.clearRect(0, 0, w, h);
    const mx = Math.max(1, ...order.map(t => shown[t] || 0));
    order.forEach((t, r) => {
      const y = padT + r * rowH;
      const bw = ((shown[t] || 0) / mx) * (w - padL - padR);
      ctx.fillStyle = topicColor(t); ctx.globalAlpha = .78; ctx.fillRect(padL, y + 5, Math.max(1, bw), rowH - 11); ctx.globalAlpha = 1;
      ctx.fillStyle = css('--fg'); ctx.font = '600 12px -apple-system, system-ui, sans-serif'; ctx.textAlign = 'right';
      ctx.fillText(t.slice(0, 8), padL - 8, y + rowH * .68);
      ctx.textAlign = 'left'; ctx.fillStyle = css('--dim');
      ctx.font = '11px -apple-system, system-ui, sans-serif';
      ctx.fillText(String(Math.round(shown[t] || 0)), padL + bw + 7, y + rowH * .68);
    });
    ctx.textAlign = 'left';
  };

  const caption = () => {
    const c = cum[i], prev = i > 0 ? cum[i - 1] : null;
    const deltas = names.map(t => ({ t, d: (c.snap[t] || 0) - (prev ? (prev.snap[t] || 0) : 0) }))
      .filter(x => x.d > 0).sort((a, b) => b.d - a.d).slice(0, 3);
    capt.innerHTML = p(`现在停在 <b>${esc(c.w)}</b>，是第 ${i + 1} / ${cum.length} 周。
      这一周你开了 <b>${c.n}</b> 场会话，产生 <b>${c.commits}</b> 条提交。
      涨得最多的是 ${deltas.map(x => `<b>${esc(x.t)}</b>（+${x.d}）`).join('、') || '没有明显增长'}。`);
  };

  const stop = () => { playing = false; btn.textContent = '▶ 播放'; };
  btn.onclick = () => {
    if (playing) return stop();
    if (i >= cum.length - 1) { i = 0; for (const k of names) shown[k] = 0; }
    playing = true; btn.textContent = '⏸ 暂停';
  };
  host.querySelector('#rew').onclick = () => { stop(); i = 0; for (const k of names) shown[k] = 0; scrub.value = 0; caption(); };
  scrub.oninput = () => { stop(); i = +scrub.value; caption(); };
  host.querySelector('#sp').onchange = e => { speed = +e.target.value; };

  const l = loop(now => {
    const dt = Math.min(80, now - last); last = now;
    if (playing && !reduced()) {
      tAcc += dt;
      if (tAcc >= speed) {
        tAcc = 0; i++;
        if (i >= cum.length - 1) { i = cum.length - 1; stop(); }
        scrub.value = i; caption();
      }
    }
    draw();
  });
  caption();
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  enter('.sec, p.body, figure', host);
  return { dispose() { l.stop(); removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
