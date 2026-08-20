import { esc, fmt, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { flyToDay } from '../shell.js';
import { hero, sec, grid, orbit, drawer, table, pill, rate } from '../kit.js';

// 星历带：不是月份方格，是一条连续的时间带。每一天是一颗星，越亮越忙。
// 悬停哪一天，背后那片真星云就飞到那一天 —— 这一屏和背景是同一套时间轴。
export async function render(host) {
  const days = D.days(), byDay = new Map(days.map(d => [d.d, d]));
  const tokDay = new Map(D.tokens().by_day.map(r => [r.d, r]));
  const first = days[0].d, last = days[days.length - 1].d;
  let mode = 'time', timeN = 0, sessN = 200, from = first, to = last, metric = 'human';

  host.innerHTML = `
${hero('星历', '每一天是一颗星', `从 ${esc(first)} 到 ${esc(last)}，一天不落地铺开。
  越亮＝那天动静越大。停在哪一天，背后的星图就飞到哪一天；点一下进那天的明细。`)}
<div class="ctl">
  <button data-mode="time" aria-pressed="true">按时间切</button>
  <button data-mode="session" aria-pressed="false">按会话数切</button>
  <button data-mode="range" aria-pressed="false">自己划区间</button>
  <span id="ctlslot"></span>
  <select id="metric">
    <option value="human">你开口的次数</option><option value="all">全部（含机器）</option>
    <option value="turns">你说话次数</option><option value="input">读进去的 token</option>
    <option value="hit">缓存命中率</option></select>
</div>
<div id="sum"></div>
<div id="band"></div>
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
        label: sessN ? `最近 ${sessN} 场，落在 ${ds.size} 天里` : `全部会话，落在 ${ds.size} 天里` };
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
  const show = v => metric === 'input' ? fmt(v) : metric === 'hit' ? v.toFixed(1) + '%' : String(v);

  const draw = () => {
    const { sessions, dayset, label } = resolve();
    const agg = D.aggregate(sessions);
    host.querySelector('#sum').innerHTML = grid([
      { k: '现在看的是', v: `<span style="font-size:21px">${esc(label)}</span>`,
        n: `${dayset.size} 天`, w: 3, tone: 'acc' },
      { k: '会话', v: String(agg.n), n: `你说话 ${agg.turns} 次 · 用工具 ${agg.tools} 次`, w: 3, alt: true },
      { k: '读进去的 token', v: fmt(agg.input_total), n: `其中命中缓存 ${rate(agg.hit)}` },
      { k: '没认出在做什么', v: String(agg.unclassified), n: '一个关键词都没对上' },
      { k: '碰过的项目', v: String(agg.projects.length), n: agg.projects.slice(0, 2).map(p => p[0]).join('、') || '—' },
    ]);

    // 亮度按你自己的四分位分，不用固定阈值 —— 否则忙的月份全是满格，闲的全是空。
    const vals = days.map(d => valueOf(d.d)).filter(v => v > 0).sort((a, b) => a - b);
    const q = p => vals.length ? vals[Math.min(vals.length - 1, Math.floor(vals.length * p))] : 1;
    const t1 = q(.25), t2 = q(.5), t3 = q(.8);
    const lv = v => v <= 0 ? 0 : v <= t1 ? 1 : v <= t2 ? 2 : v <= t3 ? 3 : 4;

    const allDays = [];
    for (let t = new Date(first + 'T00:00:00Z'); t <= new Date(last + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + 1))
      allDays.push(t.toISOString().slice(0, 10));
    let curMon = '';
    host.querySelector('#band').innerHTML = `<div class="slab" style="padding:26px 22px 20px">
      <div class="band">${allDays.map(iso => {
        const mm = iso.slice(0, 7), head = mm !== curMon;
        if (head) curMon = mm;
        const v = valueOf(iso);
        return `${head ? `<b class="bmon">${mm.slice(2).replace('-', '/')}</b>` : ''}
          <i data-day="${iso}" data-lv="${lv(v)}" ${dayset.has(iso) ? '' : 'data-out="1"'}
             title="${iso}　${show(v)}"></i>`;
      }).join('')}</div>
      <p class="hint" style="margin:16px 0 0">亮度分界 ${[t1, t2, t3].map(show).join(' / ')}
        （按你自己的分布取的四分位，不是固定值）。暗掉的＝不在当前切片里，不是那天没数据。</p></div>`;

    host.querySelector('#rest').innerHTML = `
${sec('这段时间在做什么')}
${orbit(agg.topics.map(([t, n]) => ({ k: t, v: n, attr: `data-topic="${esc(t)}"` })))}
${drawer('摊开逐日明细', table(
  [{ t: '日期' }, { t: '你开口', r: true }, { t: '机器', r: true }, { t: '有动静的钟点', r: true },
   { t: '读进 token', r: true }, { t: '命中率', r: true }, { t: '在做什么' }],
  days.filter(d => dayset.has(d.d)).slice(-60).reverse().map(d => {
    const tk = tokDay.get(d.d);
    return [`<span class="lnk" data-day="${d.d}">${d.d}</span>`, String(d.human),
      String(d.n - d.human), String(d.active_hours), tk ? fmt(tk.input_total) : '—',
      tk ? rate(tk.hit_rate) : '—',
      Object.entries(d.topics).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([t, n]) => pill(`${t} ${n}`)).join('')];
  })))}`;
    enter('.cell, .orow, .slab', host);
  };

  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-mode]');
    if (!b) return;
    mode = b.dataset.mode;
    host.querySelectorAll('[data-mode]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.mode === mode)));
    drawCtl(); draw();
  });
  host.querySelector('#metric').onchange = e => { metric = e.target.value; draw(); };
  host.addEventListener('mouseover', e => {
    const i = e.target.closest('[data-day]');
    if (i) flyToDay(i.dataset.day);
  });
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]'); if (d) return go('day', d.dataset.day);
    const t = e.target.closest('[data-topic]'); if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  drawCtl(); draw();
  enter('.hero, .sec, .cell', host);
}
