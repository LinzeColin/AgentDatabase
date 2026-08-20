import { esc, fmt, pct, go, enter, topicColor, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { sec, kv, table, meter, spark, warn, state } from '../kit.js';

// 对齐 Anthropic Economic Index：五个经济原语 + 协作五模式 + 产物分类
// + 覆盖率与有效覆盖率 + 按领域 token + Cadence + 转换轨迹 + ROI。
export async function render(host) {
  const E = D.A().aei, P = E.primitives, N = E.sessions_total;
  const modeOrder = ['指派', '反馈环', '迭代', '学习', '校验', '未归类'];
  const css = k => cssVar(k);

  const bandRow = (obj, key) => {
    const c = obj.counts, order = obj.bands || Object.keys(c);
    const mx = Math.max(1, ...Object.values(c));
    return table([{ t: key }, { t: '会话', r: true }, { t: '占比', r: true }, { t: '' }],
      order.filter(b => c[b]).map(b => [esc(b), String(c[b]), pct(c[b] / N), meter(c[b], mx, 120)]));
  };

  host.innerHTML = `
${sec('ECONOMIC INDEX', esc(E.framework))}
${kv([
  ['自动化份额', pct(E.headline.automation), 'acc'],
  ['增强份额', pct(E.headline.augmentation), ''],
  ['平均 AI 自主度', `${P.autonomy.avg} / 5`, 'acc'],
  ['中位加速', P.complexity.speedup_median ? P.complexity.speedup_median + '×' : '不确定', ''],
  ['领域集中度 HHI', E.concentration.domain_hhi ?? '不确定', ''],
  ['未归类', String(E.headline.unclassified_n), E.headline.unclassified_n ? 'warn' : ''],
])}

${sec('PRIMITIVE 1 · 任务复杂度', esc(P.complexity.note))}
${bandRow(P.complexity, '没有 AI 大概要多久')}
<p class="hint">中位加速 ${P.complexity.speedup_median ?? '不确定'}× （能算的 ${P.complexity.speedup_n} 场）。
  会话挂着不动的时间也算在墙上时钟里，所以这个倍数偏保守。</p>

${sec('PRIMITIVE 2 · 技能层级', esc(P.skill.note))}
${bandRow(P.skill, '术语密度')}

${sec('PRIMITIVE 3 · 用途', esc(P.use_case.note))}
${bandRow({ counts: P.use_case.counts, bands: ['工作', '学习', '个人'] }, '用途')}

${sec('PRIMITIVE 4 · AI 自主度', esc(P.autonomy.note))}
${table([{ t: '档位' }, { t: '会话', r: true }, { t: '占比', r: true }, { t: '' }],
  Object.entries(P.autonomy.counts).map(([k, v]) =>
    [esc(P.autonomy.labels[k] || k), String(v), pct(v / N),
     meter(v, Math.max(1, ...Object.values(P.autonomy.counts)), 120)]))}

${sec('PRIMITIVE 5 · 任务成功', esc(P.success.note))}
${bandRow(P.success, '判定')}

${sec('COLLABORATION MODES', '五种模式（AEI 原定义）。自动化 = 指派 + 反馈环。')}
${table([{ t: '模式' }, { t: 'EN' }, { t: '归属' }, { t: '会话', r: true }, { t: '占比', r: true }, { t: '判据' }],
  modeOrder.filter(m => E.modes[m]).map(m => [
    `<b>${esc(m)}</b>`, `<span class="tag">${esc(E.mode_defs[m].en)}</span>`,
    esc(E.mode_defs[m].group), String(E.modes[m]), pct(E.modes[m] / N),
    `<span class="tag">${esc(E.mode_defs[m].desc)}</span>`]))}

${sec('DOMAINS · 覆盖率与有效覆盖率', '有效覆盖率 = 覆盖率 × 成功率。AEI 用它区分「碰过」与「真的做成了」。')}
${table([{ t: '领域' }, { t: '会话', r: true }, { t: '覆盖率', r: true }, { t: '有效覆盖', r: true },
         { t: '成功率', r: true }, { t: '自动化', r: true }, { t: '自主度', r: true },
         { t: '新token/场', r: true }, { t: '缓存占比', r: true }, { t: '' }],
  E.domains.map(r => [
    `<span class="lnk" data-dom="${esc(r.domain)}">${esc(r.domain)}</span>`, String(r.n),
    pct(r.coverage), r.effective_coverage == null ? '<span class="st" data-s="不确定">—</span>' : pct(r.effective_coverage),
    r.success_rate == null ? '<span class="st" data-s="不确定">—</span>' : pct(r.success_rate),
    r.automation == null ? '—' : pct(r.automation),
    r.autonomy_avg == null ? '—' : r.autonomy_avg,
    fmt(r.tokens_per_session), pct(r.cache_ratio),
    meter(r.n, Math.max(1, ...E.domains.map(x => x.n)), 90)]))}
${E.domains_unclassified ? warn(`另有 <b>${E.domains_unclassified}</b> 场一个领域词都没命中，如实标未归类，不硬塞。`) : ''}

${sec('ARTIFACTS · 产物分类', esc(E.artifacts_note))}
${table([{ t: '产出类型' }, { t: '次数', r: true }, { t: '占比', r: true }, { t: '' }],
  E.artifacts.map(a => [`<b>${esc(a.artifact)}</b>`, fmt(a.n), pct(a.share),
    meter(a.n, Math.max(1, ...E.artifacts.map(x => x.n)), 140)]))}

${sec('CONTEXT · 上下文分布', esc(E.context.note))}
${table([{ t: '项目 / 工作区' }, { t: '会话', r: true }, { t: '新token', r: true }, { t: '新token/场', r: true }, { t: '' }],
  E.context.rows.map(r => [esc(r.context), String(r.n), fmt(r.tokens), fmt(r.tokens_per_session),
    meter(r.n, Math.max(1, ...E.context.rows.map(x => x.n)), 100)]))}
<p class="hint">集中度 HHI ${E.context.hhi ?? '不确定'}。</p>

${sec('CADENCE · 小时 × 星期', esc(E.cadence.note))}
<canvas class="viz" id="cad" height="200"></canvas>

${sec('TRANSITION · 转换轨迹', esc(E.transition.note))}
${table([{ t: '领域' }, { t: '前半段', r: true }, { t: '后半段', r: true }, { t: '漂移', r: true }, { t: '' }],
  E.transition.drift.map(x => [esc(x.domain), pct(x.early), pct(x.late),
    `<span style="color:${x.delta >= 0 ? 'var(--ok)' : 'var(--bad)'}">${x.delta >= 0 ? '↑' : '↓'}${(Math.abs(x.delta) * 100).toFixed(1)}</span>`,
    `<span class="meter" style="width:${Math.min(120, Math.abs(x.delta) * 400).toFixed(0)}px;background:${x.delta >= 0 ? 'var(--ok)' : 'var(--bad)'}"></span>`]))}

${sec('ROI')}
${E.roi.state === '通' ? kv([
  ['新 token 合计', fmt(E.roi.tokens_total), 'acc'],
  ['缓存读取', fmt(E.roi.cache_total), ''],
  ['每条提交平摊', fmt(E.roi.tokens_per_commit) + ' 新token', 'warn'],
  ['每条提交要几场会话', String(E.roi.sessions_per_commit), ''],
  ['只聊没交付', E.roi.days_talk_only + ' 天', 'warn'],
  ['重合率', pct(E.roi.overlap_rate), ''],
]) + warn(esc(E.roi.cost_basis) + '<br>' + esc(E.roi.note)) : warn(`<b>状态：不确定。</b>${esc(E.roi.why || '')}`)}

${sec('OPPORTUNITY · 机会挖掘', '按「高委派 = 已定型可产品化」「低成功 + 高投入 = 在流血」「低自主度 = 护城河或负债」三条规则找出来的。')}
${table([{ t: '类型' }, { t: '领域' }, { t: '会话', r: true }, { t: '为什么' }],
  E.opportunity.map(o => [`<b>${esc(o.kind)}</b>`, esc(o.domain), String(o.n),
    `<span class="tag">${esc(o.why)}</span>`]))}

${sec('NOT MEASURED · 做不到的', 'AEI 有而这里没有的，逐条列出来 —— 不含糊过去。')}
${table([{ t: '项' }, { t: '为什么没有' }],
  E.not_measured.map(x => [`<b>${esc(x.item)}</b>`, `<span class="tag">${esc(x.why)}</span>`]))}`;

  const drawCad = () => {
    const cv = host.querySelector('#cad'); if (!cv) return;
    const { ctx, w } = fitCanvas(cv, 200);
    const h = 200, padL = 44, padT = 18, padB = 18;
    ctx.clearRect(0, 0, w, h);
    const cw = (w - padL - 10) / 24, ch = (h - padT - padB) / 7;
    const mx = Math.max(1, ...E.cadence.grid.map(g => g.n));
    ctx.font = '10px ui-monospace, monospace';
    ctx.fillStyle = css('--dim2');
    E.cadence.weekday_labels.forEach((l, i) => ctx.fillText(l, 6, padT + i * ch + ch * .72));
    for (let hh = 0; hh < 24; hh += 3) ctx.fillText(String(hh).padStart(2, '0'), padL + hh * cw, padT - 6);
    for (const g of E.cadence.grid) {
      const a = g.n / mx;
      ctx.fillStyle = css('--acc');
      ctx.globalAlpha = 0.12 + a * 0.88;
      ctx.fillRect(padL + g.h * cw + .5, padT + g.wd * ch + .5, cw - 1.5, ch - 1.5);
    }
    ctx.globalAlpha = 1;
  };
  drawCad();
  const onR = () => drawCad();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-dom]');
    if (d) go('grid', '');
  });
  enter('.sec, .kv > div, tbody tr', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
