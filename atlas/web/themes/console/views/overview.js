import { esc, fmt, pct, go, enter, countUp } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, kv, table, meter, spark, state, warn, rate } from '../kit.js';

export async function render(host) {
  const m = D.meta(), all = D.slice(0), d7 = D.slice(7), d30 = D.slice(30);
  const L = all.ladder, tk = D.tokens().total;
  const build = L['建设'] || 0, ship = L['交付'] || 0, money = L['换钱'] || 0;
  const dayHuman = D.days().slice(-40).map(d => d.human);

  host.innerHTML = `
${sec('SUMMARY')}
${kv([
  ['你开口的会话', `<span data-cnt="${m.sessions_human}">0</span>`, 'acc'],
  ['机器跑的', String(m.sessions_auto), ''],
  ['有记录的日子', `<span data-cnt="${m.days_active}">0</span>`, ''],
  ['起始', m.first_day, ''],
  ['最近 7 天', `${d7.human} 场 / ${d7.days_active} 天`, ''],
  ['最近 30 天', `${d30.human} 场 / ${d30.days_active} 天`, ''],
  ['建设:交付:换钱', `${Math.floor(build / Math.max(1, money))}:${Math.floor(ship / Math.max(1, money))}:1`, 'warn'],
  ['token 输入(含缓存)', fmt(tk.input_total), ''],
  ['缓存命中率', rate(tk.hit_rate), 'acc'],
  ['无用量会话', String(D.tokens().no_usage), ''],
])}
<p class="hint">最近 40 天你开口的会话数 ${spark(dayHuman)}</p>

${warn(`<b>${m.sessions_total} 场里有 ${m.sessions_auto} 场不是你在对话。</b>
  ${m.sessions_fanout} 场是 agent 同一小时内密集扇出（最大一次 ${esc((m.fanout_hours[0] || {}).when || '—')}），
  其余是批处理与单轮机器指令。本页全部口径已剔除它们 —— 剔掉多少写在这里，不藏进分母。`)}

${sec('TIME BY TOPIC', '只统计你亲自开口的会话；一场最多挂 3 个主题。')}
${(() => {
  const rows = Object.entries(all.topics).sort((a, b) => b[1] - a[1]);
  const mx = Math.max(1, ...rows.map(r => r[1]), all.unclassified);
  const wk = D.topicSeries();
  return table(
    [{ t: '主题' }, { t: '会话', r: true }, { t: '占比', r: true }, { t: '分布' }, { t: '周趋势' }],
    [...rows.map(([t, n]) => [
      `<span class="lnk" data-topic="${esc(t)}">${esc(t)}</span>`,
      String(n),
      pct(n / rows.reduce((a, b) => a + b[1], 0)),
      meter(n, mx, 110),
      spark(wk.weeks.map(w => w.count[t] || 0)),
    ]), ['<span class="tag">未分类</span>', String(all.unclassified), '—', meter(all.unclassified, mx, 110), '']]);
})()}

${sec('LADDER', '把上面的主题归并成三档。归并方式见「口径」。')}
${(() => {
  const tot = Object.values(L).reduce((a, b) => a + b, 0) || 1;
  const desc = { '建设': '修bug/重构/测试/治理/文档/界面', '交付': '部署上线/办公文书/业务方案',
                 '换钱': '定价/订单/收入/求职', '学习': '弄懂原理' };
  return table([{ t: '档' }, { t: '会话', r: true }, { t: '占比', r: true }, { t: '' }, { t: '包含' }],
    ['建设', '交付', '换钱', '学习'].filter(k => k in L).map(k =>
      [k, String(L[k]), pct(L[k] / tot), meter(L[k], Math.max(...Object.values(L)), 130),
       `<span class="tag">${esc(desc[k])}</span>`]));
})()}

${sec('FACTS', '全部从数据直接数出来，没有一句是生成的。')}
${table([{ t: '' , w: '13%' }, { t: '值', w: '15%' }, { t: '说明' }],
  D.insights().map(i => [
    `${state(i.t === 'warn' ? '不确定' : '通')} ${esc(i.k)}`,
    `<b>${esc(i.v)}</b>`, `<span class="tag">${esc(i.d)}</span>`]))}

${sec('OPPORTUNITY', esc((D.opportunities() || {}).caveat || ''))}
${((D.opportunities() || {}).items || []).map(o => `
  <p class="hint" style="margin:12px 0 4px"><b style="color:var(--fg)">${esc(o.k)}</b>
    　<span style="color:var(--acc)">${esc(o.v)}</span>　
    <span class="tag">来源：${esc(o.from)}</span></p>
  <p class="hint" style="margin:0 0 6px">${esc(o.d)}</p>
  ${table([{ t: '' }], (o.list || []).map(x => [`<span class="tag">${esc(x)}</span>`]))}`).join('')}
`;

  host.querySelectorAll('[data-cnt]').forEach(el => countUp(el, +el.dataset.cnt));
  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  enter('.sec, .kv > div, tbody tr', host);
}
