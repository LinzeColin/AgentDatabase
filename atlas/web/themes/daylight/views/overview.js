import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { hero, sec, grid, orbit, slab, drawer, table, warn, pill, state } from '../kit.js';

export async function render(host) {
  const m = D.meta(), all = D.slice(0), d7 = D.slice(7), d30 = D.slice(30);
  const L = all.ladder, money = Math.max(1, L['换钱'] || 0);
  const V = D.A().delivery || {};

  host.innerHTML = `
${hero(`${esc(m.first_day)} — ${esc(m.last_day)}`, '三个月，都在这儿了',
  `${m.days_active} 天有记录，你亲自开口 ${m.sessions_human} 次。
   这一页只放数出来的东西 —— 每一个数字后面都能点到原始记录。`)}

${grid([
  { k: '你自己开口', v: `<span data-cnt="${m.sessions_human}">0</span>`,
    n: `另有 ${m.sessions_auto} 次是机器在跑，已剔除`, w: 3, tone: 'acc' },
  { k: '有记录的日子', v: `<span data-cnt="${m.days_active}">0</span>`, n: `${esc(m.first_day)} 起` },
  { k: '最近 7 天', v: String(d7.human), n: `${d7.days_active} 天有动静` },
  { k: '最近 30 天', v: String(d30.human), n: `${d30.days_active} 天有动静` },
])}

${sec('造东西 : 交出去 : 换到钱', '这是这整个仓库存在的原因。三个数摆在一起，比任何一句总结都直接。')}
<div class="grid">
  <div class="cell w6">
    <div class="ck">比例</div>
    <div class="cv warn" style="font-size:clamp(40px,9vw,96px)">${Math.floor((L['建设'] || 0) / money)} : ${Math.floor((L['交付'] || 0) / money)} : 1</div>
    <div class="cn">造东西 ${L['建设'] || 0} 场　交出去 ${L['交付'] || 0} 场　换到钱 ${L['换钱'] || 0} 场</div>
  </div>
  <div class="cell w6">
    <div class="ck">读法</div>
    <div class="cn" style="font-size:13.5px;line-height:1.75;margin-top:0">
      左边这个数越大，说明你越多时间在<b>把东西做出来</b>；右边那个 1 越孤单，
      说明做出来的东西<b>越少走到能收钱那一步</b>。<br><br>
      这不是评价 —— 它只是把「三个月很忙但没赚到钱」这件事，换成了一个可以逐周去推的数。
    </div>
  </div>
</div>

${V.state === '通' ? warn(`<b>聊了 ${V.totals.days_talked} 天，真正提交代码的只有 ${V.totals.days_shipped} 天，
  有 ${V.totals.days_talk_only} 天只聊没交付。</b>
  这不等于白干 —— 那天可能在读、在想、在做不进 git 的事。
  但它是两个互不知情的来源（本机会话、GitHub）对出来的，不是我推的。`) : ''}

${sec('时间花在哪', '只算你自己开口的。一场对话最多算三个主题，所以加起来会超过总场次。点一行进明细。')}
${orbit(Object.entries(all.topics).sort((a, b) => b[1] - a[1]).map(([t, n]) => ({
  k: t, v: n, attr: `data-topic="${esc(t)}"`,
})).concat([{ k: '没认出在做什么', v: all.unclassified }]))}

${sec('几件数出来的事', '全部从记录里直接数的，没有一句是编的。')}
<div class="grid">${D.insights().map(i => `
  <div class="cell w6">
    <div class="ck">${state(i.t === 'warn' ? '说不准' : '看这里')}　${esc(i.k)}</div>
    <div class="cv" style="font-size:29px">${esc(i.v)}</div>
    <div class="cn">${esc(i.d)}</div>
  </div>`).join('')}</div>

${sec('往哪走、哪里有口子', esc((D.opportunities() || {}).caveat || ''))}
${((D.opportunities() || {}).items || []).map(o => slab(`
  <div class="ck">${esc(o.k)}　·　依据：${esc(o.from)}</div>
  <div class="cv acc">${esc(o.v)}</div>
  <div class="cn" style="margin:10px 0 14px;max-width:70ch">${esc(o.d)}</div>
  ${(o.list || []).map(x => pill(x)).join('')}`)).join('')}
`;
  host.querySelectorAll('[data-cnt]').forEach(el => countUp(el, +el.dataset.cnt));
  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  enter('.hero, .sec, .cell, .orow, .slab', host);
}
