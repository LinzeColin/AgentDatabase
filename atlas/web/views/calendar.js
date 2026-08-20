import { S, esc, go } from '../app.js';

export async function render(host) {
  const a = S.atlas;
  const byDay = new Map(a.days.map(d => [d.d, d]));
  const first = new Date(a.meta.first_day + 'T00:00:00Z');
  const last = new Date(a.meta.last_day + 'T00:00:00Z');
  const vals = a.days.map(d => d.human).filter(n => n > 0).sort((x, y) => x - y);
  const q = p => vals.length ? vals[Math.min(vals.length - 1, Math.floor(vals.length * p))] : 1;
  const t1 = q(.25), t2 = q(.5), t3 = q(.8);
  const level = n => n <= 0 ? 0 : n <= t1 ? 1 : n <= t2 ? 2 : n <= t3 ? 3 : 4;

  const months = new Map();
  for (let t = new Date(first); t <= last; t.setUTCDate(t.getUTCDate() + 1)) {
    const iso = t.toISOString().slice(0, 10);
    const key = iso.slice(0, 7);
    if (!months.has(key)) months.set(key, []);
    months.get(key).push(iso);
  }

  const cells = list => list.map(iso => {
    const d = byDay.get(iso);
    const h = d ? d.human : 0;
    const tip = d
      ? `${iso}　你开口 ${d.human} 场，机器 ${d.n - d.human} 场，${d.active_hours} 个钟点里有动静`
      : `${iso}　没有记录`;
    return `<div class="cell" data-lv="${level(h)}" data-day="${iso}" title="${esc(tip)}"></div>`;
  }).join('');

  // 每月第一天要落在正确的星期行上，否则整张图错位
  const pad = list => {
    const wd = (new Date(list[0] + 'T00:00:00Z').getUTCDay() + 6) % 7; // 周一 = 0
    return '<div class="cell" style="visibility:hidden"></div>'.repeat(wd);
  };

  host.innerHTML = `
    <h2>日历</h2>
    <p class="sub">每个格子是一天，颜色深浅＝<b>你亲自开口的会话数</b>（机器扇出不计）。点任一格进那一天。</p>
    <div class="panel calwrap"><div class="cal">
      ${[...months].map(([m, list]) => `
        <div class="calmon"><div class="lab">${m.slice(2).replace('-', '/')}</div>
          <div class="calgrid">${pad(list)}${cells(list)}</div></div>`).join('')}
    </div>
    <div class="callegend">少
      ${[0, 1, 2, 3, 4].map(l => `<span class="cell" data-lv="${l}" style="cursor:default"></span>`).join('')}
      多　<span class="muted">分界：${t1} / ${t2} / ${t3} 场（按你自己的分布取四分位，不是拍脑袋定的）</span>
    </div></div>

    <h2>最近 30 天</h2>
    <div class="panel"><table><thead><tr><th>日期</th><th class="num">你开口</th>
      <th class="num">机器</th><th class="num">钟点</th><th>那天在做什么</th></tr></thead><tbody>
      ${a.days.slice(-30).reverse().map(d => `<tr>
        <td><button class="rowbtn" data-day="${d.d}">${d.d}</button></td>
        <td class="num">${d.human}</td>
        <td class="num muted">${d.n - d.human}</td>
        <td class="num muted">${d.active_hours}</td>
        <td>${Object.entries(d.topics).sort((x, y) => y[1] - x[1]).slice(0, 4)
          .map(([t, n]) => `<span class="chip">${esc(t)} ${n}</span>`).join('') || '<span class="muted">未分类</span>'}</td>
      </tr>`).join('')}
    </tbody></table></div>`;

  host.addEventListener('click', e => {
    const c = e.target.closest('[data-day]');
    if (c) go('day', c.dataset.day);
  });
}
