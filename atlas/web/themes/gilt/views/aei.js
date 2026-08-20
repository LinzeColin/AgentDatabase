import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

export async function render(host) {
  const A = D.A().aei || {};
  const P = A.populations || {}, Hd = A.headline || {};
  const modes = A.modes || {}, defs = A.mode_defs || {};
  const tot = Object.values(modes).reduce((a, b) => a + b, 0) || 1;

  host.innerHTML =
    leaf({
      title: '先分清谁在说话',
      lead: `AEI 从 v3 起就把不同来源分开报，因为混在一起的比值没有含义。
             这一页先给总体，下一页才是比例。`,
      body: (P.share ? plate({ k: '真的是一个人在说话的比例', v: pct(P.share.H), big: true,
        n: `${P.counts.H} 场人在对话 · ${P.counts.F} 场 agent 扇出 · ${P.counts.B} 场批处理` }) : '')
        + plates([
          { k: '自动化', v: pct(Hd.automation), n: '指派 + 反馈环' },
          { k: '增强', v: pct(Hd.augmentation), n: '迭代 + 学习 + 校验' },
          { k: '注意力集中度', v: String((A.concentration || {}).domain_hhi ?? '—'),
            n: '0 = 摊开，1 = 全压一件事。这不是 AEI 的 Gini' },
        ])
        + (P.note ? marginal(`<b>三条判据缺一不可。</b>${esc(P.note)}`) : ''),
    })
    + leaf({
      title: '协作五模式', lead: '判据是行为，不是主题。', cols: false,
      body: carve(Object.entries(modes).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({
          k: `${k} —— ${(defs[k] || {}).desc || ''}`, v, label: `${v} 场　${pct(v / tot)}`,
        })))
        + h2('按领域')
        + rub([{ t: '领域' }, { t: '会话', r: true }, { t: 'token', r: true }],
            (A.domains || []).map(d => [esc(d.name || d.domain), String(d.n), fmt(d.tokens || 0)]))
        + h2('没测的')
        + `<ul style="margin:0;padding-left:18px;font-size:12.5px;color:var(--ink2)">${
            (A.not_measured || []).map(x => `<li>${esc(typeof x === 'string' ? x : (x.what || '') + ' —— ' + (x.why || ''))}</li>`).join('')}</ul>`,
    });
}
