import { S, esc, fmt, go, topicColor } from '../app.js';

export async function render(host) {
  const a = S.atlas, m = a.meta, all = a.slices['0'], d7 = a.slices['7'], d30 = a.slices['30'];
  const L = all.ladder, build = L['建设'] || 0, ship = L['交付'] || 0, money = L['换钱'] || 0;

  const cards = [
    { k: '你亲自开口的会话', v: m.sessions_human, n: `另有 ${m.sessions_total - m.sessions_human} 场是机器`, c: 'hi' },
    { k: '有记录的日子', v: m.days_active, n: `${m.first_day} 起` },
    { k: '最近 7 天', v: d7.human, n: `活跃 ${d7.days_active} 天` },
    { k: '最近 30 天', v: d30.human, n: `活跃 ${d30.days_active} 天` },
    { k: '建设 : 交付 : 换钱', v: `${Math.floor(build / Math.max(1, money))}:${Math.floor(ship / Math.max(1, money))}:1`, n: `${build} / ${ship} / ${money}`, c: 'warn' },
  ];

  host.innerHTML = `
    <h2>你的三个月，一页看完</h2>
    <p class="sub">全部数字都从本机会话记录直接数出来，没有任何模型参与。</p>
    <div class="cards">${cards.map(c => `
      <div class="card ${c.c || ''}"><div class="k">${esc(c.k)}</div>
        <div class="v">${esc(c.v)}</div><div class="n">${esc(c.n)}</div></div>`).join('')}
    </div>

    <div class="note"><b>为什么「会话总数」和「你开口的」差这么多？</b><br>
      ${m.sessions_total} 场里有 ${m.sessions_auto} 场不是你在对话：
      ${m.sessions_fanout} 场是 agent 在同一小时里密集扇出（最大一次
      ${esc((m.fanout_hours[0] || {}).when || '—')}），
      其余是批处理和单轮机器指令。<b>本页所有口径都已经把它们剔掉了</b>，
      剔掉多少就写在这里，不藏进分母。</div>

    <h2>时间去哪了</h2>
    <p class="sub">按主题算，只统计你亲自开口的会话。一场会话最多挂 3 个主题。</p>
    <div class="panel"><table><thead><tr>
      <th>主题</th><th class="num">会话</th><th style="width:46%"></th></tr></thead><tbody>
      ${topicRows(all.topics, all.unclassified)}
    </tbody></table></div>

    <h2>差距在哪</h2>
    <div class="panel">${ladderRows(L, a.ladder)}</div>

    <h2>数出来的几件事</h2>
    ${a.insights.map(i => `
      <div class="panel"><div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap">
        <span class="state" data-s="${i.t === 'warn' ? '不确定' : '通'}">${i.t === 'warn' ? '值得看' : '事实'}</span>
        <b>${esc(i.k)}</b><span style="font-size:20px;font-weight:680">${esc(i.v)}</span></div>
        <div class="muted" style="margin-top:5px;font-size:13px">${esc(i.d)}</div></div>`).join('')}

    <h2>去看细节</h2>
    <div class="flexbar">
      <button class="act" data-go="calendar">按日历翻</button>
      <button class="act" data-go="day">看某一天</button>
      <button class="act" data-go="universe">看成一片星空</button>
      <button class="act" data-go="analysis">看趋势</button>
    </div>`;

  host.addEventListener('click', e => {
    const b = e.target.closest('[data-go]');
    if (b) go(b.dataset.go);
    const d = e.target.closest('[data-day]');
    if (d) go('day', d.dataset.day);
  });
}

function topicRows(topics, unclassified) {
  const rows = Object.entries(topics).sort((x, y) => y[1] - x[1]);
  const max = Math.max(1, ...rows.map(r => r[1]), unclassified);
  const line = (name, n, color) => `<tr>
    <td><span class="chip" style="border-color:${color}">${esc(name)}</span></td>
    <td class="num">${n}</td>
    <td><span class="bar" style="width:${(n / max * 100).toFixed(1)}%;background:${color}"></span></td></tr>`;
  return rows.map(([t, n]) => line(t, n, topicColor(t))).join('')
    + line('未分类（一个关键词都没命中）', unclassified, '#3a444f');
}

function ladderRows(L, def) {
  const total = Object.values(L).reduce((a, b) => a + b, 0) || 1;
  const order = ['建设', '交付', '换钱', '学习'];
  const desc = {
    '建设': '修 bug、重构、测试、治理、文档、界面 —— 把东西造出来',
    '交付': '部署上线、办公文书、业务方案 —— 把东西交出去',
    '换钱': '定价、订单、收入、求职 —— 把东西换成钱',
    '学习': '弄懂原理',
  };
  return `<table><tbody>${order.filter(k => k in L).map(k => `
    <tr><td style="width:74px"><b>${k}</b></td>
      <td class="num" style="width:58px">${L[k]}</td>
      <td style="width:56px" class="num muted">${(L[k] / total * 100).toFixed(0)}%</td>
      <td><span class="bar" style="width:${(L[k] / total * 100).toFixed(1)}%;background:${k === '换钱' ? '#4ade80' : k === '交付' ? '#5aa9ff' : '#4a5563'}"></span>
        <div class="muted" style="font-size:12px;margin-top:3px">${desc[k]}</div></td></tr>`).join('')}
  </tbody></table>
  <div class="muted" style="font-size:12.5px;margin-top:9px">
    这三档是把上面的主题归并出来的，不是另外算的。归并方式写在「口径」页。</div>`;
}
