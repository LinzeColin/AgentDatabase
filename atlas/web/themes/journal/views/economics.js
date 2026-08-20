import { esc, pct, topicColor, enter, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas } from '../../../core/g3d.js';
import { sec, lede, p, n, big, aside, note, figure, rank, spark, table, state } from '../kit.js';

export async function render(host) {
  const E = D.economics(), ser = D.topicSeries();
  const hum = Object.values(E.modes).reduce((a, b) => a + b, 0) || 1;
  const g = k => E.modes[k] || 0;

  host.innerHTML = `
${sec('经济指数')}
${lede(`Anthropic 的 Economic Index 问三件事：这项工作是被<b>自动化</b>了还是被<b>协作</b>放大了、
  任务份额随时间怎么迁移、注意力有多集中。把同样三个问题放到你自己的记录上，答案是这样的。`)}
${aside('全部为确定性统计。运行期不调用任何模型 —— 这里不会有一句「我猜你应该……」。')}

${p(`你 ${n(hum)} 场真人会话里，${big(pct(g('自动化') / hum))} 是<b>自动化</b>：
  你只说了一次，机器却调用了八次以上工具，一句话丢过去它自己干完。
  ${big(pct(g('协作') / hum))} 是<b>协作</b>：来回打磨五次以上才出来。
  剩下的是轻协作 ${n(g('轻协作'))} 场与单问 ${n(g('单问'))} 场。`)}
${note(`<b>这两个方向价值不同。</b>「自动化」高说明你已经能把活外包给机器；
  「协作」高说明那件事还没定型、每次都要陪着调。两者都不是坏事 ——
  但一件事做了几十次还停在协作，它就该被固化下来。`)}
${figure(rank(Object.entries(E.modes).sort((a, b) => b[1] - a[1]).map(([k, v]) =>
  ({ k, v, label: `${v}　${pct(v / hum)}` }))), '四种工作模式的构成。按行为分，不按主题分。')}

${sec('任务份额随时间')}
${p(`每一周你在各个主题上的会话占比，堆到一百。看的是<b>结构</b>怎么迁移的，不是绝对量。`)}
${figure('<canvas class="viz" id="area" height="250"></canvas>',
  ser.names.map(t => `<span class="kw" style="color:${topicColor(t)}">■ ${esc(t)}</span>`).join(''))}

${sec('集中度')}
${p(`赫芬达尔指数：零是精力完全摊开，一是全压在一件事上。
  你的主题集中度是 ${big(E.hhi_topic_all == null ? '不确定' : E.hhi_topic_all.toFixed(3))}，
  项目集中度是 ${big(E.hhi_project_all == null ? '不确定' : E.hhi_project_all.toFixed(3))}。
  逐周的起伏：${spark(E.weeks.map(w => (w.hhi_topic || 0) * 1000))}`)}
${figure(table([{ t: '周' }, { t: '会话', r: true }, { t: '主题 HHI', r: true }, { t: '项目 HHI', r: true }, { t: '每轮工具数', r: true }],
  E.weeks.slice().reverse().map(w => [w.w, String(w.n),
    w.hhi_topic == null ? state('不确定') : w.hhi_topic.toFixed(3),
    w.hhi_project == null ? state('不确定') : w.hhi_project.toFixed(3),
    w.tools_per_turn == null ? state('不确定') : w.tools_per_turn.toFixed(1)])),
  '每轮工具数 = 工具调用次数 ÷ 你说话次数，衡量一句话能撬动多少活。')}

${sec('注意力往哪挪了')}
${(() => {
  const r30 = D.slice(30).topics, all = D.slice(0).topics;
  const rt = Object.values(r30).reduce((a, b) => a + b, 0) || 1;
  const at = Object.values(all).reduce((a, b) => a + b, 0) || 1;
  const rows = D.topicNames().map(t => {
    const r = (r30[t] || 0) / rt, o = ((all[t] || 0) - (r30[t] || 0)) / Math.max(1, at - rt);
    return { t, d: r - o, r, o };
  }).filter(x => x.r > 0 || x.o > 0).sort((a, b) => b.d - a.d);
  const up = rows.filter(x => x.d > 0).slice(0, 3), down = rows.filter(x => x.d < 0).slice(-3).reverse();
  return p(`最近三十天里，占比上升最多的是
    ${up.map(x => `<b>${esc(x.t)}</b>（${pct(x.r)}，此前 ${pct(x.o)}）`).join('、')}；
    下降最多的是 ${down.map(x => `<b>${esc(x.t)}</b>（${pct(x.r)}，此前 ${pct(x.o)}）`).join('、')}。`)
    + figure(rank(rows.map(x => ({ k: x.t, v: Math.abs(x.d) * 1000,
      label: `${x.d >= 0 ? '↑' : '↓'} ${(Math.abs(x.d) * 100).toFixed(1)}` }))), '全部主题的占比变化。');
})()}`;

  const draw = () => {
    const cv = host.querySelector('#area');
    if (!cv) return;
    const { ctx, w } = fitCanvas(cv, 250);
    const h = 250, padB = 22, padT = 6;
    ctx.clearRect(0, 0, w, h);
    const W = ser.weeks;
    if (!W.length) return;
    const bw = w / W.length;
    W.forEach((wk, i) => {
      const tot = Object.values(wk.count).reduce((a, b) => a + b, 0);
      if (!tot) return;
      let acc = 0;
      for (const t of ser.names) {
        const v = wk.count[t] || 0;
        if (!v) continue;
        const hh = (v / tot) * (h - padB - padT);
        ctx.fillStyle = topicColor(t);
        ctx.globalAlpha = S.mode === 'dark' ? .8 : .62;
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
  enter('.sec, p.body, figure, .aside', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
