import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, lede, p, n, big, aside, figure, rank, spark, table, rate } from '../kit.js';

export async function render(host) {
  const days = D.days(), byDay = new Map(days.map(d => [d.d, d]));
  const tokDay = new Map(D.tokens().by_day.map(r => [r.d, r]));
  const first = days[0].d, last = days[days.length - 1].d;
  let mode = 'time', timeN = 0, sessN = 200, from = first, to = last, metric = 'human';

  host.innerHTML = `
${sec('日历')}
${lede(`从 ${n(first)} 到 ${n(last)}，${big(days.length)} 个留下过记录的日子。
  下面的格子是全历史 —— 切片只改变高亮范围，不会把格子藏起来。`)}
<div class="ctl">
  <button data-mode="time" aria-pressed="true">时间切片</button>
  <button data-mode="session" aria-pressed="false">会话切片</button>
  <button data-mode="range" aria-pressed="false">自定义区间</button>
  <span id="ctlslot"></span>
  <select id="metric"><option value="human">你开口的会话</option><option value="all">全部会话</option>
    <option value="turns">你说话次数</option><option value="input">token 输入</option>
    <option value="hit">缓存命中率</option></select>
</div>
<div id="sum"></div><div id="cal"></div><div id="rest"></div>`;

  const ctlslot = host.querySelector('#ctlslot');
  const drawCtl = () => {
    if (mode === 'time') {
      ctlslot.innerHTML = `<select id="tn">${[3,7,15,30,45,60,90,180,0].map(v=>
        `<option value="${v}" ${timeN===v?'selected':''}>${v?`最近 ${v} 天`:`全历史 ${days.length} 天`}</option>`).join('')}</select>`;
      ctlslot.querySelector('#tn').onchange = e => { timeN = +e.target.value; draw(); };
    } else if (mode === 'session') {
      ctlslot.innerHTML = `<select id="sn">${[50,100,200,400,800,0].map(v=>
        `<option value="${v}" ${sessN===v?'selected':''}>${v?`最近 ${v} 场`:'全部会话'}</option>`).join('')}</select>`;
      ctlslot.querySelector('#sn').onchange = e => { sessN = +e.target.value; draw(); };
    } else {
      ctlslot.innerHTML = `<input type="date" id="f" value="${from}" min="${first}" max="${last}">
        <input type="date" id="t" value="${to}" min="${first}" max="${last}">`;
      ctlslot.querySelector('#f').onchange = e => { from = e.target.value; draw(); };
      ctlslot.querySelector('#t').onchange = e => { to = e.target.value; draw(); };
    }
  };
  const resolve = () => {
    if (mode === 'session') {
      const sel = D.lastNSessions(sessN || 1e9, metric === 'all' ? 'all' : 'human');
      const ds = new Set(sel.map(s => s.d));
      return { sessions: sel, dayset: ds, label: sessN ? `最近 ${sessN} 场会话` : '全部会话' };
    }
    let f = from, t = to;
    if (mode === 'time') { t = last; f = timeN ? days[Math.max(0, days.length - timeN)].d : first; }
    return { sessions: D.sessions({ kind: metric === 'all' ? 'all' : 'human', from: f, to: t }),
      dayset: new Set(days.filter(d => d.d >= f && d.d <= t).map(d => d.d)), label: `${f} → ${t}` };
  };
  const valueOf = d => {
    const row = byDay.get(d), tk = tokDay.get(d);
    if (!row) return 0;
    return metric === 'human' ? row.human : metric === 'all' ? row.n : metric === 'turns' ? row.turns
      : metric === 'input' ? (tk ? tk.input_total : 0) : (tk && tk.hit_rate != null ? tk.hit_rate * 100 : 0);
  };
  const draw = () => {
    const { sessions, dayset, label } = resolve();
    const agg = D.aggregate(sessions);
    host.querySelector('#sum').innerHTML = p(`当前切片是 <b>${esc(label)}</b>，
      落在 ${n(dayset.size)} 天里，共 ${big(agg.n)} 场会话。
      你说话 ${n(agg.turns)} 次，工具被调用 ${n(agg.tools)} 次，
      读进 ${n(agg.input_total)} 个 token（含缓存），命中率 ${rate(agg.hit)}。
      其中 ${n(agg.unclassified)} 场未分类。`);

    const vals = days.map(d => valueOf(d.d)).filter(v => v > 0).sort((a, b) => a - b);
    const q = pp => vals.length ? vals[Math.min(vals.length - 1, Math.floor(vals.length * pp))] : 1;
    const t1 = q(.25), t2 = q(.5), t3 = q(.8);
    const lv = v => v <= 0 ? 0 : v <= t1 ? 1 : v <= t2 ? 2 : v <= t3 ? 3 : 4;
    const months = new Map();
    for (let t = new Date(first + 'T00:00:00Z'); t <= new Date(last + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + 1)) {
      const iso = t.toISOString().slice(0, 10), k = iso.slice(0, 7);
      if (!months.has(k)) months.set(k, []);
      months.get(k).push(iso);
    }
    const pad = l => '<i data-pad="1"></i>'.repeat((new Date(l[0] + 'T00:00:00Z').getUTCDay() + 6) % 7);
    host.querySelector('#cal').innerHTML = figure(
      `<div class="calwrap">${[...months].map(([mm, l]) =>
        `<div class="calmon"><span>${mm.slice(2).replace('-', '/')}</span><div class="calgrid">${pad(l)}${
          l.map(iso => `<i data-day="${iso}" data-lv="${lv(valueOf(iso))}" ${dayset.has(iso) ? '' : 'data-out="1"'}
            title="${iso}　${metric === 'input' ? fmt(valueOf(iso)) : valueOf(iso).toFixed(metric === 'hit' ? 1 : 0)}"></i>`).join('')
        }</div></div>`).join('')}</div>`,
      `分界 ${[t1, t2, t3].map(v => metric === 'input' ? fmt(v) : v.toFixed(metric === 'hit' ? 1 : 0)).join(' / ')}
       —— 按你自己的分布取四分位，不是拍脑袋定的。淡掉的格子＝不在当前切片内，不是没有数据。`);

    host.querySelector('#rest').innerHTML = sec('这段时间在做什么')
      + figure(rank(agg.topics.map(([t, v]) => ({ k: t, v, label: String(v), attr: `data-topic="${esc(t)}"` }))), '主题构成。')
      + figure(table([{ t: '日期' }, { t: '你开口', r: true }, { t: '机器', r: true }, { t: '钟点', r: true }, { t: '主题' }],
        days.filter(d => dayset.has(d.d)).slice(-45).reverse().map(d => [
          `<span class="lnk" data-day="${d.d}">${d.d}</span>`, String(d.human), String(d.n - d.human),
          String(d.active_hours),
          Object.entries(d.topics).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([t, v]) => `<span class="kw">${esc(t)} ${v}</span>`).join('')])),
        '逐日明细（最近 45 天）。');
    enter('figure, p.body', host);
  };
  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-mode]'); if (!b) return;
    mode = b.dataset.mode;
    host.querySelectorAll('[data-mode]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.mode === mode)));
    drawCtl(); draw();
  });
  host.querySelector('#metric').onchange = e => { metric = e.target.value; draw(); };
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]'); if (d) return go('day', d.dataset.day);
    const t = e.target.closest('[data-topic]'); if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  const st = document.createElement('style');
  st.textContent = `
    .calwrap{display:flex;gap:4px;overflow-x:auto}
    .calmon{display:flex;flex-direction:column;gap:5px}
    .calmon>span{font:10px var(--sans);color:var(--dim2);height:12px;letter-spacing:.08em}
    .calgrid{display:grid;grid-auto-flow:column;grid-template-rows:repeat(7,11px);gap:3px}
    .calgrid i{width:11px;height:11px;cursor:pointer;background:var(--rule2);border:.5px solid var(--rule)}
    .calgrid i[data-pad]{visibility:hidden;border:none}
    .calgrid i:hover{outline:1px solid var(--fg)}
    .calgrid i[data-out]{opacity:.25}
    .calgrid i[data-lv="1"]{background:color-mix(in srgb,var(--acc) 22%,var(--rule2))}
    .calgrid i[data-lv="2"]{background:color-mix(in srgb,var(--acc) 46%,var(--rule2))}
    .calgrid i[data-lv="3"]{background:color-mix(in srgb,var(--acc) 70%,var(--rule2))}
    .calgrid i[data-lv="4"]{background:var(--acc)}`;
  host.appendChild(st);
  drawCtl(); draw(); enter('.sec, p.body, figure, .aside', host);
}
