import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, kv, table, meter, spark, warn, rate } from '../kit.js';

// Owner 明确要求：全量 + 自己能选的时间切片 **和** 会话切片。两种切法都在这一屏。
export async function render(host) {
  const days = D.days(), byDay = new Map(days.map(d => [d.d, d]));
  const tokDay = new Map(D.tokens().by_day.map(r => [r.d, r]));
  const first = days[0].d, last = days[days.length - 1].d;

  let mode = 'time';      // time = 按天数切  |  session = 按会话数切  |  range = 自定义区间
  let timeN = 0;          // 0 = 全历史
  let sessN = 200;
  let from = first, to = last;
  let metric = 'human';   // human | all | input | hit | turns

  host.innerHTML = `
${sec('CALENDAR', '每格一天。切片方式、口径、区间都可以自己选 —— 默认是全历史。')}
<div class="ctl">
  <button data-mode="time" aria-pressed="true">时间切片</button>
  <button data-mode="session" aria-pressed="false">会话切片</button>
  <button data-mode="range" aria-pressed="false">自定义区间</button>
  <span id="ctlslot"></span>
  <span style="flex:1"></span>
  <label>口径
    <select id="metric">
      <option value="human">你开口的会话</option>
      <option value="all">全部会话（含机器）</option>
      <option value="turns">你说话次数</option>
      <option value="input">token 输入(含缓存)</option>
      <option value="hit">缓存命中率</option>
    </select></label>
</div>
<div id="sum"></div>
<div id="cal" style="overflow-x:auto"></div>
<div id="tbl"></div>`;

  const ctlslot = host.querySelector('#ctlslot');
  const drawCtl = () => {
    if (mode === 'time') {
      ctlslot.innerHTML = `<select id="tn">${
        [['3', '最近 3 天'], ['7', '最近 7 天'], ['15', '最近 15 天'], ['30', '最近 30 天'],
         ['45', '最近 45 天'], ['60', '最近 60 天'], ['90', '最近 90 天'], ['180', '最近 180 天'],
         ['0', `全历史（${days.length} 天）`]].map(([v, l]) =>
          `<option value="${v}" ${String(timeN) === v ? 'selected' : ''}>${l}</option>`).join('')}</select>`;
      ctlslot.querySelector('#tn').addEventListener('change', e => { timeN = +e.target.value; draw(); });
    } else if (mode === 'session') {
      ctlslot.innerHTML = `<select id="sn">${
        [50, 100, 200, 400, 800, 0].map(v =>
          `<option value="${v}" ${sessN === v ? 'selected' : ''}>${v ? `最近 ${v} 场` : '全部会话'}</option>`).join('')}</select>`;
      ctlslot.querySelector('#sn').addEventListener('change', e => { sessN = +e.target.value; draw(); });
    } else {
      ctlslot.innerHTML = `<input type="date" id="f" value="${from}" min="${first}" max="${last}">
        →<input type="date" id="t" value="${to}" min="${first}" max="${last}">`;
      ctlslot.querySelector('#f').addEventListener('change', e => { from = e.target.value; draw(); });
      ctlslot.querySelector('#t').addEventListener('change', e => { to = e.target.value; draw(); });
    }
  };

  /** 三种切法都归一成「哪些天 + 哪些会话」，后面的画法就只有一套。 */
  const resolve = () => {
    if (mode === 'session') {
      const sel = D.lastNSessions(sessN || 1e9, metric === 'all' ? 'all' : 'human');
      const dset = new Set(sel.map(s => s.d));
      return { sessions: sel, dayset: dset,
        label: sessN ? `最近 ${sessN} 场会话，落在 ${dset.size} 天里` : `全部会话，落在 ${dset.size} 天里` };
    }
    let f = from, t = to;
    if (mode === 'time') {
      t = last;
      f = timeN ? days[Math.max(0, days.length - timeN)].d : first;
    }
    const sel = D.sessions({ kind: metric === 'all' ? 'all' : 'human', from: f, to: t });
    const dset = new Set(days.filter(d => d.d >= f && d.d <= t).map(d => d.d));
    return { sessions: sel, dayset: dset, label: `${f} → ${t}，${dset.size} 天` };
  };

  const valueOf = (d) => {
    const row = byDay.get(d), tk = tokDay.get(d);
    if (!row) return 0;
    if (metric === 'human') return row.human;
    if (metric === 'all') return row.n;
    if (metric === 'turns') return row.turns;
    if (metric === 'input') return tk ? tk.input_total : 0;
    if (metric === 'hit') return tk && tk.hit_rate != null ? tk.hit_rate * 100 : 0;
    return 0;
  };

  const draw = () => {
    const { sessions, dayset, label } = resolve();
    const agg = D.aggregate(sessions);

    host.querySelector('#sum').innerHTML = kv([
      ['当前切片', label, 'acc'],
      ['会话', String(agg.n), ''],
      ['你说话次数', String(agg.turns), ''],
      ['工具调用', String(agg.tools), ''],
      ['token 输入(含缓存)', fmt(agg.input_total), ''],
      ['缓存命中率', rate(agg.hit), 'acc'],
      ['未分类', String(agg.unclassified), agg.unclassified ? 'warn' : ''],
      ['涉及项目', String(agg.projects.length), ''],
    ]);

    // 全历史热力：不因为切片而少画格子，切片只改变高亮范围
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
    const cell = iso => {
      const v = valueOf(iso), inSlice = dayset.has(iso);
      const unit = metric === 'hit' ? '%' : metric === 'input' ? '' : ' 场';
      const shown = metric === 'input' ? fmt(v) : metric === 'hit' ? v.toFixed(1) : String(v);
      return `<i data-day="${iso}" data-lv="${lv(v)}" ${inSlice ? '' : 'data-out="1"'}
        title="${iso}　${shown}${unit}"></i>`;
    };
    const pad = list => '<i data-pad="1"></i>'.repeat((new Date(list[0] + 'T00:00:00Z').getUTCDay() + 6) % 7);

    host.querySelector('#cal').innerHTML = `<div class="calwrap">${
      [...months].map(([mm, list]) => `<div class="calmon"><span>${mm.slice(2).replace('-', '/')}</span>
        <div class="calgrid">${pad(list)}${list.map(cell).join('')}</div></div>`).join('')}</div>
      <p class="hint">分界 ${metric === 'input' ? [t1, t2, t3].map(fmt).join(' / ') : [t1, t2, t3].map(v => v.toFixed(metric === 'hit' ? 1 : 0)).join(' / ')}
      　（按你自己的分布取四分位，不是拍脑袋定的）。灰掉的格子＝不在当前切片内，不是没有数据。</p>`;

    const rows = days.filter(d => dayset.has(d.d)).slice(-60).reverse();
    host.querySelector('#tbl').innerHTML = table(
      [{ t: '日期' }, { t: '你开口', r: true }, { t: '机器', r: true }, { t: '钟点', r: true },
       { t: 'token 输入', r: true }, { t: '命中率', r: true }, { t: '那天在做什么' }],
      rows.map(d => {
        const tk = tokDay.get(d.d);
        return [`<span class="lnk" data-day="${d.d}">${d.d}</span>`,
          String(d.human), String(d.n - d.human), String(d.active_hours),
          tk ? fmt(tk.input_total) : '—', tk ? rate(tk.hit_rate) : '—',
          Object.entries(d.topics).sort((a, b) => b[1] - a[1]).slice(0, 4)
            .map(([t, n]) => `<span class="tag">${esc(t)} ${n}</span>`).join('') || '<span class="tag">未分类</span>'];
      }));
    enter('tbody tr', host);
  };

  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-mode]');
    if (!b) return;
    mode = b.dataset.mode;
    host.querySelectorAll('[data-mode]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.mode === mode)));
    drawCtl(); draw();
  });
  host.querySelector('#metric').addEventListener('change', e => { metric = e.target.value; draw(); });
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]');
    if (d) go('day', d.dataset.day);
  });

  const st = document.createElement('style');
  st.textContent = `
    .calwrap{display:flex;gap:4px;min-width:min-content;padding:8px 0}
    .calmon{display:flex;flex-direction:column;gap:4px}
    .calmon>span{font-size:10px;color:var(--dim2);height:12px}
    .calgrid{display:grid;grid-auto-flow:column;grid-template-rows:repeat(7,11px);gap:3px}
    .calgrid i{width:11px;height:11px;cursor:pointer;background:var(--hair2);border:1px solid transparent}
    .calgrid i[data-pad]{visibility:hidden}
    .calgrid i:hover{border-color:var(--fg)}
    .calgrid i[data-out]{opacity:.22}
    .calgrid i[data-lv="1"]{background:color-mix(in srgb,var(--acc) 22%,var(--hair2))}
    .calgrid i[data-lv="2"]{background:color-mix(in srgb,var(--acc) 45%,var(--hair2))}
    .calgrid i[data-lv="3"]{background:color-mix(in srgb,var(--acc) 70%,var(--hair2))}
    .calgrid i[data-lv="4"]{background:var(--acc)}`;
  host.appendChild(st);

  drawCtl(); draw();
  enter('.sec, .kv > div', host);
}
