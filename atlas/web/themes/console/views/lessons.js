import { esc, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, table, warn, meter } from '../kit.js';

export async function render(host) {
  const L = D.lessons();
  if (!L) { host.innerHTML = warn('<b>状态：没做。</b>这一页的数据还没生成。'); return; }
  const mxPer = Math.max(1, ...L.pain.map(p => p.per));

  host.innerHTML = `
${sec('REPEATED ASKS', esc(L.note))}
${warn('<b>一个问题被反复问，说明上一次的答案没留下来。</b>这是「下一次该先固化什么」的清单，不是批评。')}
${table([{ t: '次数', r: true }, { t: '横跨', r: true }, { t: '问的是什么' }, { t: '项目' }],
  L.repeats.map(r => [`<b>${r.n}</b>`, `${r.days} 天`,
    `${esc(r.text)}<br><span class="tag"><span class="lnk" data-day="${r.first}">${r.first}</span> → <span class="lnk" data-day="${r.last}">${r.last}</span></span>`,
    r.projects.map(p => `<span class="tag">${esc(p)}</span>`).join('')]))}

${sec('MOST DRAINING', '按「每场会话平均提到多少次报错」排。不是哪个项目 bug 多，是哪个项目最消耗你。')}
${table([{ t: '项目' }, { t: '每场提报错', r: true }, { t: '会话', r: true }, { t: '' }],
  L.pain.map(p => [esc(p.name), p.per.toFixed(1), String(p.sessions), meter(p.per, mxPer, 120)]))}

${sec('LONGEST TEN', '你说话次数最多的会话。一场里说了几百次，通常意味着那次没有一遍过。')}
${table([{ t: '日期' }, { t: '你说', r: true }, { t: '标题' }, { t: '主题' }],
  L.longest.map(x => [`<span class="lnk" data-day="${x.day}">${x.day}</span>`, `<b>${x.turns}</b>`,
    `<span class="tag">${esc(x.title || '(无标题)')}</span>`,
    x.topics.map(t => `<span class="tag" style="color:${topicColor(t)}">${esc(t)}</span>`).join('') || '<span class="tag">未分类</span>']))}

${sec('REVISITED', '回去过的项目。')}
${table([{ t: '项目' }, { t: '你开口', r: true }, { t: '起止' }, { t: '谈过上线' }],
  L.revisit.map(p => [esc(p.name), String(p.human), `<span class="tag">${p.first} → ${p.last}</span>`,
    `<span class="st" data-s="${p.shipped ? '通' : '没做'}">${p.shipped ? '谈过' : '没谈过'}</span>`]))}`;

  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  enter('.sec, tbody tr', host);
}
