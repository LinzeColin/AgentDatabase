import { S, esc, fmt, go, topicColor } from '../app.js';

export async function render(host) {
  const a = S.atlas, W = a.trend.weeks.filter(w => w.human > 0);
  const topics = a.topic_names.filter(t => W.some(w => (w.count[t] || 0) > 0));

  host.innerHTML = `
    <h2>分析</h2>
    <p class="sub">口径固定：只统计你亲自开口的会话；一场最多挂 3 个主题；关键词按语料稀有度加权。</p>

    <h2>主题占比怎么变的</h2>
    <p class="sub">每一周你在各个主题上的会话占比。堆到 100%，看的是<b>结构</b>不是绝对量。</p>
    <div class="panel"><canvas id="area" height="300"></canvas>
      <div style="margin-top:10px">${topics.map(t =>
        `<span class="chip" style="border-color:${topicColor(t)};color:${topicColor(t)}">■ ${esc(t)}</span>`).join('')}</div></div>

    <h2>最近 30 天 vs 更早</h2>
    <p class="sub">正数＝这段时间占比更高。这是「你的注意力往哪边挪了」。</p>
    <div class="panel" id="drift"></div>

    <h2>各时间切片</h2>
    <div class="panel" id="slices"></div>

    <h2>项目</h2>
    <p class="sub">「上线过」＝这个项目下出现过「部署上线」类话题。没出现过不代表没上线，代表<b>没在对话里谈过</b>。</p>
    <div class="panel" id="proj"></div>

    <h2>Token</h2>
    <p class="sub">从会话记录里直接读到的用量。<b>口径统一为「不含缓存命中」</b> ——
      codex 的 <code>input_tokens</code> 含缓存、claude-code 的不含，不减掉就是把两种口径相加，
      单场能被抬到 24 亿这种量级。缓存读取单列，它便宜得多。</p>
    <div class="panel" id="tok"></div>`;

  drawArea(host.querySelector('#area'), W, topics);
  host.querySelector('#drift').innerHTML = drift(a);
  host.querySelector('#slices').innerHTML = slices(a);
  host.querySelector('#proj').innerHTML = projects(a);
  host.querySelector('#tok').innerHTML = tokens(a);
  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
}

function drawArea(cv, W, topics) {
  const ctx = cv.getContext('2d');
  const w = cv.clientWidth || 900; cv.width = w;
  const h = cv.height, padL = 8, padB = 26, padT = 8;
  ctx.clearRect(0, 0, w, h);
  if (!W.length) return;
  const bw = (w - padL * 2) / W.length;
  W.forEach((wk, i) => {
    const tot = Object.values(wk.count).reduce((x, y) => x + y, 0);
    let acc = 0;
    const x = padL + i * bw;
    if (!tot) return;
    for (const t of topics) {
      const v = wk.count[t] || 0;
      if (!v) continue;
      const hh = (v / tot) * (h - padB - padT);
      ctx.fillStyle = topicColor(t);
      ctx.fillRect(x, h - padB - acc - hh, Math.max(1, bw - 1), hh);
      acc += hh;
    }
  });
  ctx.fillStyle = '#5e6773'; ctx.font = '10px system-ui';
  W.forEach((wk, i) => {
    if (i % Math.ceil(W.length / 10) !== 0) return;
    ctx.fillText(wk.w.slice(2), padL + i * bw, h - 9);
  });
}

