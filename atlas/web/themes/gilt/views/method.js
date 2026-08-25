import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

export async function render(host) {
  const m = D.meta(), T = D.tokens();
  const A = D.A().aei || {}, DC = A.decidable || {}, P = A.populations || {};
  const R = ((A.primitives || {}).complexity || {}).removed;
  const worst = (DC.dims || []).slice().sort((a, b) => a.rate - b.rate)[0];

  host.innerHTML =
    leaf({
      title: '每个数字是怎么来的',
      lead: `看不懂的地方是我没写清楚，不是你的问题。状态只有四个词：
             <b>通 / 断了 / 没做 / 说不准</b>。算不出来的写「说不准」，不写「没问题」。
             颜色只是辅助，每个状态都带字。`,
      body: (worst ? plate({ k: '最不可判定的那个维度', v: `${(worst.rate * 100).toFixed(1)}%`, big: true,
          n: `${esc(worst.dim)} —— ${worst.decided} / ${worst.total} 判得出来` }) : '')
        + plates((DC.dims || []).map(d => ({
            k: d.dim, v: `${(d.rate * 100).toFixed(1)}%`, n: `${d.decided} / ${d.total}` })))
        + (DC.note ? marginal(esc(DC.note)) : ''),
    })
    + (P.counts ? leaf({
      title: '三个总体', lead: esc(P.why_split || ''),
      body: plates(Object.entries(P.counts).map(([k, v]) => ({
          k: P.labels[k], v: String(v), n: `${(P.share[k] * 100).toFixed(1)}%` })))
        + marginal(`<b>三条判据缺一不可。</b>${esc(P.note)}<br>各自抓到：${
            Object.entries(P.caught_by).map(([k, v]) => `${esc(k)} ${v} 场`).join('　')}`),
    }) : '')
    + leaf({
      title: 'v0.6.0 删掉的指标',
      lead: '删掉一个会骗人的数，比加十个新数有用。删了什么、为什么，写在这里。',
      body: (R ? warn(`<b>已删：${esc(R.what)}</b>（${esc(R.when)}）<br>${esc(R.why)}`) : '')
        + warn(`<b>本版没有「省了多少时间 / 提高了多少生产力」这类说法，这是刻意的。</b>
          要说这句话至少得有一个感知类指标；而本仓有「零 Agent 零 Token」铁律，
          感知数据没法从日志派生。要么加一个每天 10 秒的自评，要么不说 —— 现在选的是不说。`)
        + marginal(`<b>仍然不报美元。</b>单价会变，历史必须用<b>当时</b>的价重算；
          拿今天的价去乘历史用量，会把一次调价读成一次用量变化。
          所以只给 BIE，美元留给真实账单那一栏。`),
    })
    + leaf({
      title: '来源与口径', lead: '', cols: false,
      body: h2('数据从哪来')
        + carve(Object.entries(m.sources).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ k, v })))
        + h2('查过但没有对话内容的')
        + rub([{ t: '名字' }, { t: '位置' }, { t: '体积', r: true }, { t: '为什么不入库' }],
            Object.entries(m.skipped_sources).map(([k, v]) => [esc(k), esc(v.path),
              v.size_mb ? v.size_mb + ' MB' : '—', esc(v.why)]))
        + h2('全部口径')
        + rub([{ t: '项' }, { t: '口径' }],
            Object.entries(m.method).map(([k, v]) => [`<b>${esc(k)}</b>`, esc(v)])
              .concat([['<b>token</b>', esc(T.metric)], ['<b>时区</b>', esc(T.timezone)]])),
    });
}
