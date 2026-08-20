import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, lede, p, n, big, aside, note, figure, rank, spark, table, state, rate } from '../kit.js';

export async function render(host) {
  const m = D.meta(), all = D.slice(0), d7 = D.slice(7), d30 = D.slice(30);
  const L = all.ladder, tk = D.tokens().total;
  const money = Math.max(1, L['换钱'] || 0);
  const dayHuman = D.days().slice(-40).map(d => d.human);
  const wk = D.topicSeries();

  host.innerHTML = `
${sec('你的三个月')}
${lede(`从 ${n(m.first_day)} 到 ${n(m.last_day)}，这台机器一共留下 ${n(m.sessions_total)} 场会话记录。
  但其中只有 ${big(m.sessions_human)} 场是<b>你亲自开口</b>的 ——
  另外 ${n(m.sessions_auto)} 场是机器：${n(m.sessions_fanout)} 场 agent 密集扇出，其余是批处理与单轮指令。
  下面所有数字都已经把它们剔掉了。`)}

${aside(`<b>剔掉的必须单独报。</b>被丢掉的东西不参与任何总量校验，所以总量永远显得是对的。
  最大一次扇出：${esc((m.fanout_hours[0] || {}).when || '—')}。`)}

${p(`这 ${n(m.sessions_human)} 场落在 ${big(m.days_active)} 个不同的日子里。
  最近七天你开了 ${n(d7.human)} 场，最近三十天 ${n(d30.human)} 场。
  最近四十天的起伏是这样的：${spark(dayHuman)}`)}

${p(`模型这边一共读进 ${n(tk.input_total)} 个 token（含缓存命中），
  其中 ${n(tk.cached)} 个是缓存直接命中的 ——
  命中率 ${big(rate(tk.hit_rate))}。另有 ${n(D.tokens().no_usage)} 场会话根本没有用量记录，
  它们的命中率写「不确定」，不是零。`)}

${sec('时间去哪了', '只统计你亲自开口的会话；一场最多挂三个主题。')}
${figure(rank(Object.entries(all.topics).sort((a, b) => b[1] - a[1]).map(([t, v]) => ({
  k: t, v, label: `${v}　${pct(v / Object.values(all.topics).reduce((a, b) => a + b, 0))}`,
  attr: `data-topic="${esc(t)}"`,
})).concat([{ k: '未分类', v: all.unclassified, label: String(all.unclassified) }])),
  '按主题排的会话数。未分类＝一个关键词都没命中，如实留空，没有硬塞进任何一类。')}

${sec('差距在哪')}
${lede(`把上面的主题归并成三档：<b>建设</b> ${n(L['建设'] || 0)} 次，
  <b>交付</b> ${n(L['交付'] || 0)} 次，<b>换钱</b> ${n(L['换钱'] || 0)} 次。
  也就是说，你每谈一次钱，前面先做了 ${big(Math.floor((L['建设'] || 0) / money))} 次建设、
  ${big(Math.floor((L['交付'] || 0) / money))} 次交付。`)}
${aside('这三档是把主题归并出来的，不是另外算的。归并方式写在「口径」那一页。')}
${figure(table([{ t: '档' }, { t: '会话', r: true }, { t: '占比', r: true }, { t: '包含' }],
  ['建设', '交付', '换钱', '学习'].filter(k => k in L).map(k => [
    `<b>${k}</b>`, String(L[k]), pct(L[k] / Object.values(L).reduce((a, b) => a + b, 0)),
    `<span class="kw">${{ '建设': '修bug／重构／测试／治理／文档／界面', '交付': '部署上线／办公文书／业务方案',
      '换钱': '定价／订单／收入／求职', '学习': '弄懂原理' }[k]}</span>`])), '三档构成。')}

${sec('数出来的几件事', '全部从数据直接数出来，没有一句是生成的。')}
${D.insights().map(i => `
  ${p(`<b>${esc(i.k)}</b>　${big(i.v)}　${state(i.t === 'warn' ? '不确定' : '通')}<br>
    <span style="color:var(--dim)">${esc(i.d)}</span>`)}`).join('')}

${sec('方向与口子', esc((D.opportunities() || {}).caveat || ''))}
${((D.opportunities() || {}).items || []).map(o => `
  ${p(`<b>${esc(o.k)}</b>　${big(o.v)}<br><span style="color:var(--dim)">${esc(o.d)}</span>`)}
  ${aside(`数据来源：${esc(o.from)}`)}
  ${figure(rank((o.list || []).map((x, i) => ({ k: x, v: (o.list.length - i) }))), esc(o.k))}`).join('')}
`;

  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  enter('.sec, p.body, figure, .aside', host);
}