function drift(a) {
  const recent = a.slices['30'].topics, all = a.slices['0'].topics;
  const rt = Object.values(recent).reduce((x, y) => x + y, 0) || 1;
  const at = Object.values(all).reduce((x, y) => x + y, 0) || 1;
  const rows = a.topic_names.map(t => {
    const r = (recent[t] || 0) / rt, o = ((all[t] || 0) - (recent[t] || 0)) / Math.max(1, at - rt);
    return { t, r, o, d: r - o };
  }).filter(x => x.r > 0 || x.o > 0).sort((x, y) => y.d - x.d);
  const max = Math.max(0.001, ...rows.map(x => Math.abs(x.d)));
  return `<table><thead><tr><th>主题</th><th class="num">最近30天</th><th class="num">更早</th>
    <th class="num">变化</th><th style="width:34%"></th></tr></thead><tbody>
    ${rows.map(x => `<tr>
      <td><span class="chip" style="border-color:${topicColor(x.t)}">${esc(x.t)}</span></td>
      <td class="num">${(x.r * 100).toFixed(1)}%</td>
      <td class="num muted">${(x.o * 100).toFixed(1)}%</td>
      <td class="num" style="color:${x.d >= 0 ? 'var(--good)' : 'var(--bad)'}">
        ${x.d >= 0 ? '↑' : '↓'} ${(Math.abs(x.d) * 100).toFixed(1)}</td>
      <td><span class="bar" style="width:${(Math.abs(x.d) / max * 100).toFixed(0)}%;
        background:${x.d >= 0 ? 'var(--good)' : 'var(--bad)'}"></span></td></tr>`).join('')}
  </tbody></table>`;
}

function slices(a) {
  const keys = ['3', '7', '15', '30', '45', '60', '90', '180', '0'];
  return `<table><thead><tr><th>切片</th><th class="num">你开口</th><th class="num">机器</th>
    <th class="num">活跃天</th><th class="num">你说话次数</th><th class="num">未分类</th><th>最多的三个主题</th>
    </tr></thead><tbody>${keys.map(k => {
      const s = a.slices[k];
      const top = Object.entries(s.topics).sort((x, y) => y[1] - x[1]).slice(0, 3);
      return `<tr><td><b>${esc(s.label)}</b></td><td class="num">${s.human}</td>
        <td class="num muted">${s.auto}</td><td class="num">${s.days_active}</td>
        <td class="num">${s.turns}</td><td class="num muted">${s.unclassified}</td>
        <td>${top.map(([t, n]) => `<span class="chip" style="border-color:${topicColor(t)}">${esc(t)} ${n}</span>`).join('') || '<span class="muted">无</span>'}</td></tr>`;
    }).join('')}</tbody></table>`;
}

function projects(a) {
  const rows = a.projects.filter(p => p.human > 0).slice(0, 25);
  const max = Math.max(1, ...rows.map(p => p.active_hours));
  return `<table><thead><tr><th>项目</th><th class="num">你开口</th><th class="num">钟点</th>
    <th class="num">token 入</th><th>上线过</th><th>起止</th><th style="width:20%"></th></tr></thead><tbody>
    ${rows.map(p => `<tr><td>${esc(p.name)}</td><td class="num">${p.human}</td>
      <td class="num">${p.active_hours}</td><td class="num muted">${fmt(p.tok_in)}</td>
      <td><span class="state" data-s="${p.shipped ? '通' : '没做'}">${p.shipped ? '谈过上线' : '没谈过'}</span></td>
      <td class="muted" style="font-size:12px">${p.first.slice(5)} → ${p.last.slice(5)}</td>
      <td><span class="bar" style="width:${(p.active_hours / max * 100).toFixed(0)}%"></span></td></tr>`).join('')}
  </tbody></table>`;
}

function tokens(a) {
  const s = a.slices['0'];
  const rows = a.projects.filter(p => p.tok_in > 0).slice(0, 12);
  return `<div class="cards">
      <div class="card"><div class="k">输入（不含缓存）</div><div class="v">${fmt(s.tok_in)}</div></div>
      <div class="card"><div class="k">输出</div><div class="v">${fmt(s.tok_out)}</div></div>
      <div class="card"><div class="k">每场平均输出</div><div class="v">${fmt(Math.round(s.tok_out / Math.max(1, s.sessions)))}</div></div>
    </div>
    <table><thead><tr><th>项目</th><th class="num">token 入</th><th class="num">token 出</th></tr></thead><tbody>
    ${rows.map(p => `<tr><td>${esc(p.name)}</td><td class="num">${fmt(p.tok_in)}</td>
      <td class="num muted">${fmt(p.tok_out)}</td></tr>`).join('')}</tbody></table>
    <div class="note">费用<b>不估算</b>。不同模型、不同缓存命中、不同套餐的单价都不一样，
      拿不到真实账单就标「不确定」，不拿一个编出来的数字给你看。</div>`;
}
