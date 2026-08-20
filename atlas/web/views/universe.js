import { S, esc, go, topicColor, local } from '../app.js';

// 手写的 3D：CSP 是 script-src 'self'，装不了 three.js，也不该为了画点装一个库。
// 结构：离圆心越远＝越近的日子；转一圈＝一天 24 小时；高度＝主题层。
export async function render(host) {
  const a = S.atlas;
  const days = a.days.map(d => d.d);
  const dayIdx = new Map(days.map((d, i) => [d, i]));
  const topics = a.topic_names;
  const tIdx = new Map(topics.map((t, i) => [t, i]));

  host.innerHTML = `
    <h2>宇宙</h2>
    <p class="sub">一个点＝一场会话。<b>离圆心越远＝日子越近</b>，<b>绕一圈＝一天 24 小时</b>，
      <b>上下分层＝主题</b>。拖动转视角，滚轮缩放，点一个点进那一天。</p>
    <div class="flexbar">
      <label class="muted" style="font-size:12.5px"><input type="checkbox" id="mach"> 把机器扇出也画出来</label>
      <label class="muted" style="font-size:12.5px"><input type="checkbox" id="spin" checked> 自动旋转</label>
      <button class="act" id="reset">回到初始视角</button>
      <span class="muted" id="hint" style="font-size:12.5px"></span>
    </div>
    <canvas id="cv" height="620"></canvas>
    <div class="panel" id="legend"></div>
    <div class="note"><b>为什么不用颜色分状态？</b>颜色只是辅助 —— 每个主题在下面都有名字和数量，
      色盲或屏幕偏色时靠文字也读得出来。</div>`;

  host.querySelector('#legend').innerHTML = topics.map(t => {
    const n = (a.slices['0'].topics[t] || 0);
    return `<span class="chip" style="border-color:${topicColor(t)};color:${topicColor(t)}">■ ${esc(t)} ${n}</span>`;
  }).join('') + `<span class="chip" style="border-color:#3a444f;color:#6b7684">■ 未分类 ${a.slices['0'].unclassified}</span>`;

  const cv = host.querySelector('#cv');
  const ctx = cv.getContext('2d');
  const hint = host.querySelector('#hint');
  const cbMach = host.querySelector('#mach'), cbSpin = host.querySelector('#spin');

  let pts = [];
  function rebuild() {
    const showMach = cbMach.checked;
    pts = [];
    for (const s of a.sessions) {
      if (!showMach && s.k !== 'human') continue;
      const di = dayIdx.get(s.d);
      if (di == null) continue;
      const t = days.length > 1 ? di / (days.length - 1) : 1;
      const lt = local(s.t);
      const hour = lt.getUTCHours() + lt.getUTCMinutes() / 60;
      const ang = hour / 24 * Math.PI * 2;
      const R = 50 + t * 300;
      const top = s.tp[0] || null;
      const layer = top ? (tIdx.get(top) - topics.length / 2) : 0;
      pts.push({
        x: Math.cos(ang) * R, z: Math.sin(ang) * R, y: layer * 11,
        r: Math.min(6.5, 1.5 + Math.sqrt(Math.max(1, s.u)) * 0.9),
        c: top ? topicColor(top) : '#4a5563',
        human: s.k === 'human', d: s.d, n: s.n, tp: s.tp, u: s.u, p: s.p, src: s.s,
      });
    }
    hint.textContent = `${pts.length} 个点`;
  }
  rebuild();
  cbMach.addEventListener('change', rebuild);

  let yaw = -0.6, pitch = 0.78, zoom = 1.25, spin = true;
  const F = 620;
  cbSpin.addEventListener('change', () => { spin = cbSpin.checked; });
  host.querySelector('#reset').addEventListener('click', () => {
    yaw = -0.6; pitch = 0.78; zoom = 1.25;
  });

  function project(p, cx, cy) {
    const cy_ = Math.cos(yaw), sy_ = Math.sin(yaw);
    const x1 = p.x * cy_ - p.z * sy_;
    const z1 = p.x * sy_ + p.z * cy_;
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    const y1 = p.y * cp - z1 * sp;
    const z2 = p.y * sp + z1 * cp;
    const k = F / (F + z2 + 420);
    return { sx: cx + x1 * k * zoom, sy: cy + y1 * k * zoom, k, z: z2 };
  }

  let hover = null, mouse = { x: -1, y: -1 };
  function draw() {
    const w = cv.clientWidth, h = cv.height;
    if (cv.width !== w) cv.width = w;
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2;

    // 底盘：24 条时刻辐条 + 若干同心圈，给点位一个可读的坐标系
    ctx.strokeStyle = '#171d24'; ctx.lineWidth = 1;
    for (let hh = 0; hh < 24; hh += 3) {
      const ang = hh / 24 * Math.PI * 2;
      const A = project({ x: Math.cos(ang) * 50, z: Math.sin(ang) * 50, y: 0 }, cx, cy);
      const B = project({ x: Math.cos(ang) * 345, z: Math.sin(ang) * 345, y: 0 }, cx, cy);
      ctx.beginPath(); ctx.moveTo(A.sx, A.sy); ctx.lineTo(B.sx, B.sy); ctx.stroke();
      ctx.fillStyle = '#39434f'; ctx.font = '11px system-ui';
      ctx.fillText(String(hh).padStart(2, '0') + ':00', B.sx + 3, B.sy);
    }
    for (const R of [110, 200, 290]) {
      ctx.beginPath();
      for (let i = 0; i <= 72; i++) {
        const ang = i / 72 * Math.PI * 2;
        const P = project({ x: Math.cos(ang) * R, z: Math.sin(ang) * R, y: 0 }, cx, cy);
        i ? ctx.lineTo(P.sx, P.sy) : ctx.moveTo(P.sx, P.sy);
      }
      ctx.stroke();
    }

    const proj = pts.map(p => ({ p, ...project(p, cx, cy) }));
    proj.sort((a, b) => b.z - a.z);   // 远的先画，近的盖住远的
    hover = null;
    let best = 13;
    for (const q of proj) {
      const rr = Math.max(1, q.p.r * q.k * zoom);
      const d = Math.hypot(q.sx - mouse.x, q.sy - mouse.y);
      if (d < best) { best = d; hover = q; }
      ctx.globalAlpha = q.p.human ? 0.92 : 0.3;
      ctx.fillStyle = q.p.c;
      ctx.beginPath(); ctx.arc(q.sx, q.sy, rr, 0, 6.2832); ctx.fill();
    }
    ctx.globalAlpha = 1;
    if (hover) {
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(hover.sx, hover.sy, Math.max(4, hover.p.r * hover.k * zoom + 4), 0, 6.2832); ctx.stroke();
      const lines = [
        `${hover.p.d}　${hover.p.src}${hover.p.p ? ' · ' + hover.p.p : ''}`,
        (hover.p.n || '(无标题)').slice(0, 46),
        `${hover.p.tp.join('、') || '未分类'}　你说了 ${hover.p.u} 次`,
      ];
      ctx.font = '12px system-ui';
      const bw = Math.max(...lines.map(l => ctx.measureText(l).width)) + 18;
      let bx = Math.min(hover.sx + 12, w - bw - 6), by = Math.min(hover.sy + 12, h - 66);
      ctx.fillStyle = 'rgba(10,13,17,.95)'; ctx.strokeStyle = '#2c353f';
      ctx.beginPath(); ctx.roundRect(bx, by, bw, 60, 7); ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#e6e9ee';
      lines.forEach((l, i) => ctx.fillText(l, bx + 9, by + 19 + i * 16));
      cv.style.cursor = 'pointer';
    } else cv.style.cursor = 'grab';

    if (spin && !drag) yaw += 0.0016;
    raf = requestAnimationFrame(draw);
  }

  let drag = null, raf = 0;
  cv.addEventListener('pointerdown', e => {
    drag = { x: e.clientX, y: e.clientY, yaw, pitch };
    cv.setPointerCapture(e.pointerId);
  });
  cv.addEventListener('pointermove', e => {
    const r = cv.getBoundingClientRect();
    mouse = { x: e.clientX - r.left, y: e.clientY - r.top };
    if (!drag) return;
    yaw = drag.yaw + (e.clientX - drag.x) * 0.006;
    pitch = Math.max(0.06, Math.min(1.5, drag.pitch + (e.clientY - drag.y) * 0.005));
  });
  cv.addEventListener('pointerup', e => {
    if (drag && Math.hypot(e.clientX - drag.x, e.clientY - drag.y) < 4 && hover) go('day', hover.p.d);
    drag = null;
  });
  cv.addEventListener('pointerleave', () => { mouse = { x: -1, y: -1 }; drag = null; });
  cv.addEventListener('wheel', e => {
    e.preventDefault();
    zoom = Math.max(0.35, Math.min(4, zoom * (e.deltaY > 0 ? 0.92 : 1.08)));
  }, { passive: false });

  raf = requestAnimationFrame(draw);
  // 视图切走时停掉动画，别让一个看不见的 canvas 一直吃 CPU
  new MutationObserver((m, o) => {
    if (!document.body.contains(cv)) { cancelAnimationFrame(raf); o.disconnect(); }
  }).observe(document.getElementById('view'), { childList: true });
}
