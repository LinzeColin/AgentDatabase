import { esc, fmt, go, day as loadDay, hhmm, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, kv, table, warn, rate } from '../kit.js';

export async function render(host, arg) {
  const list = D.days().map(d => d.d);
  const cur = list.includes(arg) ? arg : list[list.length - 1];
  const i = list.indexOf(cur);

  host.innerHTML = `
<div class="ctl">
  <button id="prev" ${i > 0 ? '' : 'disabled'}>← 上一天</button>
  <select id="pick">${list.slice().reverse().map(d => `<option ${d === cur ? 'selected' : ''}>${d}</option>`).join('')}</select>
  <button id="next" ${i < list.length - 1 ? '' : 'disabled'}>下一天 →</button>
</div>
<div id="body"><p class="hint">读取中…</p></div>`;

  host.querySelector('#pick').addEventListener('change', e => go('day', e.target.value));
  host.querySelector('#prev').addEventListener('click', () => i > 0 && go('day', list[i - 1]));
  host.querySelector('#next').addEventListener('click', () => i < list.length - 1 && go('day', list[i + 1]));

  const j = await loadDay(cur);
  const meta = D.days().find(x => x.d === cur) || { human: 0, n: 0, active_hours: 0, topics: {} };
  const tk = D.tokens().by_day.find(x => x.d === cur);
  const human = j.sessions.filter(s => s.kind === 'human');
  const mach = j.sessions.filter(s => s.kind !== 'human');
  const wd = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][(new Date(cur + 'T00:00:00Z').getUTCDay() + 6) % 7];

  const card = s => `
<div class="sess ${s.kind === 'human' ? '' : 'mach'}">
  <div class="sh"><span class="t">${hhmm(s.start)}</span>
    <span class="ti">${esc(s.title || '(无标题)')}</span>
    ${s.topics.map(t => `<span class="tag" style="color:${topicColor(t)}">${esc(t)}</span>`).join('')}</div>
  <div class="sm">${esc(s.source)}${s.project ? ' · ' + esc(s.project) : ''}
    · 你说 ${s.turns} 次 · 工具 ${s.tools} 次 · 跨度 ${s.span_min} 分
    ${s.models.length ? ' · ' + esc(s.models.join('/')) : ''}
    ${(s.tok_in || s.tok_out) ? ` · token 入 ${fmt(s.tok_in)} 出 ${fmt(s.tok_out)}` : ''}
    ${s.kind === 'fanout' ? ` · <b>扇出：${esc(s.batch || '同一小时内大量启动')}</b>`
      : s.kind === 'auto' ? ` · <b>${s.batch ? '批处理：' + esc(s.batch) : '无用户发言／单轮机器指令'}</b>` : ''}</div>
  ${(s.prompts || []).slice(0, 4).map(p => `<pre class="sp">${esc(p)}</pre>`).join('')}
</div>`;

  host.querySelector('#body').innerHTML = `
${sec(`${cur} ${wd}`)}
${kv([
  ['你开口', String(meta.human), 'acc'], ['机器跑的', String(meta.n - meta.human), ''],
  ['有动静的钟点', String(meta.active_hours), ''],
  ['token 输入(含缓存)', tk ? fmt(tk.input_total) : '—', ''],
  ['缓存命中率', tk ? rate(tk.hit_rate) : '不确定', 'acc'],
  ['主题', Object.entries(meta.topics).sort((a, b) => b[1] - a[1]).slice(0, 3)
    .map(([t, n]) => `${esc(t)} ${n}`).join('、') || '未分类', ''],
])}
${human.length ? human.map(card).join('') : warn('这一天没有你亲自开口的会话。下面是机器跑的。')}
${mach.length ? `<div class="sec">MACHINE · ${mach.length}</div>
  <p class="hint">列出来是为了让你能核对「剔掉的是什么」，不是凑数。</p>
  ${mach.slice(0, 30).map(card).join('')}
  ${mach.length > 30 ? `<p class="hint">另有 ${mach.length - 30} 场同类，未展开。</p>` : ''}` : ''}`;

  const st = document.createElement('style');
  st.textContent = `
    .sess{border-left:2px solid var(--hair);padding:6px 0 6px 12px;margin:8px 0}
    .sess.mach{opacity:.5}
    .sh{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
    .sh .t{color:var(--dim2);font-size:11.5px}
    .sh .ti{color:var(--fg);flex:1;min-width:200px}
    .sm{color:var(--dim2);font-size:11px;margin-top:3px}
    .sm b{color:var(--warn);font-weight:400}
    .sp{margin:6px 0 0;padding:7px 10px;background:var(--hair2);border-left:2px solid var(--hair);
      color:var(--dim);font:12px/1.55 var(--mono);white-space:pre-wrap;word-break:break-word;
      max-height:150px;overflow:auto}`;
  host.appendChild(st);
  enter('.sess, .kv > div', host);
}
