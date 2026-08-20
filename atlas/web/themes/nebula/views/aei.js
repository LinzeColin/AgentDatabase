import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { hero, sec, grid, orbit, slab, drawer, table, warn, pill, state } from '../kit.js';

// 对齐 Anthropic Economic Index：五个经济原语 + 五种协作模式 + 产物 + 覆盖/有效覆盖
// + 领域/上下文/节律/迁移/ROI/机会，外加一份「AEI 有而这里做不到」的清单。
export async function render(host) {
  const E = D.A().aei, P = E.primitives, N = E.sessions_total;
  const modeOrder = ['指派', '反馈环', '迭代', '学习', '校验', '未归类'];
  const MODE_COL = { '指派': '#5ce6b4', '反馈环': '#2fae86', '迭代': '#7cc4ff',
                     '学习': '#b58cff', '校验': '#63d2ff', '未归类': '#5a6480' };
  const bands = (o, c) => orbit((o.bands || Object.keys(o.counts)).filter(b => o.counts[b])
    .map(b => ({ k: b, v: o.counts[b], label: `${o.counts[b]}　${pct(o.counts[b] / N)}`, c })));

  host.innerHTML = `
${hero('经济指数', '你这三个月，到底在产什么', `照着 Anthropic Economic Index 的骨架量的：
  ${esc(E.framework)}　每一项的口径都写在旁边，量不出来的单独列在最后。`)}

${grid([
  { k: '甩给它自己干的', v: pct(E.headline.automation), n: '指派 ＋ 反馈环', w: 3, tone: 'acc' },
  { k: '一起干的', v: pct(E.headline.augmentation), n: '迭代 ＋ 学习 ＋ 校验', w: 3, alt: true },
  { k: '平均放手程度', v: `${P.autonomy.avg}/5`, n: '1＝全程盯着 · 5＝完全撒手' },
  { k: '中位提速', v: P.complexity.speedup_median ? P.complexity.speedup_median + '×' : state('说不准'),
    n: `能算的只有 ${P.complexity.speedup_n} 场` },
  { k: '摊得开还是压一件', v: String(E.concentration.domain_hhi ?? '说不准'), n: '0＝摊开 · 1＝全压一件事' },
])}

<div class="slab" style="padding:8px 8px 4px"><canvas class="viz" id="donut" style="border:0;background:none" role="img" aria-label="协作模式与作息节律图。判据与逐行明细见下方表格。"></canvas></div>
${drawer('这五种模式各自的判据（AEI 原定义）',
  table([{ t: '模式' }, { t: '英文' }, { t: '算哪一边' }, { t: '判据' }],
    modeOrder.filter(m => E.modes[m]).map(m =>
      [`<b>${esc(m)}</b>`, esc(E.mode_defs[m].en), esc(E.mode_defs[m].group), esc(E.mode_defs[m].desc)])))}

${sec('五个经济原语', 'AEI 的骨架。做不到的在最后单独列，不含糊过去。')}
<div class="sub">① 任务有多难</div><p class="hint">${esc(P.complexity.note)}</p>${bands(P.complexity, 'var(--acc)')}
<div class="sub">② 用到哪一层本事</div><p class="hint">${esc(P.skill.note)}</p>${bands(P.skill, 'var(--acc2)')}
<div class="sub">③ 拿来干嘛</div>${bands({ counts: P.use_case.counts, bands: ['工作', '学习', '个人'] }, 'var(--ok)')}
<div class="sub">④ 放手到什么程度</div><p class="hint">${esc(P.autonomy.note)}</p>
${orbit(Object.entries(P.autonomy.counts).map(([k, v]) =>
  ({ k: P.autonomy.labels[k] || k, v, label: `${v}　${pct(v / N)}`, c: 'var(--acc2)' })))}
<div class="sub">⑤ 到底做成了没有</div><p class="hint">${esc(P.success.note)}</p>${bands(P.success, 'var(--warn)')}

${sec('行业分布：碰过多少，真做成多少',
  '「真做成的比例」＝碰过的比例 × 成功率。AEI 用这一对区分「摸过」和「做出来了」—— 只看前者会把自己骗了。')}
${orbit(E.domains.map(r => ({ k: r.domain, v: r.coverage,
  label: `碰过 ${pct(r.coverage)}　做成 ${r.effective_coverage == null ? '—' : pct(r.effective_coverage)}　${r.n} 场` })))}
${drawer('摊开行业明细', table(
  [{ t: '行业' }, { t: '会话', r: true }, { t: '碰过', r: true }, { t: '真做成', r: true },
   { t: '成功率', r: true }, { t: '甩手比例', r: true }, { t: '放手程度', r: true },
   { t: '每场新 token', r: true }, { t: '缓存占比', r: true }],
  E.domains.map(r => [esc(r.domain), String(r.n), pct(r.coverage),
    r.effective_coverage == null ? state('说不准') : pct(r.effective_coverage),
    r.success_rate == null ? state('说不准') : pct(r.success_rate),
    r.automation == null ? '—' : pct(r.automation), String(r.autonomy_avg ?? '—'),
    fmt(r.tokens_per_session), pct(r.cache_ratio)])))}
${E.domains_unclassified ? warn(`另有 <b>${E.domains_unclassified}</b> 场，一个行业词都没对上，照实标了「没归类」。
  不硬塞进某一行 —— 塞进去这张表就废了。`) : ''}

${sec('产出的是什么东西', esc(E.artifacts_note))}
${orbit(E.artifacts.map(a => ({ k: a.artifact, v: a.n, label: `${fmt(a.n)}　${pct(a.share)}`, c: 'var(--acc2)' })))}

${sec('在什么场景下用的', esc(E.context.note))}
${orbit(E.context.rows.slice(0, 14).map(r => ({ k: r.context, v: r.n,
  label: `${r.n} 场　${fmt(r.tokens)} 新 token` })))}

${sec('节律：你什么时候干活', esc(E.cadence.note))}
<div class="slab" style="padding:10px 12px 6px"><canvas class="viz" id="cad" style="border:0;background:none" role="img" aria-label="协作模式与作息节律图。判据与逐行明细见下方表格。"></canvas></div>

${sec('迁移：这三个月你从哪挪到了哪', esc(E.transition.note))}
${orbit(E.transition.drift.map(x => ({ k: x.domain, v: Math.abs(x.delta) * 1000,
  label: `${pct(x.early)} → ${pct(x.late)}　${x.delta >= 0 ? '涨' : '退'} ${(Math.abs(x.delta) * 100).toFixed(1)} 个点`,
  c: x.delta >= 0 ? 'var(--ok)' : 'var(--bad)' })))}

${sec('投入产出')}
${E.roi.state === '通' ? grid([
  { k: '每一条提交摊到', v: fmt(E.roi.tokens_per_commit), n: '个新 token', w: 3, tone: 'warn' },
  { k: '新 token 总共', v: fmt(E.roi.tokens_total), n: `另有 ${fmt(E.roi.cache_total)} 是重复读的缓存`, w: 3, alt: true },
  { k: '一条提交要聊几场', v: String(E.roi.sessions_per_commit), n: '场' },
  { k: '只聊没交付', v: `${E.roi.days_talk_only} 天`, n: `重合率 ${pct(E.roi.overlap_rate)}` },
]) + warn(esc(E.roi.cost_basis) + '<br>' + esc(E.roi.note))
   : warn(`<b>这块算不出来。</b>${esc(E.roi.why || '')}`)}

${sec('哪里有口子',
  '三条规则：甩得越干净的活越可能能打包卖；成功率低还烧得多的在流血；一直不敢放手的要么是护城河要么是包袱。')}
${E.opportunity.map(o => slab(`
  <div class="ck">${esc(o.kind)}　${pill(o.domain)}　${o.n} 场</div>
  <div class="cn" style="margin-top:9px;font-size:13.5px;line-height:1.7">${esc(o.why)}</div>`)).join('')}

${sec('AEI 有、这里没有的', '逐条列出来。不写成「后续迭代」糊过去。')}
${drawer('摊开', table([{ t: '缺什么' }, { t: '为什么现在给不出来' }],
  E.not_measured.map(x => [`<b>${esc(x.item)}</b>`, esc(x.why)])))}`;

  const drawDonut = () => {
    const cv = host.querySelector('#donut'); if (!cv) return;
    const H = 268, { ctx, w } = fitCanvas(cv, H);
    const cx = w / 2, cy = H / 2, R = Math.max(26, Math.min(94, H / 2 - 40));
    ctx.clearRect(0, 0, w, H);
    // 外圈：五种模式。内圈：自动化 / 增强 两分。星云版是双环，不是单甜甜圈。
    let a0 = -Math.PI / 2;
    ctx.lineWidth = 26; ctx.lineCap = 'butt';
    for (const m of modeOrder) {
      const v = E.modes[m] || 0; if (!v) continue;
      const a1 = a0 + (v / N) * 6.2832;
      ctx.strokeStyle = MODE_COL[m];
      ctx.shadowBlur = 16; ctx.shadowColor = MODE_COL[m];
      ctx.beginPath(); ctx.arc(cx, cy, R, a0, a1); ctx.stroke();
      ctx.shadowBlur = 0;
      const mid = (a0 + a1) / 2;
      if (v / N > 0.05) {
        ctx.fillStyle = cssVar('--fg'); ctx.textAlign = 'center';
        ctx.font = '600 12.5px -apple-system, system-ui, sans-serif';
        ctx.fillText(`${m} ${(v / N * 100).toFixed(0)}%`,
          cx + Math.cos(mid) * (R + 40), cy + Math.sin(mid) * (R + 40) + 4);
      }
      a0 = a1;
    }
    const au = E.headline.automation || 0;
    ctx.lineWidth = 7; ctx.strokeStyle = cssVar('--line');
    ctx.beginPath(); ctx.arc(cx, cy, R - 22, 0, 6.2832); ctx.stroke();
    ctx.strokeStyle = cssVar('--acc'); ctx.shadowBlur = 14; ctx.shadowColor = cssVar('--acc');
    ctx.beginPath(); ctx.arc(cx, cy, R - 22, -Math.PI / 2, -Math.PI / 2 + au * 6.2832); ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.textAlign = 'center'; ctx.fillStyle = cssVar('--dim');
    ctx.font = '11.5px -apple-system, system-ui, sans-serif';
    ctx.fillText('甩给它自己干的', cx, cy - 9);
    ctx.fillStyle = cssVar('--fg'); ctx.font = '700 27px -apple-system, system-ui, sans-serif';
    ctx.fillText(pct(au), cx, cy + 21);
    ctx.textAlign = 'left';
  };

  const drawCad = () => {
    const cv = host.querySelector('#cad'); if (!cv) return;
    const H = 214, { ctx, w } = fitCanvas(cv, H);
    const padL = 48, padT = 20, padB = 16;
    ctx.clearRect(0, 0, w, H);
    const cw = (w - padL - 14) / 24, ch = (H - padT - padB) / 7;
    const mx = Math.max(1, ...E.cadence.grid.map(g => g.n));
    ctx.font = '10.5px -apple-system, system-ui, sans-serif'; ctx.fillStyle = cssVar('--dim2');
    E.cadence.weekday_labels.forEach((l, i) => ctx.fillText(l, 8, padT + i * ch + ch * .7));
    for (let hh = 0; hh < 24; hh += 3) ctx.fillText(String(hh).padStart(2, '0'), padL + hh * cw, padT - 7);
    for (const g of E.cadence.grid) {
      const a = g.n / mx;
      ctx.fillStyle = cssVar('--acc'); ctx.globalAlpha = 0.1 + a * 0.9;
      if (a > .7) { ctx.shadowBlur = 10; ctx.shadowColor = cssVar('--acc'); }
      ctx.beginPath();
      ctx.roundRect(padL + g.h * cw + 1, padT + g.wd * ch + 1,
        Math.max(1, cw - 2), Math.max(1, ch - 2), 3);
      ctx.fill(); ctx.shadowBlur = 0;
    }
    ctx.globalAlpha = 1;
  };

  const all = () => { drawDonut(); drawCad(); };
  all();
  const onR = () => all();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  enter('.hero, .sec, .cell, .orow, .slab', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
