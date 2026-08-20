import { esc, fmt, go, day as loadDay, hhmm, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, bento, drawer, table, warn, pill, rate } from '../kit.js';

export async function render(host, arg) {
  const list = D.days().map(d => d.d);
  const cur = list.includes(arg) ? arg : list[list.length - 1];
  const i = list.indexOf(cur);
  host.innerHTML = `
<div class="ctl">
  <button id="prev" ${i > 0 ? '' : 'disabled'}>← 上一天</button>
  <select id="pick">${list.slice().reverse().map(d => `<option ${d === cur ? 'selected' : ''}>${d}</option>`).join('')}</select>
  <button id="next" ${i < list.length - 1 ? '' : 'disabled'}>下一天 →</button>
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

  const card = s => `
<div class="card w6 sess ${s.kind === 'human' ? '' : 'mach'}">
  <div class="ck">${hhmm(s.start)}　${esc(s.source)}${s.project ? ' · ' + esc(s.project) : ''}
    ${s.kind === 'fanout' ? ` · <b style="color:var(--warn)">扇出</b>` : s.kind === 'auto' ? ` · <b style="color:var(--warn)">机器</b>` : ''}</div>
  <div style="font-family:var(--disp);font-weight:640;font-size:19px;letter-spacing:-.02em;margin:6px 0 8px">${esc(s.title || '(无标题)')}</div>
  <div>${s.topics.map(t => `<span class="pill" style="border-color:${topicColor(t)};color:${topicColor(t)}">${esc(t)}</span>`).join('')}</div>
  <div class="cn" style="margin-top:8px">你说 ${s.turns} 次 · 工具 ${s.tools} 次 · 跨度 ${s.span_min} 分
    ${s.models.length ? ' · ' + esc(s.models.join('/')) : ''}
    ${(s.tok_in || s.tok_out) ? ` · token 入 ${fmt(s.tok_in)} 出 ${fmt(s.tok_out)}` : ''}</div>
  ${(s.prompts || []).slice(0, 3).map(p => `<div class="quote">${esc(p)}</div>`).join('')}
</div>`;

  host.querySelector('#body').innerHTML = `
${sec(`${cur} ${wd}`)}
${bento([
  { k: '你开口', v: String(meta.human), n: `机器 ${meta.n - meta.human} 场`, w: 3, tone: 'acc' },
  { k: '有动静的钟点', v: String(meta.active_hours), n: '不等于工作时长', w: 3, alt: true },
  { k: 'token 输入(含缓存)', v: tk ? fmt(tk.input_total) : '—', n: tk ? `命中率 ${rate(tk.hit_rate)}` : '无用量记录' },
  { k: '主题', v: `<span style="font-size:20px">${Object.entries(meta.topics).sort((a,b)=>b[1]-a[1]).slice(0,2).map(([t])=>esc(t)).join('、') || '未分类'}</span>`,
    n: Object.entries(meta.topics).length + ' 类' },
])}
${human.length ? human.map(card).join('') : warn('这一天没有你亲自开口的会话。下面是机器跑的。')}
${mach.length ? `${sec(`机器跑的 ${mach.length} 场`, '列出来是为了让你能核对「剔掉的是什么」，不是凑数。')}
  ${mach.slice(0, 24).map(card).join('')}
  ${mach.length > 24 ? `<p class="hint">另有 ${mach.length - 24} 场同类，未展开。</p>` : ''}` : ''}`;

  const st = document.createElement('style');
  st.textContent = `.sess.mach{opacity:.5}
    .quote{margin-top:9px;padding:11px 15px;border-radius:14px;background:var(--line2);
      border-left:2px solid var(--acc);color:var(--dim);font-size:13.5px;white-space:pre-wrap;
      word-break:break-word;max-height:160px;overflow:auto}`;
  host.appendChild(st);
  enter('.sec, .card', host);
}
