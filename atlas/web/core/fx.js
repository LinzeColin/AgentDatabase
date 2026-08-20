// core/fx.js —— 背景光场。只有「琉璃」用它。
//   琉璃      粒子 + 加色辉光 + 鼠标视差（参照 motionsites.ai 那类站点的做法）
//   星云宇宙  背景本身就是一整片 WebGL 星图，再叠一层 2D 粒子只会糊掉它 —— 所以不挂这一层
//   白昼      纸面上不该有星星。整套主题的主张是版式，不是光
//
// 画在一张 canvas 上，pointer-events:none，不拦交互。
// 页面不可见时停帧，别让一张看不见的画布一直吃 CPU。
// 没有 #fxlayer 的主题直接空转返回 —— 「这套主题不要背景动效」是合法选择，不是错误。

import { S } from './app.js';

let cv, ctx, raf = 0, particles = [], w = 0, h = 0, dpr = 1;
let mouse = { x: 0.5, y: 0.5, tx: 0.5, ty: 0.5 };
let t0 = 0, running = false;

const PALETTE = {
  dark: ['#7cc4ff', '#a78bfa', '#5ce6b4', '#ff9ecb'],
  light: ['#3358d4', '#7c5cd6', '#0a7a58', '#c02648'],
};

function resize() {
  if (!cv || !ctx) return;
  dpr = Math.min(2, devicePixelRatio || 1);
  w = innerWidth; h = innerHeight;
  cv.width = Math.floor(w * dpr);
  cv.height = Math.floor(h * dpr);
  cv.style.width = w + 'px';
  cv.style.height = h + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  seed();
}

function seed() {
  const colors = PALETTE[S.mode] || PALETTE.dark;
  // 粒子数按视口面积给，不是写死 —— 小窗口上 400 颗会糊成一片
  const n = S.theme === 'glass' ? Math.min(220, Math.round(w * h / 9000)) : 0;
  particles = Array.from({ length: n }, (_, i) => ({
    x: Math.random() * w, y: Math.random() * h,
    z: 0.25 + Math.random() * 0.75,
    r: 0.6 + Math.random() * 2.1,
    vx: (Math.random() - 0.5) * 0.16,
    vy: -0.05 - Math.random() * 0.2,
    c: colors[i % colors.length],
    a: 0.16 + Math.random() * 0.4,
    ph: Math.random() * 6.283,
  }));
}

function drawGlass(t) {
  ctx.clearRect(0, 0, w, h);
  // 两团缓慢漂移的辉光，给深空一点体积感
  const gx = w * (0.28 + 0.1 * Math.sin(t * 0.00007));
  const gy = h * (0.3 + 0.08 * Math.cos(t * 0.00009));
  const glow = (x, y, r, color, alpha) => {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, color); g.addColorStop(1, 'transparent');
    ctx.globalAlpha = alpha; ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill();
  };
  const strong = S.mode === 'dark' ? 0.2 : 0.1;
  glow(gx, gy, Math.max(w, h) * 0.42, PALETTE[S.mode][0], strong);
  glow(w - gx * 0.7, h - gy * 0.5, Math.max(w, h) * 0.34, PALETTE[S.mode][1], strong * 0.75);

  ctx.globalCompositeOperation = S.mode === 'dark' ? 'lighter' : 'source-over';
  const px = (mouse.x - 0.5), py = (mouse.y - 0.5);
  for (const p of particles) {
    p.x += p.vx * p.z; p.y += p.vy * p.z;
    if (p.y < -12) { p.y = h + 12; p.x = Math.random() * w; }
    if (p.x < -12) p.x = w + 12; else if (p.x > w + 12) p.x = -12;
    // 视差：近的粒子跟手更多，远的几乎不动 —— 这是深度感的来源
    const ox = px * 46 * p.z, oy = py * 30 * p.z;
    const tw = 0.72 + 0.28 * Math.sin(t * 0.0016 + p.ph);
    ctx.globalAlpha = p.a * tw * (S.mode === 'dark' ? 1 : 0.5);
    ctx.fillStyle = p.c;
    ctx.beginPath(); ctx.arc(p.x + ox, p.y + oy, p.r * p.z * 1.4, 0, 6.2832); ctx.fill();
  }
  ctx.globalCompositeOperation = 'source-over';
  ctx.globalAlpha = 1;
}


function frame(t) {
  if (!ctx) { running = false; return; }
  if (!t0) t0 = t;
  mouse.x += (mouse.tx - mouse.x) * 0.055;
  mouse.y += (mouse.ty - mouse.y) * 0.055;
  if (S.theme === 'glass') drawGlass(t - t0);
  else ctx.clearRect(0, 0, w, h);
  raf = requestAnimationFrame(frame);
}

function start() {
  if (running) return;
  running = true;
  raf = requestAnimationFrame(frame);
}
function stop() {
  running = false;
  cancelAnimationFrame(raf);
  if (ctx) ctx.clearRect(0, 0, w, h);
}

let wired = false;
export function initFX() {
  cv = document.getElementById('fxlayer');
  if (!cv) { stop(); ctx = null; return; }     // 这套主题不要背景动效
  ctx = cv.getContext('2d');
  resize();
  if (wired) { start(); return; }              // 全局监听只挂一次，切主题不该越挂越多
  wired = true;
  addEventListener('resize', resize, { passive: true });
  addEventListener('pointermove', e => {
    mouse.tx = e.clientX / innerWidth;
    mouse.ty = e.clientY / innerHeight;
  }, { passive: true });
  addEventListener('atlas:theme', () => { seed(); t0 = 0; });
  // 标签页切走就停 —— 看不见的画布不该继续烧 CPU
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop(); else start();
  });
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
    // 尊重系统设置：画一帧静态底纹就停，不做任何持续动画
    if (S.theme === 'glass') drawGlass(0);
    return;
  }
  start();
}
