import { esc, fmt, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, kv, table, warn } from '../kit.js';

export async function render(host) {
  const m = D.meta(), T = D.tokens();
  host.innerHTML = `
${sec('STATUS WORDS')}
${warn(`只有四个词：<b>通 / 断了 / 没做 / 不确定</b>。算不出来的地方写「不确定」，不写「没问题」。
  <b>颜色只是辅助</b>，每个状态都带字 —— 实测颜色对比度 15/15 不足 3:1。`)}

${sec('SOURCES')}
${table([{ t: '来源' }, { t: '会话', r: true }], Object.entries(m.sources).sort((a, b) => b[1] - a[1])
  .map(([k, v]) => [esc(k), String(v)]))}

${sec('SKIPPED', '查过但没有对话内容的。列出来是为了下次不用再挖一遍。')}
${table([{ t: '名字' }, { t: '位置' }, { t: '体积', r: true }, { t: '为什么不入库' }],
  Object.entries(m.skipped_sources).map(([k, v]) =>
    [esc(k), `<span class="tag">${esc(v.path)}</span>`, v.size_mb ? v.size_mb + ' MB' : '—', `<span class="tag">${esc(v.why)}</span>`]))}

${sec('WHAT WAS EXCLUDED', '被丢掉的东西不参与任何总量校验，所以总量永远显得是对的。这里把丢掉的摆出来。')}
${table([{ t: '重复投喂的提示词' }, { t: '场次', r: true }],
  m.auto_batches.map(b => [`<span class="tag">${esc(b.prompt)}</span>`, String(b.n)]))}
${table([{ t: 'agent 密集扇出' }], (m.fanout_hours || []).map(f => [esc(f.when)]))}

${sec('ALGORITHM')}
${table([{ t: '项' }, { t: '口径' }], Object.entries(m.method)
  .map(([k, v]) => [`<b style="color:var(--fg)">${esc(k)}</b>`, `<span class="tag">${esc(v)}</span>`]))}
${kv([['token 口径', esc(T.metric), 'acc'], ['时区', esc(T.timezone), '']])}
${warn(`<b>费用不估算。</b>不同模型、不同缓存命中、不同套餐的单价都不一样，
  拿不到真实账单就标「不确定」，不拿一个编出来的数字给你看。`)}

${sec('LADDER MAPPING')}
${table([{ t: '档' }, { t: '包含主题' }], Object.entries(D.ladder())
  .map(([k, v]) => [`<b>${esc(k)}</b>`, v.map(t => `<span class="tag">${esc(t)}</span>`).join('')]))}

${sec('KEYWORD WEIGHTS', '越少见的词权重越高。出现在半数以上会话里的词权重直接归零 —— 否则「方案」「数据」这种到处都是的词会决定一切。')}
<p class="hint">${Object.entries(D.A().keyword_weights).slice(0, 44)
  .map(([k, v]) => `<span class="tag" title="权重 ${v}">${esc(k)}</span>`).join('')}</p>

${sec('COUPLING')}
<p class="hint">${esc(D.coupling().note)}</p>`;
  enter('.sec, tbody tr', host);
}
