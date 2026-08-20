import { esc, fmt, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { hero, sec, grid, orbit, drawer, table, pill, rate } from '../kit.js';

// 白昼版时间轴＝小倍数（small multiples）：每个主题一条独立的折线，共用同一根时间轴、同一个纵向刻度。
// 这是把「谁在涨、谁在退」摊平了看最省力的排法 —— 堆叠图只能看总量，看不出单条。
export async function render(host) {
  const { weeks, names } = D.topicSeries();
  let shared = true, range = 0, sel = null;

  host.innerHTML = `
${hero('时间轴', '每个主题，各走各的线', `${weeks.length} 周，每个主题一条线。
  横轴是同一段时间，纵轴默认共用同一个刻度 —— 这样线的高低可以直接横向比。`)}
<div class="ctl">
  <button data-sc="shared" aria-pressed="true">共用纵轴</button>
  <button data-sc="own" aria-pressed="false">各自缩放</button>
  <select id="range"><option value="0" selected>全部 ${weeks.length} 周</option>
    <option value="26">最近 26 周</option><option value="13">最近 13 周</option></select>
  <span class="pill" id="hud">${names.length} 条线</span>
</div>
<div id="sm"></div>
<p class="hint">共用纵轴：所有线的 1 格＝同样多的场次，可以横向比大小。
  各自缩放：每条线自己填满，只能看形状不能比大小 —— 这一点必须写清楚，否则就是在骗自己。</p>
${sec('全期合计')}
<div id="tot"></div>
${drawer('摊开成表', table(
  [{ t: '主题' }, { t: '合计', r: true }, { t: '出现过的周', r: true }, { t: '最高的一周' }],
  names.map(t => {
    const s = weeks.map(w => w.count[t] || 0);
    const mx = Math.max(...s), at = weeks[s.indexOf(mx)];
    return [esc(t), String(s.reduce((a, b) => a + b, 0)),
      String(s.filter(x => x > 0).length), `${esc(at ? at.w : '—')}（${mx}）`];
  }).sort((a, b) => +b[1] - +a[1])))}`;

  const cols = () => range ? weeks.slice(-range) : weeks;

  const draw = () => {
    const W = cols();
    const gmax = Math.max(1, ...names.flatMap(t => W.map(w => w.count[t] || 0)));
    host.querySelector('#sm').innerHTML = `<div class="smwrap">${names.map(t => `
      <figure class="sm" data-topic="${esc(t)}">
        <figcaption><b>${esc(t)}</b><span>${W.reduce((a, w) => a + (w.count[t] || 0), 0)}</span></figcaption>
        <canvas data-t="${esc(t)}"></canvas>
      </figure>`).join('')}</div>`;
    host.querySelectorAll('.sm canvas').forEach(cv => {
      const t = cv.dataset.t;
      const s = W.map(w => w.count[t] || 0);
      const mx = shared ? gmax : Math.max(1, ...s);
      const H = 62, { ctx, w } = fitCanvas(cv, H);
      ctx.clearRect(0, 0, w, H);
      const step = w / Math.max(1, s.length - 1);
      ctx.strokeStyle = cssVar('--hair'); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(0, H - 1); ctx.lineTo(w, H - 1); ctx.stroke();
      // 面积用极浅的同色，线用主题色 —— 白昼不用发光，用面积权重
      ctx.beginPath(); ctx.moveTo(0, H - 1);
      s.forEach((v, i) => ctx.lineTo(i * step, H - 3 - (v / mx) * (H - 10)));
      ctx.lineTo(w, H - 1); ctx.closePath();
      ctx.globalAlpha = .13; ctx.fillStyle = topicColor(t); ctx.fill(); ctx.globalAlpha = 1;
      ctx.beginPath();
      s.forEach((v, i) => (i ? ctx.lineTo : ctx.moveTo).call(ctx, i * step, H - 3 - (v / mx) * (H - 10)));
      ctx.strokeStyle = topicColor(t); ctx.lineWidth = 1.6; ctx.stroke();
      const last = s[s.length - 1];
      if (last) {
        ctx.fillStyle = topicColor(t);
        ctx.beginPath(); ctx.arc(w - 2, H - 3 - (last / mx) * (H - 10), 2.6, 0, 6.2832); ctx.fill();
      }
    });
    host.querySelector('#hud').textContent =
      `${names.length} 条线 · ${W.length} 周 · 满格 ${shared ? gmax : '各自'}`;

    host.querySelector('#tot').innerHTML = orbit(names.map(t => ({
      k: t, v: W.reduce((a, w) => a + (w.count[t] || 0), 0), c: topicColor(t),
      attr: `data-topic="${esc(t)}"`,
    })).sort((a, b) => b.v - a.v));
    enter('.sm, .orow', host);
  };

  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-sc]'); if (!b) return;
    shared = b.dataset.sc === 'shared';
    host.querySelectorAll('[data-sc]').forEach(x =>
      x.setAttribute('aria-pressed', String((x.dataset.sc === 'shared') === shared)));
    draw();
  });
  host.querySelector('#range').onchange = e => { range = +e.target.value; draw(); };
  host.addEventListener('click', e => {
    const f = e.target.closest('[data-topic]');
    if (f) go('grid', 't=' + encodeURIComponent(f.dataset.topic));
  });

  const st = document.createElement('style');
  st.textContent = `
    [data-theme="gilt"] .smwrap{display:grid;grid-template-columns:repeat(auto-fill,minmax(216px,1fr));
      border-top:1px solid var(--line)}
    [data-theme="gilt"] .sm{margin:0;padding:12px 14px 10px;border-right:1px solid var(--hair);
      border-bottom:1px solid var(--hair);cursor:pointer}
    [data-theme="gilt"] .sm:hover{background:var(--track)}
    [data-theme="gilt"] .sm figcaption{display:flex;justify-content:space-between;align-items:baseline;
      font-size:12px;margin-bottom:8px}
    [data-theme="gilt"] .sm figcaption span{font-family:var(--mono);font-size:11px;color:var(--dim2)}
    [data-theme="gilt"] .sm canvas{width:100%;display:block}`;
  host.appendChild(st);

  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.hero, .sec', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
