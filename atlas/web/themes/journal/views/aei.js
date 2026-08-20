import { esc, fmt, pct, go, enter, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { sec, lede, p, n, big, aside, note, figure, rank, spark, table, state } from '../kit.js';

export async function render(host) {
  const E = D.A().aei, P = E.primitives, N = E.sessions_total;
  const order = ['指派', '反馈环', '迭代', '学习', '校验', '未归类'];
  const css = k => cssVar(k);
  const bandFig = (o, cap) => figure(rank((o.bands || Object.keys(o.counts)).filter(b => o.counts[b])
    .map(b => ({ k: b, v: o.counts[b], label: `${o.counts[b]}　${pct(o.counts[b] / N)}` }))), cap);
  const top = E.domains.slice(0, 3);
  const bleed = E.opportunity.filter(o => o.kind === '在流血');

  host.innerHTML = `
${sec('经济指数')}
${lede(`Anthropic 的 Economic Index 不只是「自动化还是协作」那一刀。它的骨架是
  <b>五个经济原语</b>（任务复杂度、技能层级、用途、AI 自主度、任务成功）、
  <b>协作五模式</b>、<b>产物分类</b>、<b>覆盖率与有效覆盖率</b>、
  <b>按职业的 token 消耗</b>、<b>地理分布</b>与 <b>cadence</b>。
  把这套框架放到你的 ${n(N)} 场会话上，答案在下面。`)}
${aside(esc(E.framework))}
<div class="pull">自动化 ${pct(E.headline.automation)}　增强 ${pct(E.headline.augmentation)}　平均自主度 ${P.autonomy.avg} / 5</div>

${sec('五个经济原语')}
${p(`<b>一、任务复杂度。</b>${esc(P.complexity.note)}
  能算出加速倍数的有 ${n(P.complexity.speedup_n)} 场，中位数 ${big((P.complexity.speedup_median ?? '不确定') + '×')}。`)}
${bandFig(P.complexity, '「没有 AI 大概要多久」的分布。这是估计，不是测量。')}
${p(`<b>二、技能层级。</b>${esc(P.skill.note)}`)}
${bandFig(P.skill, '术语密度分布。')}
${p(`<b>三、用途。</b>工作 ${n(P.use_case.counts['工作'] || 0)} 场、学习 ${n(P.use_case.counts['学习'] || 0)} 场、
  个人 ${n(P.use_case.counts['个人'] || 0)} 场。`)}
${p(`<b>四、AI 自主度。</b>${esc(P.autonomy.note)}平均 ${big(P.autonomy.avg + ' / 5')}。`)}
${figure(rank(Object.entries(P.autonomy.counts).map(([k, v]) =>
  ({ k: P.autonomy.labels[k] || k, v, label: `${v}　${pct(v / N)}` }))), '自主度分布。')}
${p(`<b>五、任务成功。</b>${esc(P.success.note)}`)}
${bandFig(P.success, '成功判定分布。')}

${sec('协作五模式')}
${figure(table([{ t: '模式' }, { t: 'EN' }, { t: '归属' }, { t: '会话', r: true }, { t: '判据' }],
  order.filter(m => E.modes[m]).map(m => [`<b>${esc(m)}</b>`, esc(E.mode_defs[m].en),
    esc(E.mode_defs[m].group), String(E.modes[m]), esc(E.mode_defs[m].desc)])),
  'AEI 的原定义。自动化 = 指派 + 反馈环。')}

${sec('领域：碰过 vs 真的做成了')}
${lede(`AEI 用<b>有效覆盖率</b>（覆盖率 × 成功率）区分这两件事。你碰得最多的三块是
  ${top.map(r => `<b>${esc(r.domain)}</b>（${r.n} 场，覆盖 ${pct(r.coverage)}）`).join('、')}。`)}
${figure(table([{ t: '领域' }, { t: '会话', r: true }, { t: '覆盖率', r: true }, { t: '有效覆盖', r: true },
  { t: '成功率', r: true }, { t: '自动化', r: true }, { t: '自主度', r: true }, { t: '新token/场', r: true }],
  E.domains.map(r => [esc(r.domain), String(r.n), pct(r.coverage),
    r.effective_coverage == null ? state('不确定') : pct(r.effective_coverage),
    r.success_rate == null ? state('不确定') : pct(r.success_rate),
    r.automation == null ? '—' : pct(r.automation), r.autonomy_avg ?? '—', fmt(r.tokens_per_session)])),
  '覆盖率＝这类活占你多少会话；有效覆盖＝其中多半成了的那部分。')}

${sec('产物分类')}
${p(esc(E.artifacts_note))}
${figure(rank(E.artifacts.map(a => ({ k: a.artifact, v: a.n, label: `${fmt(a.n)}　${pct(a.share)}` }))), '产出类型分布。')}

${sec('上下文分布')}
${p(esc(E.context.note) + `　集中度 HHI ${E.context.hhi ?? '不确定'}。`)}
${figure(rank(E.context.rows.slice(0, 14).map(r =>
  ({ k: r.context, v: r.n, label: `${r.n} 场　${fmt(r.tokens)}` }))), '注意力落在哪几块地方。')}

${sec('Cadence')}
${figure('<canvas class="viz" id="cad" height="200"></canvas>', esc(E.cadence.note))}

${sec('转换轨迹')}
${(() => {
  const up = E.transition.drift.filter(x => x.delta > 0).slice(0, 3);
  const dn = E.transition.drift.filter(x => x.delta < 0).slice(-3).reverse();
  return lede(`把这段时间按会话数切成前后两半，份额升得最多的是
    ${up.map(x => `<b>${esc(x.domain)}</b>（${pct(x.early)} → ${pct(x.late)}）`).join('、')}；
    降得最多的是 ${dn.map(x => `<b>${esc(x.domain)}</b>（${pct(x.early)} → ${pct(x.late)}）`).join('、')}。
    这就是 AEI 里「职业／经济转换」那一维在你身上的样子。`);
})()}
${figure(rank(E.transition.drift.map(x => ({ k: x.domain, v: Math.abs(x.delta) * 1000,
  label: `${pct(x.early)} → ${pct(x.late)}　${x.delta >= 0 ? '↑' : '↓'}${(Math.abs(x.delta) * 100).toFixed(1)}` }))),
  '前半段 vs 后半段的份额漂移，按会话数加权。')}

${sec('ROI')}
${E.roi.state === '通' ? lede(`一共读进 ${big(fmt(E.roi.tokens_total))} 个<b>新</b> token
  （另有 ${n(fmt(E.roi.cache_total))} 是缓存命中，单价低一个数量级，不算进成本）。
  同期产生 ${n(E.roi.commits)} 条提交 —— 每条平摊 ${big(fmt(E.roi.tokens_per_commit))} 个新 token，
  平均 ${n(E.roi.sessions_per_commit)} 场会话换一条。`) + note(esc(E.roi.cost_basis) + ' ' + esc(E.roi.note))
  : note(`<b>状态：不确定。</b>${esc(E.roi.why || '')}`)}

${sec('机会挖掘')}
${bleed.length ? note(`<b>正在流血的：</b>${bleed.map(o => esc(o.domain)).join('、')} ——
  投入不小，但判得出结果的里多半没成。`) : ''}
${E.opportunity.map(o => p(`<b>${esc(o.kind)}｜${esc(o.domain)}</b>（${o.n} 场）<br>
  <span style="color:var(--dim)">${esc(o.why)}</span>`)).join('')}

${sec('做不到的')}
${p(`AEI 有而这里没有的，逐条列出来 —— 不含糊过去。`)}
${figure(table([{ t: '项' }, { t: '为什么没有' }],
  E.not_measured.map(x => [`<b>${esc(x.item)}</b>`, esc(x.why)])), '缺口清单。')}`;

  const drawCad = () => {
    const cv = host.querySelector('#cad'); if (!cv) return;
    const { ctx, w } = fitCanvas(cv, 200);
    const h = 200, padL = 46, padT = 18, padB = 16;
    ctx.clearRect(0, 0, w, h);
    const cw = (w - padL - 10) / 24, ch = (h - padT - padB) / 7;
    const mx = Math.max(1, ...E.cadence.grid.map(g => g.n));
    ctx.font = '10px -apple-system, system-ui, sans-serif'; ctx.fillStyle = css('--dim2');
    E.cadence.weekday_labels.forEach((l, i) => ctx.fillText(l, 6, padT + i * ch + ch * .7));
    for (let hh = 0; hh < 24; hh += 4) ctx.fillText(String(hh).padStart(2, '0'), padL + hh * cw, padT - 6);
    for (const g of E.cadence.grid) {
      ctx.fillStyle = css('--acc'); ctx.globalAlpha = 0.08 + (g.n / mx) * 0.82;
      ctx.fillRect(padL + g.h * cw + .5, padT + g.wd * ch + .5, cw - 1, ch - 1);
    }
    ctx.globalAlpha = 1;
  };
  drawCad();
  const onR = () => drawCad();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  enter('.sec, p.body, figure, .aside', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
