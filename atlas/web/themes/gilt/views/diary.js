import { esc, fmt, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, carve, marginal, warn, rub, chip, seal } from '../kit.js';

// 日记。册页版一页 12 天，翻页就是往回翻日子 —— 和纸质日记一样。
export async function render(host) {
  const J = D.A().diary;
  if (!J) { host.innerHTML = leaf({ title: '日记', lead: '这一版还没有这块数据' }); return; }
  const rows = J.rows || [];
  const PER = 10, chunks = [];
  for (let i = 0; i < rows.length; i += PER) chunks.push(rows.slice(i, i + PER));

  host.innerHTML =
    leaf({
      title: '那天你在干什么',
      lead: esc(J.note) + `　${esc(J.coverage)}。往后翻是更早的日子。`,
      body: (rows[0] ? plate({ k: rows[0].d, big: true, size: 'sm', plain: true,
        v: `「${esc(rows[0].opening || '（那天没留下第一句）')}」`,
        n: `${rows[0].sessions} 场 · ${rows[0].turns} 轮${rows[0].commits ? ` · 提交 ${rows[0].commits}` : ''}` }) : '')
        + ((J.silent_days || []).length ? marginal(`<b>这些天你一次都没开口</b>（机器在跑）：${
            J.silent_days.map(chip).join('')}<br>${esc(J.silent_note)}`) : ''),
    })
    + chunks.map((c, i) => leaf({
      title: `${c[c.length - 1].d} → ${c[0].d}`,
      lead: `第 ${i + 1} 叠 / 共 ${chunks.length} 叠。点日期进那天。`,
      cols: false,
      body: c.map(r => `
        <div class="marginal" data-day="${esc(r.d)}" role="button" tabindex="0"
             style="cursor:pointer;border-left-color:${r.shipped ? 'var(--gold)' : 'var(--rule2)'}">
          <b style="font-family:var(--mono)">${esc(r.d)}</b>${r.shipped ? seal('通') : ''}
          <div style="font-size:14px;line-height:1.8;margin:4px 0">「${esc(r.opening || '（那天没留下第一句）')}」</div>
          <div style="color:var(--ink3);font-size:11.5px">
            ${r.sessions} 场 · ${r.turns} 轮${r.commits ? ` · 提交 ${r.commits}` : ''}
            ${(r.topics || []).map(chip).join('')}
          </div>
          ${(r.files || []).length ? `<div style="color:var(--ink3);font-size:11px">改过：${
            r.files.map(f => `<code>${esc(f)}</code>`).join(' ')}</div>` : ''}
        </div>`).join(''),
    })).join('');

  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
}
