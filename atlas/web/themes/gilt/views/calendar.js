import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

// 日历。**一册十二页**：每 12 天一页，翻页就是翻月份。
export async function render(host) {
  const ds = D.days();
  const active = ds.filter(d => d.human > 0);
  const peak = ds.reduce((a, b) => (b.human > (a?.human ?? -1) ? b : a), null);
  const PER = 24;
  const chunks = [];
  const rev = ds.slice().reverse();
  for (let i = 0; i < rev.length; i += PER) chunks.push(rev.slice(i, i + PER));

  host.innerHTML =
    leaf({
      title: '哪一天最重',
      lead: `一天一条刻痕，长度是你那天开口的次数。共 ${ds.length} 天，往后翻是更早的日子。`,
      body: plate({ k: '最忙的一天', v: peak ? esc(peak.d) : '—', big: true,
        n: peak ? `${peak.human} 次开口 · ${peak.turns} 轮 · ${fmt(peak.tok_in + peak.tok_cache_r)} token` : '' })
        + plates([
          { k: '有记录的天', v: String(active.length), n: `共 ${ds.length} 天有数据` },
          { k: '平均每天', v: (active.reduce((s, d) => s + d.human, 0) / Math.max(1, active.length)).toFixed(1),
            n: '只算有记录的天' },
          { k: '一次都没开口', v: String(ds.length - active.length), n: '机器在跑，你没说话' },
        ]),
    })
    + chunks.map((c, i) => leaf({
        title: `${c[c.length - 1].d} → ${c[0].d}`,
        lead: `第 ${i + 1} 组，共 ${chunks.length} 组。点一条进那天。`,
        cols: false,
        body: carve(c.map(d => ({
          k: d.d, v: d.human, label: `${d.human} 次　${d.turns} 轮　${fmt(d.tok_in + d.tok_cache_r)}`,
          attr: `data-day="${esc(d.d)}"`,
        }))),
      })).join('');

  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
}
