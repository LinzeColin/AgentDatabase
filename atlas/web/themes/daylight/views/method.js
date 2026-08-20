import { esc, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { hero, sec, drawer, table, warn, pill, orbit } from '../kit.js';

export async function render(host) {
  const m = D.meta(), T = D.tokens();
  host.innerHTML = `
${hero('怎么算的', '每个数字的出处',
  `看不懂的地方是我没写清楚，不是你的问题。这一页存在的意义只有一个：你能自己核对任何一个数字。`)}
${warn(`状态只有四个词：<b>通 / 断了 / 没做 / 说不准</b>。
  算不出来的一律写「说不准」，不写「没问题」。<b>颜色只是辅助</b> ——
  每个状态都带字，因为实测 15 组配色对比度全部不到 3:1，光靠颜色看不出来。`)}

${sec('数据从哪来的')}
${orbit(Object.entries(m.sources).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ k, v })))}

${sec('查过但进不了库的', '这些占着磁盘却没有可读的对话内容。列出来是为了下次不用再挖一遍。')}
${drawer('摊开', table([{ t: '名字' }, { t: '在哪' }, { t: '体积', r: true }, { t: '为什么进不了库' }],
  Object.entries(m.skipped_sources).map(([k, v]) =>
    [esc(k), esc(v.path), v.size_mb ? v.size_mb + ' MB' : '—', esc(v.why)])))}

${sec('被剔掉的那一部分', '被丢掉的东西不参与任何总量校验，所以总量看起来永远是对的。这里把丢掉的摆出来。')}
${drawer('重复投喂的同一句提示词', table([{ t: '提示词' }, { t: '被投喂了几场', r: true }],
  m.auto_batches.map(b => [esc(b.prompt), String(b.n)])))}
${drawer('机器一口气铺开的批量任务', table([{ t: '发生在' }],
  (m.fanout_hours || []).map(f => [esc(f.when)])))}

${sec('算法口径')}
${drawer('摊开全部口径', table([{ t: '项' }, { t: '怎么算的' }],
  Object.entries(m.method).map(([k, v]) => [`<b>${esc(k)}</b>`, esc(v)])
    .concat([['<b>token</b>', esc(T.metric)], ['<b>时区</b>', esc(T.timezone)]])))}
${warn('<b>费用不估算。</b>不同模型、不同缓存命中、不同套餐单价都不一样，拿不到真实账单就标「说不准」，不给一个看起来很精确的假数。')}

${sec('主题是怎么归档的')}
${drawer('摊开', table([{ t: '档位' }, { t: '包含哪些主题' }],
  Object.entries(D.ladder()).map(([k, v]) => [`<b>${esc(k)}</b>`, v.map(t => pill(t)).join('')])))}

${sec('权重最高的关键词', '越少见的词权重越高。出现在半数以上会话里的词，权重直接归零 —— 否则「代码」这种词会盖过一切。')}
<p class="hint">${Object.keys(D.A().keyword_weights).slice(0, 44).map(k => pill(k)).join('')}</p>`;
  enter('.hero, .sec, .orow', host);
}
