import { esc, fmt, pct, topicColor, enter, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, loop } from '../../../core/g3d.js';
import { sec, kv, table, meter, spark, warn, state } from '../kit.js';

// 对标 Anthropic Economic Index 的三个问法，换成 Owner 自己的数据能回答的形式：
//   1) 自动化 vs 协作  2) 任务份额随时间迁移  3) 集中度
export async function render(host) {
  const E = D.economics(), ser = D.topicSeries();
  const hum = Object.values(E.modes).reduce((a, b) => a + b, 0) || 1;

  host.innerHTML = `
${sec('ECONOMIC INDEX', '对标 Anthropic Economic Index 的问法，用你自己的数据回答。全部为确定性统计。')}
${table([{ t: '口径' }, { t: '定义' }], Object.entries(E.definition).map(([k, v]) =>
  [`<b style="color:var(--fg)">${esc(k)}</b>`, `<span class="tag">${esc(v)}</span>`]))}

${sec('AUTOMATION vs COLLABORATION', '按行为分，不按主题分：一句话丢过去让它干完，还是来回打磨。')}
${kv(Object.entries(E.modes).sort((a, b) => b[1] - a[1]).map(([k, v]) =>
  [k, `${v} 场 · ${pct(v / hum)}`, k === '自动化' ? 'acc' : k === '协作' ? 'warn' : '']))}
${table([{ t: '模式' }, { t: '会话', r: true }, { t: '占比', r: true }, { t: '' }, { t: '按周' }],
  Object.entries(E.modes).sort((a, b) => b[1] - a[1]).map(([k, v]) => [
    k, String(v), pct(v / hum), meter(v, Math.max(...Object.values(E.modes)), 120),
    spark(E.weeks.map(w => w.modes[k] || 0))]))}
${warn(`<b>这两个方向价值不同。</b>「自动化」高说明你已经能把活外包给机器；
  「协作」高说明那件事还没定型、每次都要陪着调。两者都不是坏事 ——
  但如果一件事做了几十次还停在协作，它就该被固化下来（见「沉淀」页）。`)}

${sec('TASK SHARE OVER TIME', '每周你在各主题上的会话占比，堆到 100%。看的是结构迁移，不是绝对量。')}
<canvas class="viz" id="area" height="260"></canvas>
<p class="hint">${ser.names.map(t =>
  `<span class="tag" style="color:${topicColor(t)}">■ ${esc(t)}</span>`).join('')}</p>

${sec('CONCENTRATION', '赫芬达尔指数 HHI：0 = 精力完全摊开，1 = 全压在一件事上。')}
${kv([
  ['主题集中度（全历史）', E.hhi_topic_all == null ? '不确定' : E.hhi_topic_all.toFixed(3), 'acc'],
  ['项目集中度（全历史）', E.hhi_project_all == null ? '不确定' : E.hhi_project_all.toFixed(3), 'acc'],
])}
${table([{ t: '周' }, { t: '会话', r: true }, { t: '主题 HHI', r: true }, { t: '项目 HHI', r: true },
         { t: '每轮工具数', r: true }, { t: '模式构成' }],
  E.weeks.slice().reverse().map(w => [
    w.w, String(w.n),
    w.hhi_topic == null ? '<span class="st" data-s="不确定">—</span>' : w.hhi_topic.toFixed(3),
    w.hhi_project == null ? '<span class="st" data-s="不确定">—</span>' : w.hhi_project.toFixed(3),
    w.tools_per_turn == null ? '<span class="st" data-s="不确定">—</span>' : w.tools_per_turn.toFixed(1),
    Object.entries(w.modes).sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `<span class="tag">${esc(k)} ${v}</span>`).join('')]))}

${sec('DRIFT', '最近 30 天 vs 更早。正数 = 这段时间占比更高，也就是注意力往哪边挪了。')}
${(() => {
  const r30 = D.slice(30).topics, all = D.slice(0).topics;
  const rt = Object.values(r30).reduce((a, b) => a + b, 0) || 1;
  const at = Object.values(all).reduce((a, b) => a + b, 0) || 1;
  const rows = D.topicNames().map(t => {
    const r = (r30[t] || 0) / rt, o = ((all[t] || 0) - (r30[t] || 0)) / Math.max(1, at - rt);
    return { t, r, o, d: r - o };
  }).filter(x => x.r > 0 || x.o > 0).sort((a, b) => b.d - a.d);
  const mx = Math.max(0.001, ...rows.map(x => Math.abs(x.d)));
  return table([{ t: '主题' }, { t: '最近30天', r: true }, { t: '更早', r: true }, { t: '变化', r: true }, { t: '' }],
    rows.map(x => [esc(x.t), pct(x.r), pct(x.o),
      `<span style="color:${x.d >= 0 ? 'var(--ok)' : 'var(--bad)'}">${x.d >= 0 ? '↑' : '↓'}${(Math.abs(x.d) * 100).toFixed(1)}</span>`,
      `<span class="meter" style="width:${(Math.abs(x.d) / mx * 110).toFixed(0)}px;background:${x.d >= 0 ? 'var(--ok)' : 'var(--bad)'}"></span>`]));
})()}
`;

  const cv = host.querySelector('#area');
  const drawArea = () => {
    const { ctx, w, h } = fitCanvas(cv, 260);
    const W = ser.weeks;
    ctx.clearRect(0, 0, w, h);
    if (!W.length) return;
    const padB = 22, padT = 6, bw = w / W.length;
    W.forEach((wk, i) => {
      const tot = Object.values(wk.count).reduce((a, b) => a + b, 0);
      if (!tot) return;
      let acc = 0;
      for (const t of ser.names) {
        const v = wk.count[t] || 0;
        if (!v) continue;
        const hh = (v / tot) * (h - padB - padT);
        ctx.fillStyle = topicColor(t);
        ctx.globalAlpha = S.mode === 'dark' ? .88 : .78;
        ctx.fillRect(i * bw, h - padB - acc - hh, Math.max(1, bw - 1), hh);
        acc += hh;
      }
    });
    ctx.globalAlpha = 1;
    ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--dim2');
    ctx.font = '10px ui-monospace, monospace';
    const step = Math.ceil(W.length / 12);
    W.forEach((wk, i) => { if (i % step === 0) ctx.fillText(wk.w.slice(2), i * bw + 1, h - 7); });
  };
  drawArea();
  const onResize = () => drawArea();
  addEventListener('resize', onResize);
  addEventListener('atlas:theme', onResize);
  enter('.sec, .kv > div, tbody tr', host);
  return { dispose() { removeEventListener('resize', onResize); removeEventListener('atlas:theme', onResize); } };
}
