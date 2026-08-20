import { esc, pct, topicColor, enter, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas } from '../../../core/g3d.js';
import { sec, bento, orbit, drawer, table, warn, pill, state } from '../kit.js';

export async function render(host) {
  const E = D.economics(), ser = D.topicSeries();
  const hum = Object.values(E.modes).reduce((a, b) => a + b, 0) || 1;
  const modeCol = { '自动化': 'var(--ok)', '协作': 'var(--acc)', '轻协作': 'var(--acc2)', '单问': 'var(--dim2)' };

  host.innerHTML = `
${sec('经济指数', '对标 Anthropic Economic Index 的问法，用你自己的数据回答。全部为确定性统计，运行期不调用任何模型。')}
${bento([
  { k: '自动化占比', v: pct((E.modes['自动化'] || 0) / hum), n: '一句话丢过去，机器自己干完一长串', w: 3, tone: 'acc' },
  { k: '协作占比', v: pct((E.modes['协作'] || 0) / hum), n: '来回打磨 5 次以上才出来的', w: 3, alt: true },
  { k: '主题集中度 HHI', v: E.hhi_topic_all == null ? '不确定' : E.hhi_topic_all.toFixed(3), n: '0 = 完全摊开，1 = 全压一件事' },
  { k: '项目集中度 HHI', v: E.hhi_project_all == null ? '不确定' : E.hhi_project_all.toFixed(3), n: '越高越集中' },
  { k: '真人会话', v: String(hum), n: '机器扇出与批处理已剔除' },
])}
<canvas class="viz" id="donut" height="240"></canvas>
${warn(`<b>这两个方向价值不同。</b>「自动化」高说明你已经能把活外包给机器；
  「协作」高说明那件事还没定型、每次都要陪着调。两者都不是坏事 ——
  但如果一件事做了几十次还停在协作，它就该被固化下来（见「沉淀」）。`)}

${sec('任务份额随时间', '每周你在各主题上的会话占比，堆到 100%。看的是结构迁移，不是绝对量。')}
<canvas class="viz" id="stream" height="300"></canvas>
<p class="hint">${ser.names.map(t => `<span class="pill" style="color:${topicColor(t)}">■ ${esc(t)}</span>`).join('')}</p>

${sec('注意力往哪挪了', '最近 30 天 vs 更早。正数 = 这段时间占比更高。')}
${(() => {
  const r30 = D.slice(30).topics, all = D.slice(0).topics;
  const rt = Object.values(r30).reduce((a, b) => a + b, 0) || 1;
  const at = Object.values(all).reduce((a, b) => a + b, 0) || 1;
  const rows = D.topicNames().map(t => {
    const r = (r30[t] || 0) / rt, o = ((all[t] || 0) - (r30[t] || 0)) / Math.max(1, at - rt);
    return { t, d: r - o, r, o };
  }).filter(x => x.r > 0 || x.o > 0).sort((a, b) => b.d - a.d);
  return orbit(rows.map(x => ({
    k: x.t, v: Math.abs(x.d) * 1000,
    label: `${x.d >= 0 ? '↑' : '↓'} ${(Math.abs(x.d) * 100).toFixed(1)}　(${pct(x.r)} ← ${pct(x.o)})`,
    c: x.d >= 0 ? 'var(--ok)' : 'var(--bad)',
  })));
})()}

${drawer('展开每周口径明细', table(
  [{ t: '周' }, { t: '会话', r: true }, { t: '主题 HHI', r: true }, { t: '项目 HHI', r: true },
   { t: '每轮工具数', r: true }, { t: '模式构成' }],
  E.weeks.slice().reverse().map(w => [w.w, String(w.n),
    w.hhi_topic == null ? state('不确定') : w.hhi_topic.toFixed(3),
    w.hhi_project == null ? state('不确定') : w.hhi_project.toFixed(3),
    w.tools_per_turn == null ? state('不确定') : w.tools_per_turn.toFixed(1),
    Object.entries(w.modes).sort((a, b) => b[1] - a[1]).map(([k, v]) => pill(`${k} ${v}`)).join('')])))}
${drawer('口径定义', table([{ t: '口径' }, { t: '定义' }],
  Object.entries(E.definition).map(([k, v]) => [`<b>${esc(k)}</b>`, esc(v)])))}`;

  const css = k => getComputedStyle(document.body).getPropertyValue(k).trim();
  const drawDonut = () => {
    const cv = host.querySelector('#donut');
    const { ctx, w } = fitCanvas(cv, 240);
    const h = 240;
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2, R = Math.max(20, Math.min(88, h / 2 - 32));
    const rows = Object.entries(E.modes).sort((a, b) => b[1] - a[1]);
    let a0 = -Math.PI / 2;
    ctx.lineWidth = 30; ctx.lineCap = 'butt';
    for (const [k, v] of rows) {
      const a1 = a0 + (v / hum) * 6.2832;
      const c = modeCol[k] || 'var(--dim2)';
      ctx.strokeStyle = css(c.replace(/var\(|\)/g, '')) || c;
      ctx.beginPath(); ctx.arc(cx, cy, R, a0, a1); ctx.stroke();
      const mid = (a0 + a1) / 2;
      if (v / hum > 0.06) {
        ctx.fillStyle = css('--fg'); ctx.textAlign = 'center';
        ctx.font = '600 12.5px -apple-system, system-ui, sans-serif';
        ctx.fillText(`${k} ${(v / hum * 100).toFixed(0)}%`,
          cx + Math.cos(mid) * (R + 34), cy + Math.sin(mid) * (R + 34) + 4);
      }
      a0 = a1;
    }
    ctx.textAlign = 'center'; ctx.fillStyle = css('--dim');
    ctx.font = '12px -apple-system, system-ui, sans-serif';
    ctx.fillText('真人会话', cx, cy - 6);
    ctx.fillStyle = css('--fg'); ctx.font = '700 24px -apple-system, system-ui, sans-serif';
    ctx.fillText(String(hum), cx, cy + 18);
    ctx.textAlign = 'left';
  };
  const drawStream = () => {
    const cv = host.querySelector('#stream');
    const { ctx, w } = fitCanvas(cv, 300);
    const h = 300, padB = 26, padT = 14;
    ctx.clearRect(0, 0, w, h);
    const W = ser.weeks;
    if (!W.length) return;
    // 流图：主题份额随周变化，用平滑面积而不是柱子 —— 星域不用直角图表
    const xs = i => 14 + (i / Math.max(1, W.length - 1)) * (w - 28);
    let base = W.map(() => h - padB);
    for (const t of ser.names) {
      const top = W.map((wk, i) => {
        const tot = Object.values(wk.count).reduce((a, b) => a + b, 0) || 1;
        return base[i] - ((wk.count[t] || 0) / tot) * (h - padB - padT);
      });
      ctx.beginPath();
      ctx.moveTo(xs(0), base[0]);
      for (let i = 0; i < W.length; i++) {
        const px = xs(i), py = top[i];
        if (i === 0) ctx.lineTo(px, py);
        else {
          const qx = xs(i - 1), qy = top[i - 1];
          ctx.bezierCurveTo((qx + px) / 2, qy, (qx + px) / 2, py, px, py);
        }
      }
      for (let i = W.length - 1; i >= 0; i--) ctx.lineTo(xs(i), base[i]);
      ctx.closePath();
      ctx.fillStyle = topicColor(t);
      ctx.globalAlpha = S.mode === 'dark' ? .82 : .7;
      ctx.fill();
      base = top;
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = css('--dim2'); ctx.font = '10.5px -apple-system, system-ui, sans-serif';
    const step = Math.ceil(W.length / 10);
    W.forEach((wk, i) => { if (i % step === 0) ctx.fillText(wk.w.slice(2), xs(i) - 12, h - 8); });
  };
  const drawAll = () => { drawDonut(); drawStream(); };
  drawAll();
  const onR = () => drawAll();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  enter('.sec, .card, .orow', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
