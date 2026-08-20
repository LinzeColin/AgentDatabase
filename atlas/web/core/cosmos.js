// core/cosmos.js —— 星云宇宙的持久 3D 场景。
//
// 和 home.linzezhang.com 那类门户的区别只有一条：**这里每一颗星都是一条真实记录**。
// 不是先做好一个漂亮场景再往上贴数据，而是场景本身由数据生成 ——
// 会话变成星，领域变成星云团，项目变成环绕体，时间变成深度。
// 数据一变，星图就变；数据是空的，星图也就该是空的。
//
// three.js 本地 vendor（CSP 的 script-src 'self' 只挡 CDN）。

import * as THREE from '../vendor/three.module.min.js';

const DOMAIN_HUE = {
  'AI工具开发': 0.56, '软件工程': 0.52, '人物蒸馏': 0.78, '视频与素材': 0.90,
  '工业设备维修': 0.08, '文书与合同': 0.11, '学习与研究': 0.34, '求职与个人': 0.62,
};
const FALLBACK_HUE = 0.58;

function haloTexture(inner = 1, mid = 0.34) {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const x = c.getContext('2d');
  const g = x.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, `rgba(255,255,255,${inner})`);
  g.addColorStop(0.28, `rgba(255,255,255,${mid})`);
  g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g;
  x.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** 确定性伪随机：同一份数据每次得到同一张星图，不会今天一个样明天一个样。 */
function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

