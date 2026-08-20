import { esc, fmt, pct, go, enter, topicColor, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas } from '../../../core/g3d.js';
import { sec, kv, table, meter, spark, warn, state } from '../kit.js';

// 对标 Anthropic Economic Index：五种协作模式，不是两分法。
// AEI 真正的看点不是总自动化率，是「哪类活已经能交出去、哪类还得你盯着」。
export async function render(host) {
  const E = D.A().aei;
  const G = { '自动化': 'var(--ok)', '增强': 'var(--acc)' };
  const modeOrder = ['指派', '反馈环', '迭代', '学习', '校验', '未归类'];
  const n = E.sessions_total;

  host.innerHTML = `
${sec('ECONOMIC INDEX', esc(E.framework))}
${kv([
  ['自动化', pct(E.headline.automation), 'acc'],
  ['增强', pct(E.headline.augmentation), ''],
  ['已归类', `${E.sessions_classified} / ${n}`, ''],
  ['未归类', String(E.headline.unclassified_n), E.headline.unclassified_n ? 'warn' : ''],
  ['任务集中度 HHI', E.concentration.task_hhi == null ? '不确定' : E.concentration.task_hhi.toFixed(3), ''],
  ['项目集中度 HHI', E.concentration.project_hhi == null ? '不确定' : E.concentration.project_hhi.toFixed(3), ''],
])}

${sec('COLLABORATION MODES', '五种模式的定义与占比。判据写在右边，不用猜。')}
${table([{ t: '模式' }, { t: '归属' }, { t: '会话', r: true }, { t: '占比', r: true }, { t: '' }, { t: '判据' }],
  modeOrder.filter(m => E.modes[m]).map(m => [
    `<b>${esc(m)}</b>`,
    `<span class="tag">${esc(E.mode_defs[m].group)}</span>`,
    String(E.modes[m]), pct(E.modes[m] / n),
    `<span class="meter" style="width:${(E.modes[m] / n * 130).toFixed(0)}px;background:${G[E.mode_defs[m].group] || 'var(--dim2)'}"></span>`,
    `<span class="tag">${esc(E.mode_defs[m].desc)}</span>`]))}

${sec('AUTOMATION RATE BY TASK', '这一栏是 AEI 最有信息量的一刀：不是你整体自动化了多少，是<b>哪类活已经能交出去</b>。')}
${(() => {
  const rows = E.by_task.filter(r => r.automation != null);
  return table([{ t: '任务' }, { t: '会话', r: true }, { t: '自动化率', r: true }, { t: '' },
    { t: '模式构成' }, { t: '主要能力' }],
    rows.map(r => [
      `<span class="lnk" data-topic="${esc(r.task)}" style="color:${topicColor(r.task)}">${esc(r.task)}</span>`,
      String(r.n), `<b>${pct(r.automation)}</b>`,
      `<span class="meter" style="width:${(r.automation * 120).toFixed(0)}px"></span>`,
      Object.entries(r.modes).sort((a, b) => b[1] - a[1]).slice(0, 3)
        .map(([k, v]) => `<span class="tag">${esc(k)} ${v}</span>`).join(''),
      Object.keys(r.skills).slice(0, 3).map(s => `<span class="tag">${esc(s)}</span>`).join('')]));
})()}
${(() => {
  const rows = E.by_task.filter(r => r.automation != null).sort((a, b) => a.automation - b.automation);
  const low = rows.slice(0, 3), high = rows.slice(-3).reverse();
  return warn(`<b>最能交出去的：</b>${high.map(r => `${esc(r.task)} ${pct(r.automation)}`).join('、')}。
    <b>最离不开你的：</b>${low.map(r => `${esc(r.task)} ${pct(r.automation)}`).join('、')}。<br>
    这两行放一起看：离不开你的那几类，要么是别人没法替你做的价值所在，要么是还没被固化下来的负债 ——
    哪一种，只有你自己知道。这一页不替你判断。`);
})()}

${sec('SKILLS', esc(E.skills_note))}
${table([{ t: '能力' }, { t: '调用次数', r: true }, { t: '占比', r: true }, { t: '' }],
  E.skills.map(s => [`<b>${esc(s.skill)}</b>`, fmt(s.n), pct(s.share),
    meter(s.n, Math.max(1, ...E.skills.map(x => x.n)), 140)]))}

${sec('MODE MIX OVER TIME', '每周五种模式的构成。看的是结构迁移。')}
<canvas class="viz" id="mix" height="220"></canvas>
<p class="hint">${modeOrder.filter(m => E.modes[m]).map(m =>
  `<span class="tag">■ ${esc(m)}</span>`).join('')}　自动化系＝绿，增强系＝蓝</p>

${sec('DEPTH vs BREADTH', '广＝这个项目碰过多少类活；深＝每类活平均开了多少场。广而浅 = 到处试；窄而深 = 死磕一件事。')}
${table([{ t: '项目' }, { t: '会话', r: true }, { t: '广', r: true }, { t: '深', r: true }, { t: '碰过的类别' }],
  E.depth_breadth.map(r => [esc(r.project), String(r.sessions), String(r.breadth), r.depth.toFixed(1),
    r.topics.slice(0, 6).map(t => `<span class="tag">${esc(t)}</span>`).join('')]))}`;

  const MODE_COL = { '指派': '#3ddc9a', '反馈环': '#1e9e73', '迭代': '#4da3ff', '学习': '#a78bfa', '校验': '#63d2ff', '未归类': '#4a5563' };
  const cv = host.querySelector('#mix');
  const draw = () => {
    const { ctx, w } = fitCanvas(cv, 220);
    const h = 220, padB = 22, padT = 6;
    ctx.clearRect(0, 0, w, h);
    const W = E.by_week.filter(x => x.n > 0);
    if (!W.length) return;
    const bw = w / W.length;
    W.forEach((wk, i) => {
      const tot = Object.values(wk.modes).reduce((a, b) => a + b, 0) || 1;
      let acc = 0;
      for (const m of modeOrder) {
        const v = wk.modes[m] || 0;
        if (!v) continue;
        const hh = (v / tot) * (h - padB - padT);
        ctx.fillStyle = MODE_COL[m];
        ctx.globalAlpha = S.mode === 'dark' ? .9 : .78;
        ctx.fillRect(i * bw, h - padB - acc - hh, Math.max(1, bw - 1), hh);
        acc += hh;
      }
    });
    ctx.globalAlpha = 1;
    ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--dim2');
    ctx.font = '10px ui-monospace, monospace';
    const step = Math.ceil(W.length / 11);
    W.forEach((wk, i) => { if (i % step === 0) ctx.fillText(wk.w.slice(2), i * bw, h - 7); });
  };
  draw();
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  enter('.sec, .kv > div, tbody tr', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
