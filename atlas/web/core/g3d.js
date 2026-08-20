// core/g3d.js —— 手写的 3D：投影、轨道相机、力导布局。
// CSP 是 script-src 'self'，装不了 three.js；而且为了画几百个点带一个 600KB 的库也不划算。

export function makeCamera(opts = {}) {
  return {
    yaw: opts.yaw ?? -0.6, pitch: opts.pitch ?? 0.5, zoom: opts.zoom ?? 1,
    dist: opts.dist ?? 900, spin: opts.spin ?? 0.0013,
  };
}

export function project(p, cam, cx, cy) {
  const cy_ = Math.cos(cam.yaw), sy_ = Math.sin(cam.yaw);
  const x1 = p.x * cy_ - p.z * sy_;
  const z1 = p.x * sy_ + p.z * cy_;
  const cp = Math.cos(cam.pitch), sp = Math.sin(cam.pitch);
  const y1 = p.y * cp - z1 * sp;
  const z2 = p.y * sp + z1 * cp;
  const k = cam.dist / (cam.dist + z2 + cam.dist * 0.55);
  return { sx: cx + x1 * k * cam.zoom, sy: cy + y1 * k * cam.zoom, k, depth: z2 };
}

/** 轨道控制。返回 dispose，视图切走时务必调用，否则监听器会越积越多。 */
export function orbit(canvas, cam, onChange) {
  let drag = null;
  const down = e => { drag = { x: e.clientX, y: e.clientY, yaw: cam.yaw, pitch: cam.pitch };
    canvas.setPointerCapture(e.pointerId); };
  const move = e => {
    if (!drag) return;
    cam.yaw = drag.yaw + (e.clientX - drag.x) * 0.0062;
    cam.pitch = Math.max(-1.45, Math.min(1.45, drag.pitch + (e.clientY - drag.y) * 0.005));
    onChange && onChange();
  };
  const up = () => { drag = null; };
  const wheel = e => {
    e.preventDefault();
    cam.zoom = Math.max(0.3, Math.min(5, cam.zoom * (e.deltaY > 0 ? 0.92 : 1.086)));
    onChange && onChange();
  };
  canvas.addEventListener('pointerdown', down);
  canvas.addEventListener('pointermove', move);
  canvas.addEventListener('pointerup', up);
  canvas.addEventListener('pointerleave', up);
  canvas.addEventListener('wheel', wheel, { passive: false });
  return {
    dragging: () => !!drag,
    dispose() {
      canvas.removeEventListener('pointerdown', down);
      canvas.removeEventListener('pointermove', move);
      canvas.removeEventListener('pointerup', up);
      canvas.removeEventListener('pointerleave', up);
      canvas.removeEventListener('wheel', wheel);
    },
  };
}

/**
 * 3D 力导布局。斥力全对全 + 边上的弹簧 + 回中心的弱重力。
 *
 * 迭代次数写死，**绝不写「跑到收敛为止」** —— 没有上限的循环在这台机器上出过事
 * （同时挂过 7 个，最长 1 天 5 小时）。300 步对几百个节点已经足够稳定，
 * 而且是确定性的：同样的输入每次得到同样的图，不会今天一个样明天一个样。
 */
