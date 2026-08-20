import { esc, fmt, pct, go, enter, topicColor, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { sec, bento, orbit, drawer, table, warn, pill, state } from '../kit.js';

export async function render(host) {
  const E = D.A().aei, P = E.primitives, N = E.sessions_total;
  const modeOrder = ['指派', '反馈环', '迭代', '学习', '校验', '未归类'];
  const MODE_COL = { '指派': '#5ce6b4', '反馈环': '#2fae86', '迭代': '#7cc4ff', '学习': '#b58cff', '校验': '#63d2ff', '未归类': '#5a6480' };
  const css = k => cssVar(k);
  const bands = o => orbit((o.bands || Object.keys(o.counts)).filter(b => o.counts[b])
    .map(b => ({ k: b, v: o.counts[b], label: `${o.counts[b]}　${pct(o.counts[b] / N)}`, c: 'var(--acc)' })));

  host.innerHTML = `
${sec('经济指数', esc(E.framework))}
${bento([
  { k: '自动化份额', v: pct(E.headline.automation), n: '指派 + 反馈环', w: 3, tone: 'acc' },
  { k: '增强份额', v: pct(E.headline.augmentation), n: '迭代 + 学习 + 校验', w: 3, alt: true },
  { k: '平均 AI 自主度', v: `${P.autonomy.avg}/5`, n: '1 全程在场 · 5 完全委派' },
  { k: '中位加速', v: P.complexity.speedup_median ? P.complexity.speedup_median + '×' : '不确定', n: `能算的 ${P.complexity.speedup_n} 场` },
  { k: '领域集中度', v: E.concentration.domain_hhi ?? '不确定', n: 'HHI 0 摊开 · 1 全压一件事' },
])}
<canvas class="viz" id="donut" height="250"></canvas>
${drawer('五种模式的判据（AEI 原定义）', table([{ t: '模式' }, { t: 'EN' }, { t: '归属' }, { t: '判据' }],
  modeOrder.filter(m => E.modes[m]).map(m =>
    [`<b>${esc(m)}</b>`, esc(E.mode_defs[m].en), esc(E.mode_defs[m].group), esc(E.mode_defs[m].desc)])))}

${sec('五个经济原语', 'AEI 的骨架。每一项的口径都写在下面，做不到的在最后单独列。')}
<p class="hint">① 任务复杂度 —— ${esc(P.complexity.note)}</p>${bands(P.complexity)}
<p class="hint" style="margin-top:24px">② 技能层级 —— ${esc(P.skill.note)}</p>${bands(P.skill)}
<p class="hint" style="margin-top:24px">③ 用途</p>${bands({ counts: P.use_case.counts, bands: ['工作', '学习', '个人'] })}
<p class="hint" style="margin-top:24px">④ AI 自主度 —— ${esc(P.autonomy.note)}</p>
${orbit(Object.entries(P.autonomy.counts).map(([k, v]) =>
  ({ k: P.autonomy.labels[k] || k, v, label: `${v}　${pct(v / N)}`, c: 'var(--acc2)' })))}
<p class="hint" style="margin-top:24px">⑤ 任务成功 —— ${esc(P.success.note)}</p>${bands(P.success)}

${sec('领域：覆盖率与有效覆盖率', '有效覆盖率 = 覆盖率 × 成功率。AEI 用它区分「碰过」与「真的做成了」。')}
${orbit(E.domains.map(r => ({ k: r.domain, v: r.coverage,
  label: `覆盖 ${pct(r.coverage)}　有效 ${r.effective_coverage == null ? '—' : pct(r.effective_coverage)}　${r.n} 场`,
  c: 'var(--acc)' })))}
${drawer('展开领域明细', table(
  [{ t: '领域' }, { t: '会话', r: true }, { t: '覆盖率', r: true }, { t: '有效覆盖', r: true },
   { t: '成功率', r: true }, { t: '自动化', r: true }, { t: '自主度', r: true },
   { t: '新token/场', r: true }, { t: '缓存占比', r: true }],
  E.domains.map(r => [esc(r.domain), String(r.n), pct(r.coverage),
    r.effective_coverage == null ? state('不确定') : pct(r.effective_coverage),
    r.success_rate == null ? state('不确定') : pct(r.success_rate),
    r.automation == null ? '—' : pct(r.automation), r.autonomy_avg ?? '—',
    fmt(r.tokens_per_session), pct(r.cache_ratio)])))}
${E.domains_unclassified ? warn(`另有 <b>${E.domains_unclassified}</b> 场一个领域词都没命中，如实标未归类。`) : ''}

${sec('产物分类', esc(E.artifacts_note))}
${orbit(E.artifacts.map(a => ({ k: a.artifact, v: a.n, label: `${fmt(a.n)}　${pct(a.share)}`, c: 'var(--acc2)' })))}

${sec('上下文分布', esc(E.context.note))}
${orbit(E.context.rows.slice(0, 14).map(r => ({ k: r.context, v: r.n,
  label: `${r.n} 场　${fmt(r.tokens)} 新token`, c: 'var(--acc)' })))}

${sec('Cadence', esc(E.cadence.note))}
<canvas class="viz" id="cad" height="210"></canvas>

${sec('转换轨迹', esc(E.transition.note))}
${orbit(E.transition.drift.map(x => ({ k: x.domain, v: Math.abs(x.delta) * 1000,
  label: `${pct(x.early)} → ${pct(x.late)}　${x.delta >= 0 ? '↑' : '↓'}${(Math.abs(x.delta) * 100).toFixed(1)}`,
  c: x.delta >= 0 ? 'var(--ok)' : 'var(--bad)' })))}

${sec('ROI')}
${E.roi.state === '通' ? bento([
  { k: '每条提交平摊', v: fmt(E.roi.tokens_per_commit), n: '个新 token', w: 3, tone: 'warn' },
  { k: '新 token 合计', v: fmt(E.roi.tokens_total), n: `缓存另有 ${fmt(E.roi.cache_total)}`, w: 3, alt: true },
  { k: '每条提交要几场', v: String(E.roi.sessions_per_commit), n: '场会话' },
  { k: '只聊没交付', v: `${E.roi.days_talk_only} 天`, n: `重合率 ${pct(E.roi.overlap_rate)}` },
]) + warn(esc(E.roi.cost_basis) + '<br>' + esc(E.roi.note)) : warn(`<b>状态：不确定。</b>${esc(E.roi.why || '')}`)}

${sec('机会挖掘', '三条规则：高委派＝已定型可产品化；低成功＋高投入＝在流血；低自主度＝护城河或负债。')}
${E.opportunity.map(o => `<div class="card w6">
  <div class="ck">${esc(o.kind)}　${pill(o.domain)}　${o.n} 场</div>
  <div class="cn" style="margin-top:8px;font-size:13.5px">${esc(o.why)}</div></div>`).join('')}

${sec('做不到的', 'AEI 有而这里没有的，逐条列出来 —— 不含糊过去。')}
${drawer('展开', table([{ t: '项' }, { t: '为什么没有' }],
  E.not_measured.map(x => [`<b>${esc(x.item)}</b>`, esc(x.why)])))}`;

  const drawDonut = () => {
    const cv = host.querySelector('#donut'); if (!cv) return;
    const { ctx, w } = fitCanvas(cv, 250);
    const h = 250, cx = w / 2, cy = h / 2, R = Math.max(24, Math.min(92, h / 2 - 34));
    ctx.clearRect(0, 0, w, h);
    let a0 = -Math.PI / 2; ctx.lineWidth = 32;
    for (const m of modeOrder) {
      const v = E.modes[m] || 0; if (!v) continue;
      const a1 = a0 + (v / N) * 6.2832;
      ctx.strokeStyle = MODE_COL[m];
      ctx.beginPath(); ctx.arc(cx, cy, R, a0, a1); ctx.stroke();
      const mid = (a0 + a1) / 2;
      if (v / N > 0.05) { ctx.fillStyle = css('--fg'); ctx.textAlign = 'center';
        ctx.font = '600 12.5px -apple-system, system-ui, sans-serif';
        ctx.fillText(`${m} ${(v / N * 100).toFixed(0)}%`, cx + Math.cos(mid) * (R + 36), cy + Math.sin(mid) * (R + 36) + 4); }
      a0 = a1;
    }
    ctx.textAlign = 'center'; ctx.fillStyle = css('--dim');
    ctx.font = '12px -apple-system, system-ui, sans-serif'; ctx.fillText('自动化', cx, cy - 8);
    ctx.fillStyle = css('--fg'); ctx.font = '700 26px -apple-system, system-ui, sans-serif';
    ctx.fillText(pct(E.headline.automation), cx, cy + 20); ctx.textAlign = 'left';
  };
  const drawCad = () => {
    const cv = host.querySelector('#cad'); if (!cv) return;
    const { ctx, w } = fitCanvas(cv, 210);
    const h = 210, padL = 48, padT = 20, padB = 16;
    ctx.clearRect(0, 0, w, h);
    const cw = (w - padL - 12) / 24, ch = (h - padT - padB) / 7;
    const mx = Math.max(1, ...E.cadence.grid.map(g => g.n));
    ctx.font = '10.5px -apple-system, system-ui, sans-serif'; ctx.fillStyle = css('--dim2');
    E.cadence.weekday_labels.forEach((l, i) => ctx.fillText(l, 8, padT + i * ch + ch * .7));
    for (let hh = 0; hh < 24; hh += 3) ctx.fillText(String(hh).padStart(2, '0'), padL + hh * cw, padT - 7);
    for (const g of E.cadence.grid) {
      const a = g.n / mx;
      ctx.fillStyle = css('--acc'); ctx.globalAlpha = 0.1 + a * 0.9;
      ctx.beginPath();
      ctx.roundRect(padL + g.h * cw + 1, padT + g.wd * ch + 1, Math.max(1, cw - 2), Math.max(1, ch - 2), 3);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  };
  const all = () => { drawDonut(); drawCad(); };
  all();
  const onR = () => all();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  enter('.sec, .card, .orow', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
