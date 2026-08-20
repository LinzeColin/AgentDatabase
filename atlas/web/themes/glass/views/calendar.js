import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, bento, orbit, drawer, table, warn, pill, rate } from '../kit.js';

// Owner 明确要求：全量 + 自己能选的时间切片 **和** 会话切片。
export async function render(host) {
  const days = D.days(), byDay = new Map(days.map(d => [d.d, d]));
  const tokDay = new Map(D.tokens().by_day.map(r => [r.d, r]));
  const first = days[0].d, last = days[days.length - 1].d;
  let mode = 'time', timeN = 0, sessN = 200, from = first, to = last, metric = 'human';

  host.innerHTML = `
${sec('日历', '每格一天，全历史铺满。切片方式、口径、区间都可以自己选。')}
<div class="ctl">
  <button data-mode="time" aria-pressed="true">时间切片</button>
  <button data-mode="session" aria-pressed="false">会话切片</button>
  <button data-mode="range" aria-pressed="false">自定义区间</button>
  <span id="ctlslot"></span>
  <select id="metric">
    <option value="human">你开口的会话</option><option value="all">全部会话（含机器）</option>
    <option value="turns">你说话次数</option><option value="input">token 输入(含缓存)</option>
    <option value="hit">缓存命中率</option></select>
</div>
<div class="card w6" id="calcard"><div id="cal"></div></div>
<div id="sum"></div>
<div id="rest"></div>`;

  const ctlslot = host.querySelector('#ctlslot');
  const drawCtl = () => {
    if (mode === 'time') {
      ctlslot.innerHTML = `<select id="tn">${[['3','最近 3 天'],['7','最近 7 天'],['15','最近 15 天'],
        ['30','最近 30 天'],['45','最近 45 天'],['60','最近 60 天'],['90','最近 90 天'],
        ['180','最近 180 天'],['0',`全历史（${days.length} 天）`]].map(([v,l])=>
        `<option value="${v}" ${String(timeN)===v?'selected':''}>${l}</option>`).join('')}</select>`;
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
      return { sessions: sel, dayset: ds,
        label: sessN ? `最近 ${sessN} 场会话，落在 ${ds.size} 天里` : `全部会话，落在 ${ds.size} 天里` };
    }
    let f = from, t = to;
    if (mode === 'time') { t = last; f = timeN ? days[Math.max(0, days.length - timeN)].d : first; }
    return { sessions: D.sessions({ kind: metric === 'all' ? 'all' : 'human', from: f, to: t }),
      dayset: new Set(days.filter(d => d.d >= f && d.d <= t).map(d => d.d)),
      label: `${f} → ${t}` };
  };

  const valueOf = d => {
    const row = byDay.get(d), tk = tokDay.get(d);
    if (!row) return 0;
    return metric === 'human' ? row.human : metric === 'all' ? row.n : metric === 'turns' ? row.turns
      : metric === 'input' ? (tk ? tk.input_total : 0)
      : (tk && tk.hit_rate != null ? tk.hit_rate * 100 : 0);
  };

  const draw = () => {
    const { sessions, dayset, label } = resolve();
    const agg = D.aggregate(sessions);
    host.querySelector('#sum').innerHTML = bento([
      { k: '当前切片', v: `${esc(label)}`, size: 'sm', n: `${dayset.size} 天`, w: 3, tone: 'acc' },
      { k: '会话', v: String(agg.n), n: `你说话 ${agg.turns} 次 · 工具 ${agg.tools} 次`, w: 3, alt: true },
      { k: 'token 输入(含缓存)', v: fmt(agg.input_total), n: `命中率 ${rate(agg.hit)}` },
      { k: '未分类', v: String(agg.unclassified), n: '一个关键词都没命中' },
      { k: '涉及项目', v: String(agg.projects.length), n: agg.projects.slice(0, 2).map(p => p[0]).join('、') || '—' },
    ]);

    const vals = days.map(d => valueOf(d.d)).filter(v => v > 0).sort((a, b) => a - b);
    const q = p => vals.length ? vals[Math.min(vals.length - 1, Math.floor(vals.length * p))] : 1;
    const t1 = q(.25), t2 = q(.5), t3 = q(.8);
    const lv = v => v <= 0 ? 0 : v <= t1 ? 1 : v <= t2 ? 2 : v <= t3 ? 3 : 4;
    const months = new Map();
    for (let t = new Date(first + 'T00:00:00Z'); t <= new Date(last + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + 1)) {
      const iso = t.toISOString().slice(0, 10), k = iso.slice(0, 7);
      if (!months.has(k)) months.set(k, []);
      months.get(k).push(iso);
    }
    const pad = l => '<i data-pad="1"></i>'.repeat((new Date(l[0] + 'T00:00:00Z').getUTCDay() + 6) % 7);
    host.querySelector('#cal').innerHTML = `<div class="calwrap">${[...months].map(([mm, l]) =>
      `<div class="calmon"><span>${mm.slice(2).replace('-', '/')}</span><div class="calgrid">${pad(l)}${
        l.map(iso => {
          const v = valueOf(iso);
          const shown = metric === 'input' ? fmt(v) : metric === 'hit' ? v.toFixed(1) + '%' : String(v);
          return `<i data-day="${iso}" data-lv="${lv(v)}" ${dayset.has(iso) ? '' : 'data-out="1"'} title="${iso}　${shown}" aria-label="${iso} ${shown}" role="button" tabindex="0"></i>`;
        }).join('')}</div></div>`).join('')}</div>
      <p class="hint" style="margin:14px 0 0">分界 ${[t1, t2, t3].map(v => metric === 'input' ? fmt(v) : v.toFixed(metric === 'hit' ? 1 : 0)).join(' / ')}
      （按你自己的分布取四分位）。淡掉的格子＝不在当前切片内，不是没有数据。</p>`;

    host.querySelector('#rest').innerHTML = `
${sec('这段时间的主题')}
${orbit(agg.topics.map(([t, n]) => ({ k: t, v: n, c: 'var(--acc)', attr: `data-topic="${esc(t)}"` })))}
${drawer('展开逐日明细', table(
  [{ t: '日期' }, { t: '你开口', r: true }, { t: '机器', r: true }, { t: '钟点', r: true },
   { t: 'token 输入', r: true }, { t: '命中率', r: true }, { t: '主题' }],
  days.filter(d => dayset.has(d.d)).slice(-60).reverse().map(d => {
    const tk = tokDay.get(d.d);
    return [`<span class="lnk" data-day="${d.d}">${d.d}</span>`, String(d.human),
      String(d.n - d.human), String(d.active_hours), tk ? fmt(tk.input_total) : '—',
      tk ? rate(tk.hit_rate) : '—',
      Object.entries(d.topics).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([t, n]) => pill(`${t} ${n}`)).join('')];
  })))}`;
    enter('.card, .orow', host);
  };

  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-mode]');
    if (!b) return;
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
    .calwrap{display:flex;gap:5px;overflow-x:auto;padding:4px 0}
    .calmon{display:flex;flex-direction:column;gap:6px}
    .calmon>span{font-size:11px;color:var(--dim2);height:13px}
    .calgrid{display:grid;grid-auto-flow:column;grid-template-rows:repeat(7,13px);gap:4px}
    .calgrid i{width:13px;height:13px;border-radius:4px;background:var(--track);cursor:pointer;
      transition:transform .25s cubic-bezier(.22,1,.36,1)}
    .calgrid i[data-pad]{visibility:hidden}
    .calgrid i:hover{transform:scale(1.42)}
    .calgrid i[data-out]{opacity:.2}
    .calgrid i[data-lv="1"]{background:color-mix(in srgb,var(--acc) 26%,var(--track))}
    .calgrid i[data-lv="2"]{background:color-mix(in srgb,var(--acc) 50%,var(--track))}
    .calgrid i[data-lv="3"]{background:color-mix(in srgb,var(--acc) 74%,var(--track))}
    .calgrid i[data-lv="4"]{background:var(--acc);box-shadow:0 0 12px -2px var(--acc)}`;
  host.appendChild(st);
  drawCtl(); draw();
  enter('.sec, .card', host);
}
