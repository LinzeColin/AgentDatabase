import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

// 总览。**两页**：第一页是这本册子的题眼，第二页是时间去了哪。
export async function render(host) {
  const m = D.meta(), all = D.slice(0), d7 = D.slice(7), d30 = D.slice(30);
  const L = all.ladder, V = D.A().delivery || {};
  const money = Math.max(1, L['换钱'] || 0);

  host.innerHTML =
    leaf({
      title: '你的册子',
      lead: `${esc(m.first_day)} 到 ${esc(m.last_day)}，${m.days_active} 天。
             背景那道书口，<b>一片金页就是一天</b> —— 厚度是你开口的次数，
             外凸是那天的 token，磕碰过的页不反光。`,
      body: plate({ k: '你自己开口的次数', v: String(m.sessions_human), big: true,
        n: `另外 ${fmt(m.sessions_auto)} 次是机器在跑 —— 那部分不算你` })
        + plates([
          { k: '造 : 交 : 换到钱',
            v: `${Math.floor((L['建设'] || 0) / money)}:${Math.floor((L['交付'] || 0) / money)}:1`,
            size: 'sm', n: `${L['建设'] || 0} / ${L['交付'] || 0} / ${L['换钱'] || 0}` },
          { k: '有记录的日子', v: String(m.days_active), n: `${esc(m.first_day)} 起` },
          { k: '最近七天', v: String(d7.human), n: `${d7.days_active} 天里都在做` },
          { k: '最近三十天', v: String(d30.human), n: `${d30.days_active} 天里都在做` },
        ])
        + (V.state === '通' ? marginal(`<b>聊了 ${V.totals.days_talked} 天，真正提交代码的只有
            ${V.totals.days_shipped} 天。</b>有 ${V.totals.days_talk_only} 天只聊没交付 ——
            不等于白干，但它是两个互不知情的来源对出来的。`) : ''),
    })
    + leaf({
      title: '时间花在哪',
      lead: '只算你自己开口的。一次对话最多算三个主题，所以各主题之和大于总数。点一条进明细。',
      cols: false,
      body: carve(Object.entries(all.topics).sort((a, b) => b[1] - a[1]).map(([t, n]) => ({
          k: t, v: n, attr: `data-topic="${esc(t)}"`,
        })).concat([{ k: '没认出在做什么', v: all.unclassified }]))
        + h2('几件数出来的事')
        + D.insights().map(i => marginal(
            `<b>${esc(i.k)}</b>${seal(i.t === 'warn' ? '说不准' : '看这里')}<br>${esc(i.v)}<br>${esc(i.d)}`)).join(''),
    });

  host.addEventListener('click', e => {
    const b = e.target.closest('[data-topic]');
    if (b) go('grid', b.dataset.topic);
  });
}
