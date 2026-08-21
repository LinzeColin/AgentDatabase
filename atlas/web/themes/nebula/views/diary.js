import { esc, fmt, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, beams, sheet, table, warn, pill, hud } from '../kit.js';

export async function render(host) {
  const J = D.A().diary;
  if (!J) { host.innerHTML = stage({ title: '日记', hint: '这一版还没有这块数据' }); return; }
  const rows = J.rows || [];
  hud([{ k: '有记录的日子', v: String(rows.length) }]);

  host.innerHTML = stage({
    eyebrow: '时间 · 日记',
    title: '那天你在干什么',
    hint: esc(J.note),
    body: (rows[0] ? headline(esc(rows[0].d), `「${esc((rows[0].opening || '').slice(0, 34))}」`,
      `${rows[0].sessions} 场 · ${rows[0].turns} 轮${rows[0].commits ? ` · 提交 ${rows[0].commits}` : ''}`) : '')
      + beams(rows.map(r => ({
          k: `${r.d}　${(r.opening || '（那天没留下第一句）').slice(0, 40)}`,
          v: r.turns || 1,
          sub: `${r.sessions} 场${r.commits ? ` · 提交 ${r.commits}` : ''}　${(r.topics || []).join('、')}`,
          label: r.shipped ? '交付了' : '—',
          c: r.shipped ? 'var(--acc3)' : 'var(--ink3)',
          attr: `data-day="${esc(r.d)}"` })))
      + ((J.silent_days || []).length ? warn(`<b>这些天你一次都没开口</b>（机器在跑）：${
          J.silent_days.map(esc).join('　')}<br>${esc(J.silent_note)}`) : ''),
  });
  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
  enter('.headline, .beam', host);
}
