import { esc, fmt, go, day as loadDay, hhmm, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { hero, sec, grid, slab, drawer, table, warn, pill, rate } from '../kit.js';

export async function render(host, arg) {
  const list = D.days().map(d => d.d);
  const cur = list.includes(arg) ? arg : list[list.length - 1];
  const i = list.indexOf(cur);
  host.innerHTML = `
<div class="ctl">
  <button id="prev" ${i > 0 ? '' : 'disabled'}>← 前一天</button>
  <select id="pick">${list.slice().reverse().map(d => `<option ${d === cur ? 'selected' : ''}>${d}</option>`).join('')}</select>
  <button id="next" ${i < list.length - 1 ? '' : 'disabled'}>后一天 →</button>
</div><div id="body"><p class="hint">读取中…</p></div>`;
  host.querySelector('#pick').onchange = e => go('day', e.target.value);
  host.querySelector('#prev').onclick = () => i > 0 && go('day', list[i - 1]);
  host.querySelector('#next').onclick = () => i < list.length - 1 && go('day', list[i + 1]);

  const j = await loadDay(cur);
  const meta = D.days().find(x => x.d === cur) || { human: 0, n: 0, active_hours: 0, topics: {} };
  const tk = D.tokens().by_day.find(x => x.d === cur);
  const human = j.sessions.filter(s => s.kind === 'human');
  const mach = j.sessions.filter(s => s.kind !== 'human');
  const wd = ['周一','周二','周三','周四','周五','周六','周日'][(new Date(cur + 'T00:00:00Z').getUTCDay() + 6) % 7];

  const card = s => slab(`
  <div class="ck">${hhmm(s.start)}　${esc(s.source)}${s.project ? '　' + esc(s.project) : ''}
    ${s.kind === 'fanout' ? '　同一批扇出去的' : s.kind === 'auto' ? '　机器自己跑的' : ''}</div>
  <div class="stitle">${esc(s.title || '(没有标题)')}</div>
  <div>${s.topics.map(t => `<span class="pill" style="border-color:${topicColor(t)};color:${topicColor(t)}">${esc(t)}</span>`).join('')}</div>
  <div class="cn">你说 ${s.turns} 次 · 用工具 ${s.tools} 次 · 前后 ${s.span_min} 分钟
    ${s.models.length ? '　' + esc(s.models.join(' / ')) : ''}
    ${(s.tok_in || s.tok_out) ? `　token 进 ${fmt(s.tok_in)} 出 ${fmt(s.tok_out)}` : ''}</div>
  ${(s.prompts || []).slice(0, 3).map(p => `<div class="quote">${esc(p)}</div>`).join('')}`);

  host.querySelector('#body').innerHTML = `
${hero(wd, cur, `这一天你开口 ${meta.human} 次，机器跑了 ${meta.n - meta.human} 次。下面是原话。`)}
${grid([
  { k: '你开口', v: String(meta.human), n: `机器另跑 ${meta.n - meta.human} 场`, w: 3, tone: 'acc' },
  { k: '有动静的钟点', v: String(meta.active_hours), n: '这不等于工作时长', w: 3 },
  { k: '读进 token', v: tk ? fmt(tk.input_total) : '—', n: tk ? `命中缓存 ${rate(tk.hit_rate)}` : '这天没有用量记录', w: 3 },
  { k: '在做什么', v: `<span style="font-size:22px">${Object.entries(meta.topics).sort((a,b)=>b[1]-a[1]).slice(0,2).map(([t])=>esc(t)).join('、') || '没认出来'}</span>`,
    n: Object.entries(meta.topics).length + ' 类', w: 3 },
])}
${sec('你说的话')}
${human.length ? human.map(card).join('') : warn('这一天你没有亲自开口。下面全是机器跑的。')}
${mach.length ? sec(`机器跑的 ${mach.length} 场`, '列出来是让你能核对「被剔掉的到底是什么」，不是凑数。')
  + mach.slice(0, 24).map(card).join('')
  + (mach.length > 24 ? `<p class="hint">还有 ${mach.length - 24} 场同类，没展开。</p>` : '') : ''}`;
  enter('.hero, .sec, .cell, .slab', host);
}
