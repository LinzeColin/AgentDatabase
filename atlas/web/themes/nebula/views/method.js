import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 口径。**这一屏的头条是「可判定率」** —— 一个维度判不出来的比例，
// 比任何一个分类结果都更能说明这份数据能不能信。
export async function render(host) {
  const m = D.meta(), T = D.tokens();
  const A = D.A().aei || {}, DC = A.decidable || {}, P = A.populations || {};
  const R = ((A.primitives || {}).complexity || {}).removed;
  const worst = (DC.dims || []).slice().sort((a, b) => a.rate - b.rate)[0];

  hud([{ k: '来源', v: String(Object.keys(m.sources).length) }]);

  host.innerHTML = stage({
    eyebrow: '档案 · 口径',
    title: '每个数字是怎么来的',
    hint: `看不懂的地方是我没写清楚，不是你的问题。状态只有四个词：
           <b>通 / 断了 / 没做 / 说不准</b>。算不出来的写「说不准」，不写「没问题」。`,
    body: (worst ? headline('最不可判定的那个维度', `${(worst.rate * 100).toFixed(1)}%`,
      `${esc(worst.dim)} —— ${worst.decided} / ${worst.total} 判得出来`) : '')
      + reads((DC.dims || []).map(d => ({
          k: d.dim, v: `${(d.rate * 100).toFixed(1)}%`, n: `${d.decided} / ${d.total}`,
          tone: d.rate < 0.8 ? 'warn' : '',
        })))
      + (DC.note ? warn(esc(DC.note)) : '')
      + (P.counts ? `<p class="hint" style="margin-top:24px">三个总体 —— ${esc(P.why_split || '')}</p>`
        + beams(Object.entries(P.counts).map(([k, v]) => ({
            k: P.labels[k], v, label: `${v} 场　${(P.share[k] * 100).toFixed(1)}%`,
            c: k === 'H' ? 'var(--acc)' : 'var(--ink3)',
          })))
        + warn(`<b>三条判据缺一不可。</b>${esc(P.note)}<br>各自抓到：${
            Object.entries(P.caught_by).map(([k, v]) => `${esc(k)} ${v} 场`).join('　')}`) : '')
      + (R ? warn(`<b>v0.6.0 删掉了：${esc(R.what)}</b><br>${esc(R.why)}`) : '')
      + warn(`<b>本版没有「省了多少时间 / 提高了多少生产力」这类说法，这是刻意的。</b>
        要说这句话至少得有一个感知类指标；而本仓有「零 Agent 零 Token」铁律，感知数据没法从日志派生。
        要么加一个每天 10 秒的自评，要么不说 —— 现在选的是不说。`)
      + sheet('数据从哪来', beams(Object.entries(m.sources).sort((a, b) => b[1] - a[1])
          .map(([k, v]) => ({ k, v, c: 'var(--acc3)' }))))
      + sheet('查过但没有对话内容的', table([{ t: '名字' }, { t: '位置' }, { t: '体积', r: true }, { t: '为什么不入库' }],
          Object.entries(m.skipped_sources).map(([k, v]) => [esc(k), esc(v.path),
            v.size_mb ? v.size_mb + ' MB' : '—', esc(v.why)])))
      + sheet('全部口径', table([{ t: '项' }, { t: '口径' }],
          Object.entries(m.method).map(([k, v]) => [`<b>${esc(k)}</b>`, esc(v)])
            .concat([['<b>token</b>', esc(T.metric)], ['<b>时区</b>', esc(T.timezone)]]))),
  });
  enter('.headline, .read, .beam, .warnbox', host);
}
