import { S, esc, day, hhmm, go, topicColor } from '../app.js';

export async function render(host, arg) {
  const a = S.atlas;
  const days = a.days.map(d => d.d);
  const cur = days.includes(arg) ? arg : days[days.length - 1];
  const i = days.indexOf(cur);
  const prev = i > 0 ? days[i - 1] : '', next = i < days.length - 1 ? days[i + 1] : '';

  host.innerHTML = `<div class="flexbar">
      <button class="act" ${prev ? `data-day="${prev}"` : 'disabled'}>← 上一个有记录的日子</button>
      <select id="pick">${days.slice().reverse().map(d =>
        `<option value="${d}" ${d === cur ? 'selected' : ''}>${d}</option>`).join('')}</select>
      <button class="act" ${next ? `data-day="${next}"` : 'disabled'}>下一个 →</button>
    </div><div id="body"><div class="loading">读取中…</div></div>`;

  host.querySelector('#pick').addEventListener('change', e => go('day', e.target.value));
  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });

  const j = await day(cur);
  const d = a.days.find(x => x.d === cur) || { human: 0, n: 0, active_hours: 0, topics: {} };
  const human = j.sessions.filter(s => s.kind === 'human');
  const mach = j.sessions.filter(s => s.kind !== 'human');
  const wd = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][(new Date(cur + 'T00:00:00Z').getUTCDay() + 6) % 7];

  host.querySelector('#body').innerHTML = `
    <h2>${cur} ${wd}</h2>
    <p class="sub">你开口 ${d.human} 场 · 机器 ${d.n - d.human} 场 · ${d.active_hours} 个钟点里有动静
      ${Object.entries(d.topics).sort((x, y) => y[1] - x[1]).slice(0, 5)
        .map(([t, n]) => `<span class="chip" style="border-color:${topicColor(t)}">${esc(t)} ${n}</span>`).join('')}</p>
    ${human.length ? human.map(card).join('')
      : '<div class="note">这一天没有你亲自开口的会话。下面是机器跑过的。</div>'}
    ${mach.length ? `<h2 class="muted" style="font-size:15px">机器跑的 ${mach.length} 场</h2>
      <p class="sub">列出来是为了让你能核对「剔掉的是什么」，不是凑数。</p>
      ${mach.slice(0, 40).map(card).join('')}
      ${mach.length > 40 ? `<div class="muted" style="font-size:12.5px">另有 ${mach.length - 40} 场同类，未展开。</div>` : ''}` : ''}`;
}

function card(s) {
  const why = s.kind === 'fanout' ? `扇出（${esc(s.batch || '同一小时内大量启动')}）`
    : s.kind === 'auto' ? (s.batch ? `批处理：${esc(s.batch)}` : '无用户发言／单轮机器指令') : '';
  return `<div class="sess ${s.kind === 'human' ? '' : 'mach'}">
    <div class="hd">
      <span class="t">${hhmm(s.start)}</span>
      <span class="ti">${esc(s.title || '(无标题)')}</span>
      ${s.topics.map(t => `<span class="chip" style="border-color:${topicColor(t)}">${esc(t)}</span>`).join('')}
    </div>
    <div class="meta">${esc(s.source)}${s.project ? ' · ' + esc(s.project) : ''}
      · 你说了 ${s.turns} 次 · 工具 ${s.tools} 次 · 跨度 ${s.span_min} 分钟
      ${s.models.length ? ' · ' + esc(s.models.join('/')) : ''}
      ${why ? ' · <b>' + why + '</b>' : ''}</div>
    ${(s.prompts || []).slice(0, 4).map(p => `<div class="p">${esc(p)}</div>`).join('')}
  </div>`;
}
