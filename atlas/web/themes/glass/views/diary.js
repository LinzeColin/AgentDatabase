import { esc, fmt, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, drawer, table, warn, pill, state } from '../kit.js';

// 日记。日历回答「哪天忙」，这里回答「那天你在干什么」——
// 所以主体必须是**你自己的原话**，统计只做配角。
export async function render(host) {
  const J = D.A().diary;
  if (!J) { host.innerHTML = sec('日记', '这一版还没有这块数据'); enter('.sec', host); return; }

  host.innerHTML = `
${sec('日记', esc(J.note))}
<p class="hint">${esc(J.coverage)}</p>
<div class="orbit">${(J.rows || []).map(r => `
  <div class="orow" data-day="${esc(r.d)}" role="button" tabindex="0"
       style="grid-template-columns:auto 1fr auto;align-items:start;padding:12px 0">
    <span class="olabel" style="min-width:96px;font-variant-numeric:tabular-nums">${esc(r.d)}</span>
    <span style="text-align:left;min-width:0">
      <span style="display:block;font-family:var(--disp);font-size:15px;line-height:1.6">「${esc(r.opening || '（那天没留下第一句）')}」</span>
      <span class="hint" style="display:block;margin-top:4px">
        ${r.sessions} 场 · ${r.turns} 轮${r.commits ? ` · 提交 ${r.commits}` : ''}${r.merged ? ` · 合并 ${r.merged}` : ''}
        ${(r.topics || []).map(t => pill(t)).join('')}
      </span>
      ${(r.files || []).length ? `<span class="hint" style="display:block">改过：${
        r.files.map(f => `<code>${esc(f)}</code>`).join(' ')}</span>` : ''}
    </span>
    <span class="oval">${r.shipped ? state('通') : ''}</span>
  </div>`).join('')}</div>
${(J.silent_days || []).length ? warn(`<b>这些天你一次都没开口</b>（机器在跑）：
  ${J.silent_days.map(d => pill(d)).join('')}<br>${esc(J.silent_note)}`) : ''}`;

  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
  enter('.sec, .orow', host);
}
