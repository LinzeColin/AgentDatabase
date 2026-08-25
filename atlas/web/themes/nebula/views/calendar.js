import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 日历。星云版不画热力网格 —— 网格是琉璃的做法。
// 这里把每一天变成一条射线，最忙的那天最长；点一条飞到那天。
export async function render(host) {
  const ds = D.days();
  const peak = ds.reduce((a, b) => (b.human > (a?.human ?? -1) ? b : a), null);
  const active = ds.filter(d => d.human > 0);

  hud([
    { k: '有记录的天', v: String(active.length) },
    { k: '最忙一天', v: peak ? String(peak.human) : '—' },
  ]);

  host.innerHTML = stage({
    eyebrow: '时间 · 日历',
    title: '哪一天最重',
    hint: '一天一条光，长度是你那天开口的次数。<b>点一条进那天的明细。</b>',
    body: headline('最忙的一天', peak ? esc(peak.d) : '—',
      peak ? `${peak.human} 次开口 · ${peak.turns} 轮 · ${fmt(peak.tok_in + peak.tok_cache_r)} token` : '')
      + reads([
        { k: '有记录的天', v: String(active.length), n: `共 ${ds.length} 天有数据` },
        { k: '平均每天', v: (active.reduce((s, d) => s + d.human, 0) / Math.max(1, active.length)).toFixed(1), n: '只算有记录的天' },
        { k: '一次都没开口', v: String(ds.length - active.length), n: '机器在跑，你没说话' },
      ])
      + beams(ds.slice().reverse().slice(0, 60).map(d => ({
          k: d.d, v: d.human, sub: `${d.turns} 轮`,
          label: `${d.human} 次`, c: 'var(--acc)', attr: `data-day="${esc(d.d)}"`,
        })))
      + sheet(`全部 ${ds.length} 天`, table(
          [{ t: '日期' }, { t: '你开口', r: true }, { t: '机器', r: true }, { t: '轮次', r: true }, { t: 'token', r: true }],
          ds.slice().reverse().map(d => [`<a href="#/day/${esc(d.d)}" style="color:var(--acc)">${esc(d.d)}</a>`,
            String(d.human), String(d.auto), String(d.turns), fmt(d.tok_in + d.tok_cache_r)]))),
  });

  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
  enter('.headline, .read, .beam', host);
}
