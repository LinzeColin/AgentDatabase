import { esc, pct, fmt, go, enter, topicColor, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas , cssVar } from '../../../core/g3d.js';
import { sec, bento, orbit, drawer, table, warn, pill, state } from '../kit.js';

export async function render(host) {
  const E = D.A().aei, n = E.sessions_total;
  const modeOrder = ['指派', '反馈环', '迭代', '学习', '校验', '未归类'];
  const MODE_COL = { '指派': '#5ce6b4', '反馈环': '#2fae86', '迭代': '#7cc4ff', '学习': '#b58cff', '校验': '#63d2ff', '未归类': '#5a6480' };

  host.innerHTML = `
${sec('经济指数', esc(E.framework))}
${bento([
  { k: '自动化', v: pct(E.headline.automation), n: '指派 + 反馈环', w: 3, tone: 'acc' },
  { k: '增强', v: pct(E.headline.augmentation), n: '迭代 + 学习 + 校验', w: 3, alt: true },
  { k: '已归类', v: `${E.sessions_classified}/${n}`, n: E.headline.unclassified_n ? `未归类 ${E.headline.unclassified_n}` : '全部归类' },
  { k: '任务集中度', v: E.concentration.task_hhi == null ? '不确定' : E.concentration.task_hhi.toFixed(3), n: '0 摊开 · 1 全压一件事' },
  { k: '项目集中度', v: E.concentration.project_hhi == null ? '不确定' : E.concentration.project_hhi.toFixed(3), n: 'HHI' },
])}
<canvas class="viz" id="donut" height="250"></canvas>
${drawer('五种模式的判据', table([{ t: '模式' }, { t: '归属' }, { t: '判据' }],
  modeOrder.filter(m => E.modes[m]).map(m => [`<b>${esc(m)}</b>`, esc(E.mode_defs[m].group), esc(E.mode_defs[m].desc)])))}

${sec('哪类活已经能交出去', 'AEI 最有信息量的一刀：不是整体自动化了多少，是<b>每一类各自</b>自动化了多少。')}
${orbit(E.by_task.filter(r => r.automation != null).map(r => ({
  k: r.task, v: r.automation, label: `${pct(r.automation)}　${r.n} 场`,
  c: topicColor(r.task), attr: `data-topic="${esc(r.task)}"` })))}
${(() => {
  const rows = E.by_task.filter(r => r.automation != null).sort((a, b) => a.automation - b.automation);
  return warn(`<b>最能交出去的：</b>${rows.slice(-3).reverse().map(r => `${esc(r.task)} ${pct(r.automation)}`).join('、')}。
    <b>最离不开你的：</b>${rows.slice(0, 3).map(r => `${esc(r.task)} ${pct(r.automation)}`).join('、')}。<br>
    离不开你的那几类，要么是别人替不了的价值，要么是还没被固化的负债 —— 哪一种只有你知道。这一页不替你判断。`);
})()}

${sec('用到了哪些能力', esc(E.skills_note))}
${orbit(E.skills.map(s => ({ k: s.skill, v: s.n, label: `${fmt(s.n)}　${pct(s.share)}`, c: 'var(--acc)' })))}

${sec('模式构成随时间')}
<canvas class="viz" id="mix" height="240"></canvas>
<p class="hint">${modeOrder.filter(m => E.modes[m]).map(m =>
  `<span class="pill" style="color:${MODE_COL[m]}">■ ${esc(m)}</span>`).join('')}</p>

${sec('深度与广度', '广＝碰过多少类活；深＝每类平均开了多少场。')}
${drawer('展开', table([{ t: '项目' }, { t: '会话', r: true }, { t: '广', r: true }, { t: '深', r: true }, { t: '类别' }],
  E.depth_breadth.map(r => [esc(r.project), String(r.sessions), String(r.breadth), r.depth.toFixed(1),
    r.topics.slice(0, 6).map(t => pill(t)).join('')])))}`;

  const css = k => cssVar(k);
  const drawDonut = () => {
    const { ctx, w } = fitCanvas(host.querySelector('#donut'), 250);
    const h = 250, cx = w / 2, cy = h / 2, R = Math.max(24, Math.min(92, h / 2 - 34));
    ctx.clearRect(0, 0, w, h);
    let a0 = -Math.PI / 2;
    ctx.lineWidth = 32;
    for (const m of modeOrder) {
      const v = E.modes[m] || 0; if (!v) continue;
      const a1 = a0 + (v / n) * 6.2832;
      ctx.strokeStyle = MODE_COL[m];
      ctx.beginPath(); ctx.arc(cx, cy, R, a0, a1); ctx.stroke();
      const mid = (a0 + a1) / 2;
      if (v / n > 0.05) {
        ctx.fillStyle = css('--fg'); ctx.textAlign = 'center';
        ctx.font = '600 12.5px -apple-system, system-ui, sans-serif';
        ctx.fillText(`${m} ${(v / n * 100).toFixed(0)}%`, cx + Math.cos(mid) * (R + 36), cy + Math.sin(mid) * (R + 36) + 4);
      }
      a0 = a1;
    }
    ctx.textAlign = 'center'; ctx.fillStyle = css('--dim');
    ctx.font = '12px -apple-system, system-ui, sans-serif'; ctx.fillText('自动化', cx, cy - 8);
    ctx.fillStyle = css('--fg'); ctx.font = '700 26px -apple-system, system-ui, sans-serif';
    ctx.fillText(pct(E.headline.automation), cx, cy + 20);
    ctx.textAlign = 'left';
  };
  const drawMix = () => {
    const { ctx, w } = fitCanvas(host.querySelector('#mix'), 240);
    const h = 240, padB = 24, padT = 10;
    ctx.clearRect(0, 0, w, h);
    const W = E.by_week.filter(x => x.n > 0);
    if (!W.length) return;
    const xs = i => 12 + (i / Math.max(1, W.length - 1)) * (w - 24);
    let base = W.map(() => h - padB);
    for (const m of modeOrder) {
      const top = W.map((wk, i) => {
        const tot = Object.values(wk.modes).reduce((a, b) => a + b, 0) || 1;
        return base[i] - ((wk.modes[m] || 0) / tot) * (h - padB - padT);
      });
      ctx.beginPath(); ctx.moveTo(xs(0), base[0]);
      for (let i = 0; i < W.length; i++) {
        const px = xs(i), py = top[i];
        if (i === 0) ctx.lineTo(px, py);
        else { const qx = xs(i - 1), qy = top[i - 1];
          ctx.bezierCurveTo((qx + px) / 2, qy, (qx + px) / 2, py, px, py); }
      }
      for (let i = W.length - 1; i >= 0; i--) ctx.lineTo(xs(i), base[i]);
      ctx.closePath(); ctx.fillStyle = MODE_COL[m];
      ctx.globalAlpha = S.mode === 'dark' ? .85 : .72; ctx.fill();
      base = top;
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = css('--dim2'); ctx.font = '10.5px -apple-system, system-ui, sans-serif';
    const step = Math.ceil(W.length / 10);
    W.forEach((wk, i) => { if (i % step === 0) ctx.fillText(wk.w.slice(2), xs(i) - 12, h - 8); });
  };
  const all = () => { drawDonut(); drawMix(); };
  all();
  const onR = () => all();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  enter('.sec, .card, .orow', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
