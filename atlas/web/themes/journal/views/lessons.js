import { esc, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, lede, p, n, big, aside, note, figure, rank, table, state } from '../kit.js';

export async function render(host) {
  const L = D.lessons();
  if (!L) { host.innerHTML = note('<b>状态：没做。</b>这一页的数据还没生成。'); return; }
  const top = L.repeats[0];
  host.innerHTML = `
${sec('沉淀')}
${lede(`把每一场会话的第一句话拿出来，前二十六个字一样的算同一件事。
  这样数下来，${top ? `问得最多的一件你问过 ${big(top.n)} 次，横跨 ${n(top.days)} 天` : '没有重复到三次以上的'}。`)}
${aside(esc(L.note))}
${note('<b>一个问题被反复问，说明上一次的答案没留下来。</b>这是「下一次该先固化什么」的清单，不是批评。')}
${L.repeats.slice(0, 12).map(r => p(`<b>${r.n} 次</b>　横跨 ${r.days} 天　
  <span class="lnk" data-day="${r.first}">${r.first}</span> → <span class="lnk" data-day="${r.last}">${r.last}</span><br>
  <span style="color:var(--dim);font-style:italic">${esc(r.text)}</span><br>
  <span class="kw">${r.projects.map(x => esc(x)).join('　')}</span>`)).join('')}
${figure(table([{ t: '次数', r: true }, { t: '横跨', r: true }, { t: '问的是什么' }],
  L.repeats.map(r => [String(r.n), `${r.days} 天`, esc(r.text.slice(0, 60))])), `全部 ${L.repeats.length} 组。`)}

${sec('最耗你的项目', '按每场会话平均提到多少次报错排。不是哪个项目 bug 多，是哪个项目最消耗你。')}
${figure(rank(L.pain.map(x => ({ k: x.name, v: x.per, label: `${x.per.toFixed(1)} / 场（${x.sessions} 场）` }))), '消耗排行。')}

${sec('最长的十场', '你说话次数最多的会话。一场里说了几百次，通常意味着那次没有一遍过。')}
${figure(rank(L.longest.map(x => ({ k: `${x.day}　${(x.title || '').slice(0, 26)}`, v: x.turns,
  label: `${x.turns} 次`, attr: `data-day="${x.day}"` }))), '按你说话次数降序。')}

${sec('回去过的项目')}
${figure(table([{ t: '项目' }, { t: '你开口', r: true }, { t: '起止' }, { t: '谈过上线' }],
  L.revisit.map(x => [esc(x.name), String(x.human), `${x.first} → ${x.last}`,
    `<span class="st" data-s="${x.shipped ? '通' : '没做'}">${x.shipped ? '谈过' : '没谈过'}</span>`])), '重复回访的项目。')}`;
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  enter('.sec, p.body, figure, .aside', host);
}
