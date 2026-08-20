import { esc, fmt, pct, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { hero, sec, grid, orbit, slab, drawer, table, warn, pill, state } from '../kit.js';

// 对齐 Anthropic Economic Index。白昼版把甜甜圈换成**百分比堆叠条**（瑞士版式里
// 比例永远画成一条横带，不画成圆），节律换成印刷网点。数据口径与另外两个主题完全一致。
export async function render(host) {
  const E = D.A().aei, P = E.primitives, N = E.sessions_total;
  const modeOrder = ['指派', '反馈环', '迭代', '学习', '校验', '未归类'];
  const MODE_COL = { '指派': '#1f7a5a', '反馈环': '#2fae86', '迭代': '#2563eb',
                     '学习': '#7c3aed', '校验': '#0891b2', '未归类': '#9aa0a6' };
  const bands = (o, c) => orbit((o.bands || Object.keys(o.counts)).filter(b => o.counts[b])
    .map(b => ({ k: b, v: o.counts[b], label: `${o.counts[b]}　${pct(o.counts[b] / N)}`, c })));

  host.innerHTML = `
${hero('经济指数', '你这三个月，到底在产什么',
  `照着 Anthropic Economic Index 的骨架量的：${esc(E.framework)}
   每一项的口径都写在旁边，量不出来的单独列在最后 —— 不含糊过去。`)}

${grid([
  { k: '甩给它自己干的', v: pct(E.headline.automation), n: '指派 ＋ 反馈环', w: 3, tone: 'acc' },
  { k: '一起干的', v: pct(E.headline.augmentation), n: '迭代 ＋ 学习 ＋ 校验', w: 3 },
  { k: '平均放手程度', v: `${P.autonomy.avg}/5`, n: '1＝全程盯着　5＝完全撒手', w: 3 },
  { k: '中位提速', v: P.complexity.speedup_median ? P.complexity.speedup_median + '×' : state('说不准'),
    n: `能算的只有 ${P.complexity.speedup_n} 场`, w: 3 },
])}

${sec('五种协作模式的配比', 'AEI 把它们分成两边：指派、反馈环算「自动化」；迭代、学习、校验算「增强」。')}
<canvas class="viz" id="stackbar" role="img" aria-label="协作模式与作息节律图。判据与逐行明细见下方表格。"></canvas>
<div id="legend"></div>
${drawer('这五种模式各自的判据（AEI 原定义）',
  table([{ t: '模式' }, { t: '英文' }, { t: '算哪一边' }, { t: '判据' }],
    modeOrder.filter(m => E.modes[m]).map(m =>
      [`<b>${esc(m)}</b>`, esc(E.mode_defs[m].en), esc(E.mode_defs[m].group), esc(E.mode_defs[m].desc)])))}

${sec('五个经济原语', 'AEI 的骨架。')}
<div class="sub">① 任务有多难</div><p class="hint">${esc(P.complexity.note)}</p>${bands(P.complexity, 'var(--acc)')}
<div class="sub">② 用到哪一层本事</div><p class="hint">${esc(P.skill.note)}</p>${bands(P.skill, 'var(--acc2)')}
<div class="sub">③ 拿来干嘛</div>${bands({ counts: P.use_case.counts, bands: ['工作', '学习', '个人'] }, 'var(--ok)')}
<div class="sub">④ 放手到什么程度</div><p class="hint">${esc(P.autonomy.note)}</p>
${orbit(Object.entries(P.autonomy.counts).map(([k, v]) =>
  ({ k: P.autonomy.labels[k] || k, v, label: `${v}　${pct(v / N)}` })))}
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
${orbit(E.artifacts.map(a => ({ k: a.artifact, v: a.n, label: `${fmt(a.n)}　${pct(a.share)}` })))}

${sec('在什么场景下用的', esc(E.context.note))}
${orbit(E.context.rows.slice(0, 14).map(r => ({ k: r.context, v: r.n,
  label: `${r.n} 场　${fmt(r.tokens)} 新 token` })))}

${sec('节律：你什么时候干活', esc(E.cadence.note))}
<canvas class="viz" id="cad" role="img" aria-label="协作模式与作息节律图。判据与逐行明细见下方表格。"></canvas>

${sec('迁移：这三个月你从哪挪到了哪', esc(E.transition.note))}
${orbit(E.transition.drift.map(x => ({ k: x.domain, v: Math.abs(x.delta) * 1000,
  label: `${pct(x.early)} → ${pct(x.late)}　${x.delta >= 0 ? '涨' : '退'} ${(Math.abs(x.delta) * 100).toFixed(1)} 个点` })))}

${sec('投入产出')}
${E.roi.state === '通' ? grid([
  { k: '每一条提交摊到', v: fmt(E.roi.tokens_per_commit), n: '个新 token', w: 3, tone: 'warn' },
  { k: '新 token 总共', v: fmt(E.roi.tokens_total), n: `另有 ${fmt(E.roi.cache_total)} 是重复读的缓存`, w: 3 },
  { k: '一条提交要聊几场', v: String(E.roi.sessions_per_commit), n: '场', w: 3 },
  { k: '只聊没交付', v: `${E.roi.days_talk_only} 天`, n: `重合率 ${pct(E.roi.overlap_rate)}`, w: 3 },
]) + warn(esc(E.roi.cost_basis) + '<br>' + esc(E.roi.note))
   : warn(`<b>这块算不出来。</b>${esc(E.roi.why || '')}`)}

${sec('哪里有口子',
  '三条规则：甩得越干净的活越可能能打包卖；成功率低还烧得多的在流血；一直不敢放手的要么是护城河要么是包袱。')}
${E.opportunity.map(o => slab(`
  <div class="ck">${esc(o.kind)}　${pill(o.domain)}　${o.n} 场</div>
  <div class="cn" style="margin-top:8px;font-size:13.5px;line-height:1.75;max-width:70ch">${esc(o.why)}</div>`)).join('')}

${sec('AEI 有、这里没有的', '逐条列出来。不写成「后续迭代」糊过去。')}
${drawer('摊开', table([{ t: '缺什么' }, { t: '为什么现在给不出来' }],
  E.not_measured.map(x => [`<b>${esc(x.item)}</b>`, esc(x.why)])))}`;

  const drawBar = () => {
    const cv = host.querySelector('#stackbar'); if (!cv) return;
    const H = 74, { ctx, w } = fitCanvas(cv, H);
    ctx.clearRect(0, 0, w, H);
    const barY = 16, barH = 34;
    let x = 0;
    for (const m of modeOrder) {
      const v = E.modes[m] || 0; if (!v) continue;
      const bw = (v / N) * w;
      ctx.fillStyle = MODE_COL[m];
      ctx.fillRect(x, barY, bw, barH);
      if (bw > 46) {
        ctx.fillStyle = '#fff'; ctx.font = '600 11px -apple-system, system-ui, sans-serif';
        ctx.fillText(`${(v / N * 100).toFixed(0)}%`, x + 7, barY + barH / 2 + 4);
      }
      x += bw;
    }
    // 自动化 / 增强 的分界线：一条压在条上的实线 + 上方标注
    const cut = (E.headline.automation || 0) * w;
    ctx.strokeStyle = cssVar('--fg'); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(cut, barY - 8); ctx.lineTo(cut, barY + barH + 8); ctx.stroke();
    ctx.fillStyle = cssVar('--fg'); ctx.font = '600 11px -apple-system, system-ui, sans-serif';
    ctx.fillText(`自动化 ${pct(E.headline.automation)}`, 2, 11);
    ctx.textAlign = 'right';
    ctx.fillText(`增强 ${pct(E.headline.augmentation)}`, w - 2, 11);
    ctx.textAlign = 'left';
    host.querySelector('#legend').innerHTML = `<p class="hint">${modeOrder.filter(m => E.modes[m])
      .map(m => `<span class="pill" style="border-color:${MODE_COL[m]};color:${MODE_COL[m]}">${esc(m)} ${E.modes[m]}</span>`)
      .join('')}</p>`;
  };

  const drawCad = () => {
    const cv = host.querySelector('#cad'); if (!cv) return;
    const H = 208, { ctx, w } = fitCanvas(cv, H);
    const padL = 46, padT = 20, padB = 14;
    ctx.clearRect(0, 0, w, H);
    const cw = (w - padL - 12) / 24, ch = (H - padT - padB) / 7;
    const mx = Math.max(1, ...E.cadence.grid.map(g => g.n));
    ctx.font = '10px ui-monospace, SF Mono, Menlo, monospace'; ctx.fillStyle = cssVar('--dim2');
    E.cadence.weekday_labels.forEach((l, i) => ctx.fillText(l, 8, padT + i * ch + ch * 0.68));
    for (let hh = 0; hh < 24; hh += 3) ctx.fillText(String(hh).padStart(2, '0'), padL + hh * cw, padT - 7);
    // 印刷网点：面积编码强度，不是透明度 —— 打印出来也读得出。
    for (const g of E.cadence.grid) {
      const a = g.n / mx;
      const r = Math.max(1, Math.sqrt(a) * Math.min(cw, ch) * 0.46);
      ctx.fillStyle = a > 0.66 ? cssVar('--acc') : cssVar('--fg');
      ctx.beginPath();
      ctx.arc(padL + g.h * cw + cw / 2, padT + g.wd * ch + ch / 2, r, 0, 6.2832);
      ctx.fill();
    }
    ctx.strokeStyle = cssVar('--hair'); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(padL, padT - 3); ctx.lineTo(w - 12, padT - 3); ctx.stroke();
  };

  const all = () => { drawBar(); drawCad(); };
  all();
  const onR = () => all();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  enter('.hero, .sec, .cell, .orow, .slab', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
