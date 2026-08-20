import { esc, fmt, go, enter, topicColor, reduced } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { loop } from '../../../core/g3d.js';
import { flyToDay, holdCamera } from '../shell.js';
import { hero, sec, grid, orbit, slab, warn, pill } from '../kit.js';

// 星云主题的回放不是图表在动 —— 是**相机真的往回飞**。
// 按播放，背后那片星图会一周一周往前推，前面这块牌子告诉你这一周发生了什么。
export async function render(host) {
  const A = D.A(), W = A.trend.weeks.filter(w => w.human > 0);
  const names = A.topic_names.filter(t => W.some(w => (w.count[t] || 0) > 0));
  const dl = (A.delivery && A.delivery.state === '通') ? A.delivery.days : [];

  const commitsByWeek = {}, prByWeek = {};
  for (const r of dl) {
    const wk = isoWeekOf(r.d);
    commitsByWeek[wk] = (commitsByWeek[wk] || 0) + r.commits;
    prByWeek[wk] = (prByWeek[wk] || 0) + (r.prs || 0);
  }
  function isoWeekOf(iso) {
    const d = new Date(iso + 'T00:00:00Z');
    const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
    const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day);
    const y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
    return `${t.getUTCFullYear()}-W${String(Math.ceil(((t - y0) / 864e5 + 1) / 7)).padStart(2, '0')}`;
  }

  const acc = {};
  const cum = W.map(w => {
    for (const t of names) acc[t] = (acc[t] || 0) + (w.count[t] || 0);
    return { w: w.w, n: w.human, snap: { ...acc },
      commits: commitsByWeek[w.w] || 0, prs: prByWeek[w.w] || 0 };
  });

  let i = 0, playing = false, speed = 1100, tAcc = 0, last = performance.now();
  holdCamera(true);          // 这一屏由回放开镜头，滚动不参与

  host.innerHTML = `
${hero('回放', '一周一周飞回去', `按播放，背后那片星图会跟着往前推 —— 你看到的是<b>当时</b>的天空。
  前面这块牌子告诉你那一周新长出了什么。`)}
<div class="ctl">
  <button id="play">▶ 播放</button><button id="rew">⟲ 回到最早</button>
  <input type="range" id="scrub" min="0" max="${cum.length - 1}" value="0" style="flex:1;min-width:220px">
  <select id="sp"><option value="600">快</option><option value="1100" selected>中</option><option value="1900">慢</option></select>
</div>
<div id="capt"></div>
<div id="bars"></div>
${dl.length ? '' : warn('这一屏没有接上 GitHub 提交数据，所以「那周交付了什么」是空的。不是零，是没读到。')}`;

  const btn = host.querySelector('#play'), scrub = host.querySelector('#scrub');
  const capt = host.querySelector('#capt'), bars = host.querySelector('#bars');

  const paint = () => {
    const c = cum[i], prev = i > 0 ? cum[i - 1] : null;
    const deltas = names.map(t => ({ t, d: (c.snap[t] || 0) - (prev ? (prev.snap[t] || 0) : 0) }))
      .filter(x => x.d > 0).sort((a, b) => b.d - a.d);
    capt.innerHTML = grid([
      { k: '飞到了', v: `${esc(c.w)}`, size: 'md',
        n: `第 ${i + 1} / ${cum.length} 周`, w: 3, tone: 'acc' },
      { k: '那周你开口', v: String(c.n), n: `提交 ${c.commits} 次 · PR ${c.prs} 个`, w: 3, alt: true },
      { k: '那周新长出来的', v: `${deltas.slice(0, 3).map(x => esc(x.t)).join('、') || '没有新的'}`, size: 'sm',
        n: deltas.slice(0, 3).map(x => `+${x.d}`).join('　') || '这周在做老活' },
      { k: '到这周为止累计', v: fmt(Object.values(c.snap).reduce((a, b) => a + b, 0)), n: '所有主题加起来' },
    ]);
    const top = names.map(t => ({ k: t, v: c.snap[t] || 0, c: topicColor(t) }))
      .filter(x => x.v > 0).sort((a, b) => b.v - a.v).slice(0, 10);
    bars.innerHTML = sec('到这一周为止，谁跑在前面') + orbit(top);
    flyToDay(weekStart(c.w));
  };

  function weekStart(wk) {
    const [y, w] = wk.split('-W').map(Number);
    const jan4 = new Date(Date.UTC(y, 0, 4));
    const mon = new Date(jan4); mon.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() || 7) - 1) + (w - 1) * 7);
    return mon.toISOString().slice(0, 10);
  }

  const stop = () => { playing = false; btn.textContent = '▶ 播放'; };
  btn.onclick = () => {
    if (playing) return stop();
    if (i >= cum.length - 1) i = 0;
    playing = true; btn.textContent = '⏸ 停';
  };
  host.querySelector('#rew').onclick = () => { stop(); i = 0; scrub.value = 0; paint(); };
  scrub.oninput = () => { stop(); i = +scrub.value; paint(); };
  host.querySelector('#sp').onchange = e => { speed = +e.target.value; };

  const l = loop(now => {
    const dt = Math.min(90, now - last); last = now;
    if (!playing || reduced()) return;
    tAcc += dt;
    if (tAcc < speed) return;
    tAcc = 0; i++;
    if (i >= cum.length - 1) { i = cum.length - 1; stop(); }
    scrub.value = i; paint();
  });

  paint();
  enter('.hero, .sec, .cell', host);
  return { dispose() { l.stop(); holdCamera(false); } };
}
