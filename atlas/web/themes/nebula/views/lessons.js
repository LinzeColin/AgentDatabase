import { esc, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { flyToDay } from '../shell.js';
import { hero, sec, grid, orbit, slab, drawer, table, warn, pill, state } from '../kit.js';

export async function render(host) {
  const L = D.lessons();
  if (!L) {
    host.innerHTML = hero('复盘', '这一页还没数据', '') + warn('<b>没做。</b>这一页要的数据还没生成出来。');
    enter('.hero', host); return;
  }
  host.innerHTML = `
${hero('复盘', '同一件事，你问过几遍', esc(L.note))}
${warn(`<b>一个问题被反复问，说明上一次的答案没留下来。</b>
  这是「下一次该先把什么写下来」的清单，不是在挑你毛病。`)}

${L.repeats.slice(0, 14).map(r => slab(`
  <div class="ck">问了 ${r.n} 遍 · 前后横跨 ${r.days} 天 ·
    <span class="lnk" data-day="${r.first}">${r.first}</span> →
    <span class="lnk" data-day="${r.last}">${r.last}</span></div>
  <div style="font-size:14.5px;color:var(--fg);margin:9px 0 11px;line-height:1.65">${esc(r.text)}</div>
  ${r.projects.map(p => pill(p)).join('')}`)).join('')}
${drawer(`摊开全部 ${L.repeats.length} 组`,
  table([{ t: '遍数', r: true }, { t: '横跨', r: true }, { t: '问的是什么' }],
    L.repeats.map(r => [String(r.n), `${r.days} 天`, esc(r.text)])))}

${sec('最耗你的项目', '按「每场会话里 error/报错 这个词出现几次」排 —— 是<b>消耗代理</b>，不是 bug 数。'
  + '一段贴进来的日志能一次贡献上百次。它回答的是「哪个项目最磨你」。')}
${orbit(L.pain.map(p => ({ k: p.name, v: p.per,
  label: `${p.per.toFixed(1)} 次提及/场（共 ${p.sessions} 场）`, c: 'var(--warn)' })))}

${sec('最长的十场', '你说话次数最多的会话。一场说了几百次，通常意味着那次没一遍过。')}
${orbit(L.longest.map(x => ({ k: x.day, v: x.turns,
  label: `${x.turns} 次 · ${esc((x.title || '').slice(0, 26))}`, attr: `data-day="${x.day}"` })))}

${sec('回头又捡起来的项目')}
${drawer('摊开', table([{ t: '项目' }, { t: '你开口', r: true }, { t: '起止' }, { t: '谈过上线没有' }],
  L.revisit.map(p => [esc(p.name), String(p.human), `${p.first} → ${p.last}`,
    state(p.shipped ? '通' : '没做')])))}`;

  host.addEventListener('mouseover', e => {
    const d = e.target.closest('[data-day]'); if (d) flyToDay(d.dataset.day);
  });
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day);
  });
  enter('.hero, .sec, .slab, .orow', host);
}
