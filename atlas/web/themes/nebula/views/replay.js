import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 回放。**这一屏是这套主题最像它自己的地方** ——
// 按下播放，镜头沿时间轴飞，中央只报当前飞到哪一周。
import { holdCamera, scene } from '../shell.js';

export async function render(host) {
  const ws = D.weeks();
  if (!ws.length) { host.innerHTML = warn('<b>没做。</b>没有周数据。'); return; }
  let i = 0, timer = 0, playing = false;

  hud([{ k: '回放', v: '就绪' }]);
  host.innerHTML = stage({
    eyebrow: '时间 · 回放',
    title: '穿过自己的时间',
    hint: '按下播放，镜头会沿时间轴一周一周往前飞。<b>回放期间滚动不再控制镜头。</b>',
    body: `<div class="headline"><div class="k" id="rw">${esc(ws[0].w)}</div>
             <div class="v" id="rn">${ws[0].human}</div>
             <div class="n" id="rd">${ws[0].auto} 场机器 · ${ws[0].turns} 轮</div></div>
           <div style="display:flex;gap:8px;justify-content:center;margin:18px 0">
             <button id="play" class="pill" style="cursor:pointer;padding:8px 20px;font-size:13px">▶ 播放</button>
             <button id="stop" class="pill" style="cursor:pointer;padding:8px 20px;font-size:13px">■ 停</button>
           </div>
           <p class="hint" id="prog"></p>`,
  });

  const $ = s => host.querySelector(s);
  const paint = () => {
    const w = ws[i];
    $('#rw').textContent = w.w; $('#rn').textContent = w.human;
    $('#rd').textContent = `${w.auto} 场机器 · ${w.turns} 轮`;
    $('#prog').textContent = `${i + 1} / ${ws.length}`;
    try { scene()?.flyTo(ws.length > 1 ? i / (ws.length - 1) : 0); } catch { /* 天幕没点起来 */ }
  };
  const stop = () => { playing = false; clearInterval(timer); timer = 0; holdCamera(false); hud([{ k: '回放', v: '停' }]); };
  $('#play').onclick = () => {
    if (playing) return;
    playing = true; holdCamera(true); hud([{ k: '回放', v: '播放中' }]);
    timer = setInterval(() => {
      i = (i + 1) % ws.length; paint();
      if (i === 0) stop();
    }, 900);
  };
  $('#stop').onclick = stop;
  paint();
  enter('.headline', host);
  return { dispose() { stop(); } };
}
