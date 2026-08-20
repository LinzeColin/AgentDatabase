import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

export async function render(host, arg) {
  const topic = arg || '';
  const list = D.sessions({ kind: 'human', topic });
  const all = D.slice(0);

  if (!topic) {
    host.innerHTML = leaf({
      title: '按主题看',
      lead: '选一个主题。一次对话最多算三个主题，所以各主题之和大于总数。',
      cols: false,
      body: carve(Object.entries(all.topics).sort((a, b) => b[1] - a[1]).map(([t, n]) => ({
        k: t, v: n, attr: `data-topic="${esc(t)}"`,
      }))),
    });
  } else {
    const PER = 26, chunks = [];
    for (let i = 0; i < list.length; i += PER) chunks.push(list.slice(i, i + PER));
    host.innerHTML = leaf({
      title: topic,
      lead: `命中 ${list.length} 场，占你全部开口的 ${pct(list.length / Math.max(1, D.meta().sessions_human))}。
             <a href="#/grid" style="color:var(--gold)">← 回到全部主题</a>`,
      body: plate({ k: '命中的场次', v: String(list.length), big: true, n: '往后翻是逐场明细' }),
    }) + chunks.map((c, i) => leaf({
      title: `${topic} · 第 ${i + 1} 叠`, lead: `共 ${chunks.length} 叠。点一条进那天。`, cols: false,
      body: carve(c.map(s => ({
        k: (s.n || '（没有标题）').slice(0, 44), v: s.u || 1,
        label: `${s.d}　${s.u || 0} 轮`, attr: `data-day="${esc(s.d)}"`,
      }))),
    })).join('');
  }

  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]'), d = e.target.closest('[data-day]');
    if (t) go('grid', t.dataset.topic);
    else if (d) go('day', d.dataset.day);
  });
}
