import { esc, pct, fmt, go, enter, topicColor, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas } from '../../../core/g3d.js';
import { sec, lede, p, n, big, aside, note, figure, rank, spark, table, state } from '../kit.js';

export async function render(host) {
  const E = D.A().aei, N = E.sessions_total;
  const order = ['指派', '反馈环', '迭代', '学习', '校验', '未归类'];
  const rows = E.by_task.filter(r => r.automation != null).sort((a, b) => a.automation - b.automation);
  const low = rows.slice(0, 3), high = rows.slice(-3).reverse();

  host.innerHTML = `
${sec('经济指数')}
${lede(`Anthropic 的 Economic Index 把人与模型的协作分成五种：<b>指派</b>与<b>反馈环</b>属于自动化，
  <b>迭代</b>、<b>学习</b>、<b>校验</b>属于增强。按这套分法数你的 ${n(N)} 场会话，
  自动化占 ${big(pct(E.headline.automation))}，增强占 ${big(pct(E.headline.augmentation))}。`)}
${aside(esc(E.framework))}
${figure(rank(order.filter(m => E.modes[m]).map(m => ({ k: m, v: E.modes[m],
  label: `${E.modes[m]}　${pct(E.modes[m] / N)}` }))), '五种模式的分布。')}
${figure(table([{ t: '模式' }, { t: '归属' }, { t: '判据' }],
  order.filter(m => E.modes[m]).map(m => [`<b>${esc(m)}</b>`, esc(E.mode_defs[m].group), esc(E.mode_defs[m].desc)])),
  '判据写在这里，不用猜。')}

${sec('哪类活已经能交出去')}
${lede(`AEI 最有信息量的一刀不是「你整体自动化了多少」，而是<b>每一类活各自</b>自动化了多少。
  最能交出去的是 ${high.map(r => `<b>${esc(r.task)}</b>（${pct(r.automation)}）`).join('、')}；
  最离不开你的是 ${low.map(r => `<b>${esc(r.task)}</b>（${pct(r.automation)}）`).join('、')}。`)}
${note(`离不开你的那几类，要么是别人替不了的价值所在，要么是还没被固化下来的负债 ——
  哪一种，只有你自己知道。这一页不替你判断。`)}
${figure(rank(E.by_task.filter(r => r.automation != null).map(r => ({
  k: r.task, v: r.automation, label: `${pct(r.automation)}　${r.n} 场`,
  attr: `data-topic="${esc(r.task)}"` }))), '按自动化率排。')}

${sec('用到了哪些能力')}
${p(esc(E.skills_note))}
${figure(rank(E.skills.map(s => ({ k: s.skill, v: s.n, label: `${fmt(s.n)}　${pct(s.share)}` }))), '工具调用作为能力的可观测代理。')}

${sec('模式构成随时间')}
${figure('<canvas class="viz" id="mix" height="230"></canvas>',
  order.filter(m => E.modes[m]).map(m => `<span class="kw">■ ${esc(m)}</span>`).join(''))}

${sec('深度与广度')}
${p(`广＝这个项目碰过多少类活，深＝每类活平均开了多少场。广而浅是到处试，窄而深是死磕一件事。`)}
${figure(table([{ t: '项目' }, { t: '会话', r: true }, { t: '广', r: true }, { t: '深', r: true }, { t: '类别' }],
  E.depth_breadth.map(r => [esc(r.project), String(r.sessions), String(r.breadth), r.depth.toFixed(1),
    r.topics.slice(0, 6).map(t => `<span class="kw">${esc(t)}</span>`).join('')])),
  `集中度 HHI：任务 ${E.concentration.task_hhi ?? '不确定'}，项目 ${E.concentration.project_hhi ?? '不确定'}。0 是完全摊开，1 是全压在一件事上。`)}`;

  const MODE_COL = { '指派': '#3f6b48', '反馈环': '#6b8f5a', '迭代': '#a2423a', '学习': '#7a6a4f', '校验': '#9a6212', '未归类': '#b6ada0' };
  const draw = () => {
    const cv = host.querySelector('#mix'); if (!cv) return;
    const { ctx, w } = fitCanvas(cv, 230);
    const h = 230, padB = 22, padT = 6;
    ctx.clearRect(0, 0, w, h);
    const W = E.by_week.filter(x => x.n > 0);
    if (!W.length) return;
    const bw = w / W.length;
    W.forEach((wk, i) => {
      const tot = Object.values(wk.modes).reduce((a, b) => a + b, 0) || 1;
      let acc = 0;
      for (const m of order) {
        const v = wk.modes[m] || 0; if (!v) continue;
        const hh = (v / tot) * (h - padB - padT);
        ctx.fillStyle = MODE_COL[m];
        ctx.globalAlpha = S.mode === 'dark' ? .82 : .68;
        ctx.fillRect(i * bw, h - padB - acc - hh, Math.max(1, bw - 1.5), hh);
        acc += hh;
      }
    });
    ctx.globalAlpha = 1;
    ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--dim2');
    ctx.font = '10px -apple-system, system-ui, sans-serif';
    const step = Math.ceil(W.length / 10);
    W.forEach((wk, i) => { if (i % step === 0) ctx.fillText(wk.w.slice(2), i * bw, h - 7); });
  };
  draw();
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });
  enter('.sec, p.body, figure, .aside', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
