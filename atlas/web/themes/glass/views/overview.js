import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, loop } from '../../../core/g3d.js';
import { sec, bento, orbit, drawer, table, warn, pill, state, rate } from '../kit.js';

export async function render(host) {
  const m = D.meta(), all = D.slice(0), d7 = D.slice(7), d30 = D.slice(30);
  const L = all.ladder, tk = D.tokens().total;
  const money = Math.max(1, L['换钱'] || 0);

  host.innerHTML = `
${sec('你的三个月', '全部数字从本机会话记录直接数出来，运行期不调用任何模型。')}
${bento([
  { k: '你亲自开口的会话', v: `<span data-cnt="${m.sessions_human}">0</span>`, n: `另有 ${m.sessions_auto} 场是机器`, w: 3, tone: 'acc' },
  { k: '建设 : 交付 : 换钱', v: `${Math.floor((L['建设'] || 0) / money)}:${Math.floor((L['交付'] || 0) / money)}:1`,
    n: `${L['建设'] || 0} / ${L['交付'] || 0} / ${L['换钱'] || 0}`, w: 3, tone: 'warn', alt: true },
  { k: '有记录的日子', v: `<span data-cnt="${m.days_active}">0</span>`, n: `${m.first_day} 起` },
  { k: '最近 7 天', v: String(d7.human), n: `活跃 ${d7.days_active} 天` },
  { k: '最近 30 天', v: String(d30.human), n: `活跃 ${d30.days_active} 天` },
  { k: '缓存命中率', v: rate(tk.hit_rate), n: `输入 ${fmt(tk.input_total)}（含缓存）`, tone: 'acc' },
  { k: '未分类', v: String(all.unclassified), n: '这些会话里没出现能判断的词，就先空着' },
  { k: '没有用量数据数据', v: String(D.tokens().no_usage), n: '这类记录里没有 token 字段，所以写「说不准」而不是 0' },
])}

${warn(`<b>${m.sessions_total} 场里有 ${m.sessions_auto} 场不是你在对话。</b>
  ${m.sessions_fanout} 场是 机器在一小时内一次性铺开了大批任务（最大一次 ${esc((m.fanout_hours[0] || {}).when || '—')}），
  其余是批处理与单轮机器指令。本页全部口径已剔除它们 —— 剔掉多少写在这里，不会悄悄算进总数。`)}

${sec('时间去哪了', '只统计你亲自开口的会话；一场最多挂 3 个主题。点任一条进网格。')}
${orbit(Object.entries(all.topics).sort((a, b) => b[1] - a[1]).map(([t, n]) => ({
  k: t, v: n, c: topicColor(t), attr: `data-topic="${esc(t)}"`,
})).concat([{ k: '未分类', v: all.unclassified, c: 'var(--dim2)' }]))}

${sec('三档', '把上面的主题归并出来的，不是另外算的。')}
<canvas class="viz" id="ladder" height="150"></canvas>
<p class="hint">${['建设', '交付', '换钱', '学习'].filter(k => k in L).map(k =>
  `${pill(`${k} ${L[k]} · ${pct(L[k] / Object.values(L).reduce((a, b) => a + b, 0))}`)}`).join('')}</p>

${sec('数出来的几件事')}
${bento(D.insights().map((i, idx, arr) => ({
  kHtml: `${state(i.t === 'warn' ? '说不准' : '看这里')}　${esc(i.k)}`, k: i.k,
  v: `${esc(i.v)}`, size: 'sm', n: esc(i.d),
  w: idx === arr.length - 1 && arr.length % 2 ? 6 : 3,   // 末张单数时占满，别留孤儿
})))}

${sec('方向与口子', esc((D.opportunities() || {}).caveat || ''))}
${((D.opportunities() || {}).items || []).map(o => `
  <div class="card w6" style="margin:14px 0">
    <div class="ck">${esc(o.k)}　<span style="color:var(--dim2)">来源：${esc(o.from)}</span></div>
    <div class="cv acc md">${esc(o.v)}</div>
    <div class="cn" style="margin:6px 0 12px">${esc(o.d)}</div>
    ${(o.list || []).map(x => pill(x)).join('')}
  </div>`).join('')}
`;

  host.querySelectorAll('[data-cnt]').forEach(el => countUp(el, +el.dataset.cnt));
  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]');
    if (t) go('grid', 't=' + encodeURIComponent(t.dataset.topic));
  });

  // 三档画成一条分段弧，不是柱状图 —— 琉璃主题不用直角图表
  const cv = host.querySelector('#ladder');
  const draw = () => {
    const { ctx, w } = fitCanvas(cv, 150);
    const h = 150;
    ctx.clearRect(0, 0, w, h);
    const order = ['建设', '交付', '换钱', '学习'].filter(k => k in L);
    const tot = order.reduce((a, k) => a + L[k], 0) || 1;
    const cx = w / 2, cy = h - 12, R = Math.max(24, Math.min(w / 2 - 30, 118));
    const cols = { '建设': 'var(--dim2)', '交付': 'var(--acc)', '换钱': 'var(--ok)', '学习': 'var(--acc2)' };
    let a0 = Math.PI;
    ctx.lineCap = 'butt';
    for (const k of order) {
      const a1 = a0 + (L[k] / tot) * Math.PI;
      ctx.strokeStyle = getComputedStyle(document.body).getPropertyValue(cols[k].replace(/var\(|\)/g, '')) || cols[k];
      ctx.lineWidth = 26;
      ctx.beginPath(); ctx.arc(cx, cy, R, a0, a1); ctx.stroke();
      const mid = (a0 + a1) / 2;
      if ((L[k] / tot) > 0.05) {
        ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--fg');
        ctx.font = '600 12px -apple-system, system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(k, cx + Math.cos(mid) * (R + 22), cy + Math.sin(mid) * (R + 22) + 4);
      }
      a0 = a1;
    }
    ctx.textAlign = 'left';
  };
  draw();
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  enter('.sec, .card, .orow', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
