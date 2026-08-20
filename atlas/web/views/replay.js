import { S, esc, go, topicColor, local } from '../app.js';

// 历史回放：把 126 天按时间推一遍，看结构怎么长出来的。
export async function render(host) {
  const a = S.atlas, days = a.days;
  const byDay = new Map();
  for (const s of a.sessions) {
    if (!byDay.has(s.d)) byDay.set(s.d, []);
    byDay.get(s.d).push(s);
  }

  host.innerHTML = `
    <h2>回放</h2>
    <p class="sub">从 ${a.meta.first_day} 推到 ${a.meta.last_day}，一帧一天。点会一颗颗落下来，不会消失。</p>
    <div class="flexbar">
      <button class="act" id="play">▶ 播放</button>
      <button class="act" id="rewind">⟲ 从头</button>
      <input type="range" id="scrub" min="0" max="${days.length - 1}" value="${days.length - 1}" style="flex:1;min-width:220px">
      <select id="speed"><option value="60">快</option><option value="140" selected>中</option><option value="320">慢</option></select>
    </div>
    <canvas id="cv" height="420"></canvas>
    <div class="panel" id="stat"></div>`;

  const cv = host.querySelector('#cv'), ctx = cv.getContext('2d');
  const scrub = host.querySelector('#scrub'), stat = host.querySelector('#stat');
  const btn = host.querySelector('#play');
  let idx = days.length - 1, timer = null;

  const pos = [];
  days.forEach((d, di) => {
    for (const s of (byDay.get(d.d) || [])) {
      const lt = local(s.t);
      const hour = lt.getUTCHours() + lt.getUTCMinutes() / 60;
      pos.push({
        di, x: di / Math.max(1, days.length - 1), y: hour / 24,
        r: Math.min(7, 2 + Math.sqrt(Math.max(1, s.u)) * 1.1),
        c: s.tp[0] ? topicColor(s.tp[0]) : '#39434f', human: s.k === 'human',
      });
    }
  });

  function draw() {
    const w = cv.clientWidth; if (cv.width !== w) cv.width = w;
    const h = cv.height, pl = 44, pb = 24, pt = 10;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = '#171d24'; ctx.fillStyle = '#4a5563'; ctx.font = '11px system-ui';
    for (let hh = 0; hh <= 24; hh += 4) {
      const y = pt + (hh / 24) * (h - pt - pb);
      ctx.beginPath(); ctx.moveTo(pl, y); ctx.lineTo(w - 6, y); ctx.stroke();
      ctx.fillText(String(hh).padStart(2, '0') + ':00', 4, y + 4);
    }
    for (const p of pos) {
      if (p.di > idx) continue;
      const fade = p.di === idx ? 1 : (p.human ? 0.72 : 0.22);
      ctx.globalAlpha = fade;
      ctx.fillStyle = p.c;
      const x = pl + p.x * (w - pl - 8), y = pt + p.y * (h - pt - pb);
      ctx.beginPath(); ctx.arc(x, y, p.di === idx ? p.r + 1.6 : p.r, 0, 6.2832); ctx.fill();
    }
    ctx.globalAlpha = 1;
    const cx = pl + (idx / Math.max(1, days.length - 1)) * (cv.width - pl - 8);
    ctx.strokeStyle = '#5aa9ff'; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(cx, pt); ctx.lineTo(cx, h - pb); ctx.stroke();

    const d = days[idx];
    const upto = days.slice(0, idx + 1);
    const humanSum = upto.reduce((x, y) => x + y.human, 0);
    const top = Object.entries(d.topics).sort((x, y) => y[1] - x[1]).slice(0, 4);
    stat.innerHTML = `<div style="display:flex;gap:20px;flex-wrap:wrap;align-items:baseline">
        <button class="rowbtn" data-day="${d.d}" style="font-size:19px;font-weight:650">${d.d}</button>
        <span>这天你开口 <b>${d.human}</b> 场</span>
        <span class="muted">累计 ${humanSum} 场 · 第 ${idx + 1}/${days.length} 个有记录的日子</span>
        <span>${top.map(([t, n]) => `<span class="chip" style="border-color:${topicColor(t)}">${esc(t)} ${n}</span>`).join('') || '<span class="muted">未分类</span>'}</span>
      </div>`;
  }

  const stop = () => { if (timer) { clearInterval(timer); timer = null; } btn.textContent = '▶ 播放'; };
  btn.addEventListener('click', () => {
    if (timer) return stop();
    if (idx >= days.length - 1) idx = 0;
    btn.textContent = '⏸ 暂停';
    // 到头就停。绝不写没有终止条件的循环。
    timer = setInterval(() => {
      idx++;
      if (idx >= days.length - 1) { idx = days.length - 1; stop(); }
      scrub.value = idx; draw();
    }, +host.querySelector('#speed').value);
  });
  host.querySelector('#rewind').addEventListener('click', () => { stop(); idx = 0; scrub.value = 0; draw(); });
  scrub.addEventListener('input', () => { stop(); idx = +scrub.value; draw(); });
  host.querySelector('#speed').addEventListener('change', () => { if (timer) { stop(); btn.click(); } });
  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
  new MutationObserver((m, o) => {
    if (!document.body.contains(cv)) { stop(); o.disconnect(); }
  }).observe(document.getElementById('view'), { childList: true });
  draw();
}
