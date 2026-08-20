import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

export async function render(host) {
  const ws = D.weeks();
  const peak = ws.reduce((a, b) => (b.human > (a?.human ?? -1) ? b : a), null);
  host.innerHTML =
    leaf({
      title: '一周一周看过去',
      lead: '按 ISO 周聚合。比日历更适合看趋势 —— 单日的高低多半是噪声。',
      body: plate({ k: '最重的一周', v: peak ? esc(peak.w) : '—', big: true,
        n: peak ? `${peak.human} 次开口 · ${peak.active_hours || 0} 个活跃小时` : '' })
        + carve(ws.slice().reverse().map(w => ({
            k: w.w, v: w.human, label: `${w.human} 次　${w.turns} 轮`,
          }))),
    })
    + leaf({
      title: '按周明细', lead: '', cols: false,
      body: rub([{ t: '周' }, { t: '你开口', r: true }, { t: '机器', r: true },
                 { t: '轮次', r: true }, { t: '活跃小时', r: true }],
        ws.slice().reverse().map(w => [esc(w.w), String(w.human), String(w.auto),
          String(w.turns), String(w.active_hours || 0)])),
    });
}
