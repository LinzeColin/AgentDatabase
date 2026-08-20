import { esc, fmt, go, enter, reduced, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { loop } from '../../../core/g3d.js';
import { hero, sec, grid, orbit, slab, drawer, table, warn, pill } from '../kit.js';
import { flyToDay, holdCamera } from '../shell.js';

// 白昼的回放是一份**逐周排版的编年**：像翻报纸，一周一版。
// 不做竞速条（琉璃有）、不飞相机（星云有）—— 它靠字号跨度和留白讲「这一周发生了什么」。
export async function render(host) {
  const A = D.A(), W = A.trend.weeks.filter(w => w.human > 0);
  const names = A.topic_names.filter(t => W.some(w => (w.count[t] || 0) > 0));
  const dl = (A.delivery && A.delivery.state === '通') ? A.delivery.days : [];
  const cw = {}, pw = {};
  for (const r of dl) {
    const k = isoWeekOf(r.d);
    cw[k] = (cw[k] || 0) + r.commits; pw[k] = (pw[k] || 0) + (r.prs || 0);
  }
  function isoWeekOf(iso) {
    const d = new Date(iso + 'T00:00:00Z');
    const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
    const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day);
    const y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
    return `${t.getUTCFullYear()}-W${String(Math.ceil(((t - y0) / 864e5 + 1) / 7)).padStart(2, '0')}`;
  }
  function weekStart(wk) {
    const [y, n] = wk.split('-W').map(Number);
    const jan4 = new Date(Date.UTC(y, 0, 4));
    const mon = new Date(jan4);
    mon.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() || 7) - 1) + (n - 1) * 7);
    return mon.toISOString().slice(0, 10);
  }

  const acc = {};
  const cum = W.map(w => {
    for (const t of names) acc[t] = (acc[t] || 0) + (w.count[t] || 0);
    return { w: w.w, n: w.human, snap: { ...acc }, commits: cw[w.w] || 0, prs: pw[w.w] || 0 };
  });

  let i = 0, playing = false, speed = 1200, tAcc = 0, last = performance.now();
  holdCamera(true);            // 回放期间镜头归回放，滚动不抢方向盘

  host.innerHTML = `
${hero('回放', '一周一版', `${cum.length} 周，一周一版地翻过去。
  每一版只回答三件事：那周你在做什么、新长出了什么、交出去了多少。`)}
<div class="ctl">
  <button id="play">▶ 播放</button><button id="rew">⟲ 回到第一版</button>
  <input type="range" id="scrub" min="0" max="${cum.length - 1}" value="0" style="flex:1;min-width:220px">
  <select id="sp"><option value="700">快</option><option value="1200" selected>中</option><option value="2000">慢</option></select>
</div>
<div id="page"></div>
${dl.length ? '' : warn('没接上 GitHub 提交数据，所以「那周交出去了多少」是空的。不是零，是没读到。')}`;

  const btn = host.querySelector('#play'), scrub = host.querySelector('#scrub');
  const page = host.querySelector('#page');

  const paint = () => {
    const c = cum[i], prev = i > 0 ? cum[i - 1] : null;
    const deltas = names.map(t => ({ t, d: (c.snap[t] || 0) - (prev ? (prev.snap[t] || 0) : 0) }))
      .filter(x => x.d > 0).sort((a, b) => b.d - a.d);
    const top = names.map(t => ({ k: t, v: c.snap[t] || 0, c: topicColor(t) }))
      .filter(x => x.v > 0).sort((a, b) => b.v - a.v).slice(0, 10);
    page.innerHTML = `
      <div class="pgtop">
        <div>
          <div class="ck">第 ${i + 1} / ${cum.length} 版</div>
          <div class="pgw">${esc(c.w)}</div>
          <div class="cn"><span class="lnk" data-day="${weekStart(c.w)}">${weekStart(c.w)}</span> 那一周</div>
        </div>
        <div class="pgnum">
          <div><b>${c.n}</b><span>场会话</span></div>
          <div><b>${c.commits}</b><span>条提交</span></div>
          <div><b>${c.prs}</b><span>个 PR</span></div>
        </div>
      </div>
      ${deltas.length ? `<div class="sec">这一周新长出来的</div>${orbit(deltas.slice(0, 6).map(x =>
        ({ k: x.t, v: x.d, label: `+${x.d}`, c: topicColor(x.t) })))}`
        : `<div class="sec">这一周在做老活</div><p class="hint">没有新增的主题 —— 全部落在此前已经开过的口子里。</p>`}
      <div class="sec">到这一周为止，谁跑在前面</div>${orbit(top)}`;
    enter('.orow', page);
    flyToDay(weekStart(c.w));  // 翻到哪一版，碑林就摇到那一周
  };

  const stop = () => { playing = false; btn.textContent = '▶ 播放'; };
  btn.onclick = () => {
    if (playing) return stop();
    if (i >= cum.length - 1) i = 0;
    playing = true; btn.textContent = '⏸ 停';
  };
  host.querySelector('#rew').onclick = () => { stop(); i = 0; scrub.value = 0; paint(); };
  scrub.oninput = () => { stop(); i = +scrub.value; paint(); };
  host.querySelector('#sp').onchange = e => { speed = +e.target.value; };
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day);
  });

  const st = document.createElement('style');
  st.textContent = `
    [data-theme="gilt"] .pgtop{display:flex;justify-content:space-between;align-items:flex-end;
      gap:24px;flex-wrap:wrap;border-top:3px solid var(--fg);padding-top:14px;margin-top:8px}
    [data-theme="gilt"] .pgw{font-size:clamp(34px,6vw,64px);font-weight:700;letter-spacing:-.04em;
      line-height:1;margin:6px 0 8px;font-variant-numeric:tabular-nums}
    [data-theme="gilt"] .pgnum{display:flex;gap:32px}
    [data-theme="gilt"] .pgnum b{display:block;font-size:34px;font-weight:700;letter-spacing:-.03em;
      font-variant-numeric:tabular-nums}
    [data-theme="gilt"] .pgnum span{font-family:var(--mono);font-size:10px;color:var(--dim2);
      letter-spacing:.08em}`;
  host.appendChild(st);

  const l = loop(now => {
    const dt = Math.min(90, now - last); last = now;
    if (!playing || reduced()) return;
    tAcc += dt;
    if (tAcc < speed) return;
    tAcc = 0; i++;
    if (i >= cum.length - 1) { i = cum.length - 1; stop(); }
    scrub.value = i; paint();
  });
  paint(); enter('.hero', host);
  return { dispose() { l.stop(); holdCamera(false); } };
}
