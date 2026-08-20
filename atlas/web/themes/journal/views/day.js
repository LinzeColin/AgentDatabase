import { esc, fmt, go, day as loadDay, hhmm, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, lede, p, n, big, aside, note, figure, rate } from '../kit.js';

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
  const topStr = Object.entries(meta.topics).sort((a, b) => b[1] - a[1]).slice(0, 3)
    .map(([t, v]) => `<b>${esc(t)}</b>（${v}）`).join('、') || '未分类';

  const entry = s => `
<div class="entry ${s.kind === 'human' ? '' : 'mach'}">
  <div class="eh"><span class="et">${hhmm(s.start)}</span>
    <span class="ett">${esc(s.title || '(无标题)')}</span></div>
  <div class="em">${esc(s.source)}${s.project ? ' · ' + esc(s.project) : ''}
    · 你说 ${s.turns} 次 · 工具 ${s.tools} 次 · 跨度 ${s.span_min} 分
    ${s.topics.length ? ' · ' + s.topics.map(t => esc(t)).join('、') : ''}
    ${s.kind !== 'human' ? ' · <b>机器</b>' : ''}</div>
  ${(s.prompts || []).slice(0, 3).map(x => `<blockquote>${esc(x)}</blockquote>`).join('')}
</div>`;

  host.querySelector('#body').innerHTML = `
${sec(`${cur}　${wd}`)}
${lede(`这一天你开了 ${big(meta.human)} 场会话，机器另跑了 ${n(meta.n - meta.human)} 场。
  动静分布在 ${n(meta.active_hours)} 个不同的钟点里 —— 这是「有动静的钟点数」，不是你连续干了这么久。
  主要在做 ${topStr}。${tk ? `模型读进 ${n(tk.input_total)} 个 token，命中率 ${rate(tk.hit_rate)}。` : '这一天没有 token 用量记录。'}`)}
${human.length ? human.map(entry).join('') : note('这一天没有你亲自开口的会话。下面是机器跑的。')}
${mach.length ? sec(`机器跑的 ${mach.length} 场`, '列出来是为了让你能核对「剔掉的是什么」，不是凑数。')
  + mach.slice(0, 24).map(entry).join('')
  + (mach.length > 24 ? p(`另有 ${mach.length - 24} 场同类，未展开。`) : '') : ''}`;

  const st = document.createElement('style');
  st.textContent = `
    .entry{margin:26px 0;padding-bottom:22px;border-bottom:1px solid var(--rule2)}
    .entry.mach{opacity:.5}
    .eh{display:flex;gap:14px;align-items:baseline}
    .et{font:11px var(--sans);letter-spacing:.1em;color:var(--dim2);flex:none;width:44px}
    .ett{font-size:19px;font-weight:600;line-height:1.4}
    .em{font:11.5px var(--sans);color:var(--dim2);margin:6px 0 0 58px;letter-spacing:.01em}
    .em b{color:var(--warn)}
    blockquote{margin:12px 0 0 58px;padding-left:16px;border-left:2px solid var(--rule);
      color:var(--dim);font-size:15.5px;font-style:italic;white-space:pre-wrap;word-break:break-word;
      max-height:170px;overflow:auto}`;
  host.appendChild(st);
  enter('.sec, p.body, .entry', host);
}
