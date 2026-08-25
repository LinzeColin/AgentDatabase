import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 总览。**这一屏只回答一个问题：你自己开口了多少次。**
// 琉璃版把 5 张卡摊开让你扫，这里只留一个大数 —— 其余降级成注脚与射线。
export async function render(host) {
  const m = D.meta(), all = D.slice(0), d7 = D.slice(7), d30 = D.slice(30);
  const L = all.ladder, V = D.A().delivery || {};
  const money = Math.max(1, L['换钱'] || 0);

  hud([
    { k: '天', v: String(m.days_active) },
    { k: '最近七天', v: String(d7.human) },
    { k: '最近三十天', v: String(d30.human) },
  ]);

  host.innerHTML = stage({
    eyebrow: `${esc(m.first_day)} → ${esc(m.last_day)}`,
    title: '你的星图',
    hint: `背景里每一颗星都是一条真实记录。<b>往下滚就是往回飞</b> —— 这一屏的滚动直接开着镜头。`,
    body: headline('你自己开口的次数', `<span data-cnt="${m.sessions_human}">0</span>`,
      `另外 ${fmt(m.sessions_auto)} 次是机器在跑 —— 那部分不算你`)
      + reads([
        { k: '造 : 交 : 换到钱', tone: 'warn',
          v: `${Math.floor((L['建设'] || 0) / money)}:${Math.floor((L['交付'] || 0) / money)}:1`,
          n: `${L['建设'] || 0} / ${L['交付'] || 0} / ${L['换钱'] || 0}` },
        { k: '有记录的日子', v: String(m.days_active), n: `${esc(m.first_day)} 起` },
        { k: '最近七天', v: String(d7.human), n: `${d7.days_active} 天里都在做` },
        { k: '最近三十天', v: String(d30.human), n: `${d30.days_active} 天里都在做` },
      ])
      + (V.state === '通' ? warn(`<b>聊了 ${V.totals.days_talked} 天，真正提交代码的只有 ${V.totals.days_shipped} 天。</b>
          有 ${V.totals.days_talk_only} 天只聊没交付 —— 不等于白干（可能在读、在想、在做不进 git 的事），
          但它是两个互不知情的来源对出来的。`) : '')
      + `<p class="hint" style="margin-top:22px">时间花在哪 —— 只算你自己开口的，一次对话最多算三个主题。</p>`
      + beams(Object.entries(all.topics).sort((a, b) => b[1] - a[1]).map(([t, n]) => ({
          k: t, v: n, c: topicColor(t), attr: `data-topic="${esc(t)}"`,
        })).concat([{ k: '没认出在做什么', v: all.unclassified, c: 'var(--ink3)' }]))
      + sheet('几件数出来的事', D.insights().map(i =>
          `<p style="margin:0 0 12px"><b>${esc(i.k)}</b>${state(i.t === 'warn' ? '说不准' : '看这里')}<br>
           <span style="font-family:var(--mono);color:var(--acc)">${esc(i.v)}</span><br>
           <span style="color:var(--ink3);font-size:12px">${esc(i.d)}</span></p>`).join('')),
  });

  host.querySelectorAll('[data-cnt]').forEach(el => countUp(el, +el.dataset.cnt));
  host.querySelector('.beams')?.addEventListener('click', e => {
    const b = e.target.closest('[data-topic]');
    if (b) go('grid', b.dataset.topic);
  });
  enter('.headline, .read, .beam, .sheet', host);
}
