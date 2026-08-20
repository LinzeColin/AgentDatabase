import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 经济指数。头条是「有多少场其实是一个人在说话」——
// 在这台机器上它只有两成，任何不先说清楚这件事的百分比都会骗人。
export async function render(host) {
  const A = D.A().aei || {};
  const P = A.populations || {}, H = A.headline || {};
  const modes = A.modes || {}, defs = A.mode_defs || {};
  const tot = Object.values(modes).reduce((a, b) => a + b, 0) || 1;

  hud([{ k: '真人会话', v: String(A.sessions_total || 0) }]);

  host.innerHTML = stage({
    eyebrow: '经济 · 经济指数',
    title: '先分清谁在说话',
    hint: `AEI 从 v3 起就把不同来源分开报，因为混在一起的比值没有含义。
           <b>这一屏先给总体，再给比例。</b>`,
    body: (P.share ? headline('真的是一个人在说话的比例', pct(P.share.H),
      `${P.counts.H} 场人在对话 · ${P.counts.F} 场 agent 扇出 · ${P.counts.B} 场批处理`) : '')
      + reads([
        { k: '自动化', v: pct(H.automation), n: '指派 + 反馈环' },
        { k: '增强', v: pct(H.augmentation), n: '迭代 + 学习 + 校验' },
        { k: '注意力集中度', v: String((A.concentration || {}).domain_hhi ?? '—'),
          n: '0 = 摊开，1 = 全压一件事' },
      ])
      + (P.note ? warn(`<b>三条判据缺一不可。</b>${esc(P.note)}`) : '')
      + `<p class="hint" style="margin-top:22px">协作五模式 —— 判据是行为，不是主题。</p>`
      + beams(Object.entries(modes).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({
          k, v, sub: (defs[k] || {}).desc || '',
          label: `${v} 场　${pct(v / tot)}`,
          c: (defs[k] || {}).group === '自动化' ? 'var(--acc)' : 'var(--acc2)',
        })))
      + sheet('按领域', table([{ t: '领域' }, { t: '会话', r: true }, { t: 'token', r: true }],
          (A.domains || []).map(d => [esc(d.name || d.domain), String(d.n), fmt(d.tokens || 0)])))
      + sheet('没测的', `<ul style="margin:0;padding-left:18px">${
          (A.not_measured || []).map(x => `<li>${esc(typeof x === 'string' ? x : (x.what || '') + ' —— ' + (x.why || ''))}</li>`).join('')}</ul>`),
  });
  enter('.headline, .read, .beam, .warnbox', host);
}
