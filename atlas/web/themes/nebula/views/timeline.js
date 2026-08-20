import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 时间轴。按周聚合 —— 一条周线一束光。
export async function render(host) {
  const ws = D.weeks();
  const peak = ws.reduce((a, b) => (b.human > (a?.human ?? -1) ? b : a), null);
  hud([{ k: '周', v: String(ws.length) }, { k: '最重一周', v: peak ? String(peak.human) : '—' }]);

  host.innerHTML = stage({
    eyebrow: '时间 · 时间轴',
    title: '一周一周看过去',
    hint: '按 ISO 周聚合。<b>比日历更适合看趋势</b> —— 单日的高低多半是噪声。',
    body: headline('最重的一周', peak ? esc(peak.w) : '—',
      peak ? `${peak.human} 次开口 · ${peak.days_active ?? peak.active_hours ?? 0} 个活跃小时` : '')
      + beams(ws.slice().reverse().map(w => ({
          k: w.w, v: w.human, sub: `${w.auto} 场机器`,
          label: `${w.human} 次`, c: 'var(--acc2)',
        })))
      + sheet('按周明细', table(
          [{ t: '周' }, { t: '你开口', r: true }, { t: '机器', r: true }, { t: '轮次', r: true }, { t: '活跃小时', r: true }],
          ws.slice().reverse().map(w => [esc(w.w), String(w.human), String(w.auto),
            String(w.turns), String(w.active_hours || 0)]))),
  });
  enter('.headline, .beam', host);
}
