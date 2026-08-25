import { esc, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, bento, drawer, table, warn, pill, orbit } from '../kit.js';

export async function render(host) {
  const m = D.meta(), T = D.tokens();
  const A = D.A().aei || {};
  const R = ((A.primitives || {}).complexity || {}).removed;
  host.innerHTML = `
${sec('口径', '每个数字是怎么来的。看不懂的地方是我没写清楚，不是你的问题。')}
${warn(`状态只有四个词：<b>通 / 断了 / 没做 / 说不准</b>。算不出来的写「说不准」，不写「没问题」。
  <b>颜色只是辅助</b>，每个状态都带字 —— 实测颜色对比度 15/15 不足 3:1。`)}
${sec('数据从哪来')}
${orbit(Object.entries(m.sources).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ k, v, c: 'var(--acc)' })))}
${sec('查过但没有对话内容的', '这些占着磁盘但入不了库。列出来是为了下次不用再挖一遍。')}
${drawer('展开', table([{ t: '名字' }, { t: '位置' }, { t: '体积', r: true }, { t: '为什么不入库' }],
  Object.entries(m.skipped_sources).map(([k, v]) => [esc(k), esc(v.path), v.size_mb ? v.size_mb + ' MB' : '—', esc(v.why)])))}
${sec('被剔掉的那部分', '被丢掉的东西不参与任何总量校验，所以总量永远显得是对的。这里把丢掉的摆出来。')}
${drawer('重复投喂的提示词', table([{ t: '提示词' }, { t: '场次', r: true }],
  m.auto_batches.map(b => [esc(b.prompt), String(b.n)])))}
${drawer('机器一次性铺开的批量任务', table([{ t: '时段' }], (m.fanout_hours || []).map(f => [esc(f.when)])))}
${sec('可判定率', esc((A.decidable || {}).note || ''))}
${A.decidable ? table([{ t: '维度' }, { t: '判出来的', r: true }, { t: '总数', r: true }, { t: '可判定率', r: true }],
  A.decidable.dims.map(d => [esc(d.dim), String(d.decided), String(d.total),
    `<b>${(d.rate * 100).toFixed(1)}%</b>`])) : ''}

${sec('三个总体', esc((A.populations || {}).why_split || ''))}
${A.populations ? bento(Object.entries(A.populations.counts).map(([k, v]) => ({
  k: esc(A.populations.labels[k]), v: String(v),
  n: (A.populations.share[k] * 100).toFixed(1) + '%', w: 2,
  tone: k === 'H' ? 'acc' : '' }))) : ''}
${A.populations ? warn(`<b>三条判据缺一不可。</b>${esc(A.populations.note)}<br>
  各自抓到：${Object.entries(A.populations.caught_by).map(([k, v]) => `${esc(k)} ${v} 场`).join('　')}`) : ''}

${sec('v0.6.0 删掉的指标', '删掉一个会骗人的数，比加十个新数有用。删了什么、为什么，写在这里。')}
${R ? warn(`<b>已删：${esc(R.what)}</b>（${esc(R.when)}）<br>${esc(R.why)}`) : ''}
${warn(`<b>本版没有「省了多少时间 / 提高了多少生产力」这类说法，这是刻意的。</b>
  要说这句话，至少得有一个感知类指标；而本仓有「零 Agent 零 Token」铁律，
  感知数据没法从日志派生。所以要么加一个每天 10 秒的自评，要么不说 —— 现在选的是不说。`)}

${sec('算法')}
${drawer('展开全部口径', table([{ t: '项' }, { t: '口径' }],
  Object.entries(m.method).map(([k, v]) => [`<b>${esc(k)}</b>`, esc(v)])
    .concat([['<b>token</b>', esc(T.metric)], ['<b>时区</b>', esc(T.timezone)]])))}
${warn(`<b>仍然不报美元。</b>单价会变，历史必须用<b>当时</b>的价重算 ——
  拿今天的价去乘历史用量，会把一次调价读成一次用量变化。
  所以只给 <b>BIE</b>（价格加权 token，无量纲、跨时间可比），美元留给真实账单那一栏。`)}
${sec('主题归并')}
${drawer('展开', table([{ t: '档' }, { t: '包含主题' }],
  Object.entries(D.ladder()).map(([k, v]) => [`<b>${esc(k)}</b>`, v.map(t => pill(t)).join('')])))}
${sec('权重最高的关键词', '越少见的词权重越高。出现在半数以上会话里的词权重直接归零。')}
<p class="hint">${Object.entries(D.A().keyword_weights).slice(0, 44).map(([k, v]) => pill(k)).join('')}</p>`;
  enter('.sec, .card, .orow', host);
}
