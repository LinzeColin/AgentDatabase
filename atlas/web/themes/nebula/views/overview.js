import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { hero, sec, grid, orbit, slab, drawer, table, warn, pill, state, rate } from '../kit.js';

export async function render(host) {
  const m = D.meta(), all = D.slice(0), d7 = D.slice(7), d30 = D.slice(30);
  const L = all.ladder, tk = D.tokens().total;
  const money = Math.max(1, L['换钱'] || 0);
  const V = D.A().delivery || {};

  host.innerHTML = `
${hero('你的星图', `${m.days_active} 天，${m.sessions_human} 次开口`,
  `从 ${esc(m.first_day)} 到 ${esc(m.last_day)}。背景里每一颗星都是一条真实记录 ——
   往下滚，就是往回飞。`)}

${grid([
  { k: '你自己开口的', v: `<span data-cnt="${m.sessions_human}">0</span>`,
    n: `另外 ${m.sessions_auto} 次是机器在跑`, w: 3, tone: 'acc' },
  { k: '造东西 : 交出去 : 换到钱', v: `${Math.floor((L['建设'] || 0) / money)}:${Math.floor((L['交付'] || 0) / money)}:1`,
    n: `${L['建设'] || 0} / ${L['交付'] || 0} / ${L['换钱'] || 0}`, w: 3, tone: 'warn', alt: true },
  { k: '有记录的日子', v: `<span data-cnt="${m.days_active}">0</span>`, n: `${esc(m.first_day)} 起` },
  { k: '最近七天', v: String(d7.human), n: `${d7.days_active} 天里都在做` },
  { k: '最近三十天', v: String(d30.human), n: `${d30.days_active} 天里都在做` },
])}

${V.state === '通' ? warn(`<b>聊了 ${V.totals.days_talked} 天，真正提交代码的只有 ${V.totals.days_shipped} 天。</b>
  有 ${V.totals.days_talk_only} 天只聊没交付。这不等于白干 —— 那天可能在读、在想、在做不进 git 的事
  （Excel、方案、视频）。但它是两个互不知情的来源对出来的，不是我推的。`) : ''}

${sec('时间花在哪', '只算你自己开口的。一次对话最多算三个主题。点一条进明细。')}
${orbit(Object.entries(all.topics).sort((a, b) => b[1] - a[1]).map(([t, n]) => ({
  k: t, v: n, c: topicColor(t), attr: `data-topic="${esc(t)}"`,
})).concat([{ k: '没认出在做什么', v: all.unclassified, c: 'var(--dim2)' }]))}

${sec('几件数出来的事', '全部从记录里直接数的，没有一句是编的。')}
${grid(D.insights().map(i => ({
  kHtml: `${state(i.t === 'warn' ? '说不准' : '看这里')}　${esc(i.k)}`, k: i.k,
  v: `<span style="font-size:26px">${esc(i.v)}</span>`, n: esc(i.d), w: 3,
})))}

${sec('往哪走、哪里有口子', esc((D.opportunities() || {}).caveat || ''))}
${((D.opportunities() || {}).items || []).map(o => `
  <div class="slab">
    <div class="ck">${esc(o.k)}　<span style="color:var(--dim2)">依据：${esc(o.from)}</span></div>
    <div class="cv acc" style="font-size:34px">${esc(o.v)}</div>
    <div class="cn" style="margin:8px 0 14px">${esc(o.d)}</div>
    ${(o.list || []).map(x => pill(x)).join('')}
  </div>`).join('')}
`;
  host.querySelectorAll('[data-cnt]').forEach(el => countUp(el, +el.dataset.cnt));
  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  enter('.hero, .sec, .cell, .orow, .slab', host);
}
