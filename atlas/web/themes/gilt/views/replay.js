import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

// 回放。金册版的回放是**自动翻页**：每 1.1 秒翻一页，金页上的读书光跟着走。
export async function render(host) {
  const ws = D.weeks();
  if (!ws.length) { host.innerHTML = leaf({ title: '回放', body: warn('<b>没做。</b>没有周数据。') }); return; }
  host.innerHTML = ws.slice().reverse().map((w, i) => leaf({
    title: w.w,
    lead: `第 ${i + 1} 页 / 共 ${ws.length} 页。按下自动翻页，书口上的读书光会跟着往前走。`,
    body: plate({ k: '这一周你开口', v: String(w.human), big: true,
      n: `${w.auto} 场机器 · ${w.turns} 轮 · ${w.active_hours || 0} 个活跃小时` })
      + (i === 0 ? `<div style="text-align:center;margin:18px 0">
          <button id="auto" class="chip" style="cursor:pointer;padding:7px 20px;font-size:13px">▶ 自动翻页</button>
          </div>` : ''),
  })).join('');

  let timer = 0;
  host.addEventListener('click', e => {
    if (!e.target.closest('#auto')) return;
    const btn = e.target.closest('#auto');
    if (timer) { clearInterval(timer); timer = 0; btn.textContent = '▶ 自动翻页'; return; }
    btn.textContent = '■ 停';
    timer = setInterval(() => {
      const nx = document.getElementById('next');
      if (!nx || nx.disabled) { clearInterval(timer); timer = 0; btn.textContent = '▶ 自动翻页'; return; }
      nx.click();
    }, 1100);
  });
  return { dispose() { if (timer) clearInterval(timer); } };
}