export function buildCosmos(canvas, atlas, opts = {}) {
  // 浅色模式下加色混合等于什么都不画（白底上加光还是白）。
  // 所以浅色走正常混合 + 压暗的颜色 —— 星图在白昼底下也必须看得见，否则「浅色」就是把这套主题关掉。
  const light = (opts.mode || 'dark') === 'light';
  const BLEND = light ? THREE.NormalBlending : THREE.AdditiveBlending;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(2, devicePixelRatio || 1));
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(light ? 0xeaeefc : 0x05030f, light ? 0.00014 : 0.00020);
  const camera = new THREE.PerspectiveCamera(58, 1, 1, 12000);

  const sessions = atlas.sessions || [];
  const days = (atlas.days || []).map(d => d.d);
  const dayIdx = new Map(days.map((d, i) => [d, i]));
  const span = Math.max(1, days.length - 1);
  const DEPTH = 4200;                 // 时间轴总长度：最早在最远处
  const R_MAX = 760;

  // ── 星：一条会话一颗 ──
  const N = sessions.length;
  const pos = new Float32Array(N * 3);
  const col = new Float32Array(N * 3);
  const siz = new Float32Array(N);
  const meta = new Array(N);
  const rand = rng(N * 7919 + days.length);
  const c = new THREE.Color();
  let k = 0;
  for (const s of sessions) {
    const di = dayIdx.get(s.d);
    if (di == null) continue;
    const t = di / span;                          // 0 = 最早
    const hour = (new Date(new Date(s.t).getTime() + 10 * 3600e3)).getUTCHours();
    const ang = (hour / 24) * Math.PI * 2 + (rand() - 0.5) * 0.42;
    // 半径由「你说了几次」决定：说得越多离轴心越远，中心留给一问一答
    const r = 90 + Math.min(1, Math.sqrt(Math.max(1, s.u)) / 9) * R_MAX * (0.35 + rand() * 0.65);
    pos[k * 3] = Math.cos(ang) * r;
    pos[k * 3 + 1] = Math.sin(ang) * r * 0.55 + (rand() - 0.5) * 120;
    pos[k * 3 + 2] = -t * DEPTH;
    const hue = DOMAIN_HUE[s.tp && s.tp[0]] ?? FALLBACK_HUE;
    const human = s.k === 'human';
    c.setHSL(hue, human ? 0.80 : 0.26, light ? (human ? 0.44 : 0.72) : (human ? 0.70 : 0.38));
    col[k * 3] = c.r; col[k * 3 + 1] = c.g; col[k * 3 + 2] = c.b;
    siz[k] = (human ? 26 : 11) + Math.min(40, Math.sqrt(Math.max(1, s.u)) * 6.4);
    meta[k] = s;
    k++;
  }
  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute('position', new THREE.BufferAttribute(pos.subarray(0, k * 3), 3));
  starGeo.setAttribute('color', new THREE.BufferAttribute(col.subarray(0, k * 3), 3));
  starGeo.setAttribute('size', new THREE.BufferAttribute(siz.subarray(0, k), 1));
  const starMat = new THREE.PointsMaterial({
    map: haloTexture(1, 0.32), vertexColors: true, size: 20, sizeAttenuation: true,
    transparent: true, opacity: light ? 0.8 : 0.95, blending: BLEND, depthWrite: false,
  });
  // 让每颗星用自己的 size：PointsMaterial 只有一个全局 size，注入到 shader 里
  starMat.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader
      .replace('uniform float size;', 'uniform float size;\nattribute float size2;')
      .replace('gl_PointSize = size;', 'gl_PointSize = size2;')
      // 下限 1.9px：低于一个像素的点在屏幕上就是不存在。上限 96px 防止贴脸时糊屏。
      .replace('#include <logdepthbuf_vertex>',
               'gl_PointSize = clamp(gl_PointSize, 1.9, 96.0);\n\t#include <logdepthbuf_vertex>');
  };
  starGeo.attributes.size.name = 'size2';
  starGeo.setAttribute('size2', starGeo.attributes.size);
  const stars = new THREE.Points(starGeo, starMat);
  scene.add(stars);

  // ── 星云团：一个领域一团，位置取该领域所有会话的重心 ──
  const clouds = new THREE.Group();
  const byDom = new Map();
  for (let i = 0; i < k; i++) {
    const d = meta[i].tp && meta[i].tp[0];
    if (!d) continue;
    if (!byDom.has(d)) byDom.set(d, []);
    byDom.get(d).push(i);
  }
  const cloudTex = haloTexture(0.55, 0.16);
  for (const [dom, idxs] of byDom) {
    if (idxs.length < 12) continue;
    let cx = 0, cy = 0, cz = 0;
    for (const i of idxs) { cx += pos[i * 3]; cy += pos[i * 3 + 1]; cz += pos[i * 3 + 2]; }
    cx /= idxs.length; cy /= idxs.length; cz /= idxs.length;
    const n = Math.min(900, 140 + idxs.length * 3);
    const p = new Float32Array(n * 3);
    const r2 = rng(dom.length * 131 + idxs.length);
    const spread = 260 + Math.sqrt(idxs.length) * 42;
    for (let i = 0; i < n; i++) {
      p[i * 3] = cx + (r2() - 0.5) * spread * 2;
      p[i * 3 + 1] = cy + (r2() - 0.5) * spread;
      p[i * 3 + 2] = cz + (r2() - 0.5) * spread * 2.4;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(p, 3));
    const hue = DOMAIN_HUE[dom] ?? FALLBACK_HUE;
    const cc = new THREE.Color().setHSL(hue, 0.66, light ? 0.62 : 0.5);
    const m = new THREE.PointsMaterial({
      map: cloudTex, color: cc, size: 300, sizeAttenuation: true,
      transparent: true, opacity: light ? 0.1 : 0.15, blending: BLEND, depthWrite: false,
    });
    const pts = new THREE.Points(g, m);
    pts.userData = { domain: dom, n: idxs.length };
    clouds.add(pts);
  }
  scene.add(clouds);

  // ── 远景恒星背景：给深空一点底噪，不承载数据，纯背景 ──
  const bgN = 1400;
  const bp = new Float32Array(bgN * 3);
  const r3 = rng(20260820);
  for (let i = 0; i < bgN; i++) {
    const rr = 3000 + r3() * 5000;
    const th = r3() * Math.PI * 2, ph = Math.acos(2 * r3() - 1);
    bp[i * 3] = rr * Math.sin(ph) * Math.cos(th);
    bp[i * 3 + 1] = rr * Math.cos(ph);
    bp[i * 3 + 2] = rr * Math.sin(ph) * Math.sin(th) - DEPTH * 0.5;
  }
  const bgGeo = new THREE.BufferGeometry();
  bgGeo.setAttribute('position', new THREE.BufferAttribute(bp, 3));
  scene.add(new THREE.Points(bgGeo, new THREE.PointsMaterial({
    map: haloTexture(0.9, 0.2), color: light ? 0x8fa4cc : 0xbfd0ff, size: 16, sizeAttenuation: true,
    transparent: true, opacity: light ? 0.45 : 0.7, blending: BLEND, depthWrite: false })));

  // ── 时间刻度环：每个月一道环，飞行时能看出自己在哪一段 ──
  const rings = new THREE.Group();
  const months = new Map();
  days.forEach((d, i) => { const m = d.slice(0, 7); if (!months.has(m)) months.set(m, i); });
  for (const [m, i] of months) {
    const g = new THREE.RingGeometry(R_MAX * 1.16, R_MAX * 1.18, 96);
    const mat = new THREE.MeshBasicMaterial({ color: light ? 0x5f7bd6 : 0x7c9cff, transparent: true,
      opacity: light ? 0.13 : 0.16, side: THREE.DoubleSide, depthWrite: false });
    const ring = new THREE.Mesh(g, mat);
    ring.position.z = -(i / span) * DEPTH;
    ring.scale.y = 0.55;
    ring.userData = { month: m };
    rings.add(ring);
  }
  scene.add(rings);

  // ── 相机：沿时间轴飞行 ──
  const cam = { t: 1, drift: 0, yaw: 0, pitch: 0, targetT: 1 };
  function place() {
    const z = -(1 - cam.t) * DEPTH;
    camera.position.set(Math.sin(cam.yaw) * 240, 95 + cam.pitch * 220, z + 620);
    camera.lookAt(Math.sin(cam.yaw) * 70, 25, z - 720);
  }

  function resize() {
    const r = canvas.getBoundingClientRect();
    const w = Math.max(120, Math.round(r.width) || canvas.clientWidth || innerWidth);
    const h = Math.max(120, Math.round(r.height) || canvas.clientHeight || innerHeight);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  let disposed = false;
  function frame(dt) {
    if (disposed) return;
    cam.t += (cam.targetT - cam.t) * 0.045;
    cam.drift += dt * 0.00004;
    cam.yaw += (Math.sin(cam.drift) * 0.16 - cam.yaw) * 0.03;
    place();
    stars.rotation.z += dt * 0.000012;
    clouds.rotation.z = stars.rotation.z * 0.6;
    renderer.render(scene, camera);
  }

  resize();
  place();

  return {
    resize, frame,
    /** 0 = 最早，1 = 最近。用来把「当前视图看的是哪一段时间」映射成相机位置。 */
    flyTo(t) { cam.targetT = Math.max(0, Math.min(1, t)); },
    at() { return cam.t; },
    dayAt() { return days[Math.round(cam.t * span)] || days[days.length - 1]; },
    /** 把某一天推到镜头前。找不到就飞到时间上最接近的一天。 */
    flyToDay(iso) {
      if (!days.length) return;
      let i = days.indexOf(iso);
      if (i < 0) { i = days.findIndex(d => d >= iso); if (i < 0) i = days.length - 1; }
      cam.targetT = span ? i / span : 0;
    },
    stats: { stars: k, clouds: clouds.children.length, months: months.size, days: days.length },
    dispose() {
      disposed = true;
      starGeo.dispose(); starMat.dispose(); bgGeo.dispose();
      clouds.children.forEach(p => { p.geometry.dispose(); p.material.dispose(); });
      rings.children.forEach(p => { p.geometry.dispose(); p.material.dispose(); });
      cloudTex.dispose();
      renderer.dispose();
    },
  };
}
