import { esc, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, lede, p, n, big, aside, note, figure, rank, table, kw } from '../kit.js';

export async function render(host) {
  const m = D.meta(), T = D.tokens();
  host.innerHTML = `
${sec('口径')}
${lede(`每个数字是怎么来的，都写在这一页。看不懂的地方是我没写清楚，不是你的问题。`)}
${note(`给你看的状态只有四个词：<b>通 / 断了 / 没做 / 不确定</b>。
  算不出来的地方写「不确定」，不写「没问题」。<b>颜色只是辅助</b>，每个状态都带字 ——
  实测颜色对比度 15/15 不足 3:1。`)}

${sec('数据从哪来')}
${figure(rank(Object.entries(m.sources).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ k, v, label: String(v) }))),
  `共 ${m.sessions_total} 场，其中 ${m.sessions_human} 场是你亲自开口的。`)}

${sec('查过但没有对话内容的', '这些占着磁盘但入不了库。列出来是为了下次不用再挖一遍。')}
${figure(table([{ t: '名字' }, { t: '位置' }, { t: '体积', r: true }, { t: '为什么不入库' }],
  Object.entries(m.skipped_sources).map(([k, v]) => [esc(k), `<span class="kw">${esc(v.path)}</span>`,
    v.size_mb ? v.size_mb + ' MB' : '—', esc(v.why)])), '已排除的来源。')}

${sec('被剔掉的那部分')}
${p(`被丢掉的东西不参与任何总量校验，所以总量永远显得是对的。这里把丢掉的摆出来：
  批处理 ${n(m.sessions_auto - m.sessions_fanout)} 场，agent 密集扇出 ${n(m.sessions_fanout)} 场。`)}
${figure(table([{ t: '重复投喂的提示词' }, { t: '场次', r: true }],
  m.auto_batches.map(b => [esc(b.prompt), String(b.n)])), '重复投喂的批处理。')}
${figure(table([{ t: 'agent 密集扇出' }], (m.fanout_hours || []).map(f => [esc(f.when)])), '扇出时段。')}

${sec('算法')}
${figure(table([{ t: '项' }, { t: '口径' }], Object.entries(m.method).map(([k, v]) => [`<b>${esc(k)}</b>`, esc(v)])
  .concat([['<b>token</b>', esc(T.metric)], ['<b>时区</b>', esc(T.timezone)]])), '全部口径。')}
${note('<b>费用不估算。</b>不同模型、不同缓存命中、不同套餐的单价都不一样，拿不到真实账单就标「不确定」，不拿一个编出来的数字给你看。')}

${sec('主题归并')}
${figure(table([{ t: '档' }, { t: '包含主题' }], Object.entries(D.ladder())
  .map(([k, v]) => [`<b>${esc(k)}</b>`, v.map(t => kw(t)).join('')])), '三档是怎么归并的。')}

${sec('权重最高的关键词', '越少见的词权重越高。出现在半数以上会话里的词权重直接归零 —— 否则「方案」「数据」这种到处都是的词会决定一切。')}
${p(Object.entries(D.A().keyword_weights).slice(0, 46).map(([k]) => kw(k)).join(''))}

${sec('耦合')}
${p(esc(D.coupling().note))}`;
  enter('.sec, p.body, figure, .aside', host);
}