export function forceLayout(nodes, edges, opts = {}) {
  const N = nodes.length;
  if (!N) return nodes;
  const steps = opts.steps ?? 300;
  const R = opts.radius ?? 300;
  const kRep = opts.repulsion ?? 9000;
  const kSpring = opts.spring ?? 0.012;
  const gravity = opts.gravity ?? 0.0055;

  const idx = new Map(nodes.map((n, i) => [n.id, i]));
  // 用节点 id 派生初始位置，而不是 Math.random()：布局要可复现
  nodes.forEach((n, i) => {
    let hsh = 0;
    for (let c = 0; c < n.id.length; c++) hsh = (hsh * 31 + n.id.charCodeAt(c)) | 0;
    const a = ((hsh >>> 0) % 1000) / 1000 * 6.2832;
    const b = (((hsh >>> 10) >>> 0) % 1000) / 1000 * Math.PI;
    const r = R * (0.4 + ((i * 37) % 100) / 160);
    n.x = r * Math.sin(b) * Math.cos(a);
    n.y = r * Math.cos(b) * 0.6;
    n.z = r * Math.sin(b) * Math.sin(a);
    n.vx = n.vy = n.vz = 0;
  });

  const E = edges.map(e => ({ a: idx.get(e.a), b: idx.get(e.b), w: e.w }))
    .filter(e => e.a != null && e.b != null);
  const maxW = Math.max(1, ...E.map(e => e.w));

  for (let s = 0; s < steps; s++) {
    const cool = 1 - s / steps;
    for (let i = 0; i < N; i++) {
      const a = nodes[i];
      for (let j = i + 1; j < N; j++) {
        const b = nodes[j];
        let dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
        let d2 = dx * dx + dy * dy + dz * dz;
        if (d2 < 1) { d2 = 1; dx = (i % 3) - 1; dy = (j % 3) - 1; dz = 1; }
        const f = kRep / d2;
        const d = Math.sqrt(d2);
        const ux = dx / d, uy = dy / d, uz = dz / d;
        a.vx += ux * f; a.vy += uy * f; a.vz += uz * f;
        b.vx -= ux * f; b.vy -= uy * f; b.vz -= uz * f;
      }
    }
    for (const e of E) {
      const a = nodes[e.a], b = nodes[e.b];
      const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
      const f = kSpring * (0.35 + e.w / maxW);
      a.vx += dx * f; a.vy += dy * f; a.vz += dz * f;
      b.vx -= dx * f; b.vy -= dy * f; b.vz -= dz * f;
    }
    for (const n of nodes) {
      n.vx -= n.x * gravity; n.vy -= n.y * gravity * 1.7; n.vz -= n.z * gravity;
      const damp = 0.72 * cool + 0.12;
      n.x += n.vx * damp; n.y += n.vy * damp; n.z += n.vz * damp;
      n.vx *= 0.55; n.vy *= 0.55; n.vz *= 0.55;
    }
  }
  // 归一到统一半径，免得不同数据量下缩放差太多
  const maxR = Math.max(1, ...nodes.map(n => Math.hypot(n.x, n.y, n.z)));
  const k = R / maxR;
  nodes.forEach(n => { n.x *= k; n.y *= k; n.z *= k; });
  return nodes;
}

/** 高 DPI 画布：不做这一步，视网膜屏上所有文字和线都是糊的。 */
export function fitCanvas(cv, cssHeight) {
  const dpr = Math.min(2, devicePixelRatio || 1);
  // 首帧时元素可能还没布局，clientWidth 为 0 —— 半径算出来是负数，
  // canvas 的 arc() 会直接抛「radius is negative」把整个视图打死。
  // 所以这里给一个下限，画得糊一帧也比整页报错强。
  const w = Math.max(120,
    cv.clientWidth || (cv.parentElement && cv.parentElement.clientWidth) || innerWidth - 60);
  cv.style.height = cssHeight + 'px';
  cv.width = Math.floor(w * dpr);
  cv.height = Math.floor(cssHeight * dpr);
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h: cssHeight };
}

/** 视图切走时停帧。返回 {stop}，别让看不见的 canvas 一直跑。 */
export function loop(fn) {
  let raf = 0, alive = true;
  const tick = t => { if (!alive) return; fn(t); raf = requestAnimationFrame(tick); };
  raf = requestAnimationFrame(tick);
  return { stop() { alive = false; cancelAnimationFrame(raf); } };
}

/** 读 CSS 变量并保证拿到一个合法颜色。
 *  主题 CSS 还没加载、或变量名写错时，getPropertyValue 返回空串，
 *  canvas 的 addColorStop('') 会直接抛错、整个视图当场死掉 —— 实测踩过。
 *  兜底表放在这里而不是各个视图里：调用方少一个必须记得声明的东西，
 *  就少一处会忘。一个取不到的颜色不该让页面崩。 */
const CSS_FALLBACK = {
  '--acc': '#7cc4ff', '--acc2': '#b58cff', '--ok': '#5ce6b4', '--warn': '#ffc46b', '--bad': '#ff7a92',
  '--fg': '#e6e9ee', '--dim': '#8e99a8', '--dim2': '#5e6773',
  '--line': '#2a3140', '--line2': '#1a2030', '--track': '#2a3140',
  '--hair': '#1c2530', '--hair2': '#141b23', '--sel': '#1a2230',
  '--rule': '#ddd4c4', '--rule2': '#ece4d5', '--paper': '#fffdf7',
};

export function cssVar(name, fallback) {
  const v = getComputedStyle(document.body).getPropertyValue(name);
  return (v && v.trim()) || fallback || CSS_FALLBACK[name] || '#888';
}
