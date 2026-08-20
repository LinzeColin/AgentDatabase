// core/scene3d.js —— 真正的 WebGL 3D（three.js，本地 vendor）。
//
// 上一版说「CSP 装不了 three.js」是判断错了：CSP 的 script-src 'self' 只挡 CDN，
// 和 GSAP 一样 vendor 到本地就完全合法。所以这一版是真网格、真光照、真深度，
// 不是把二维点画得像三维。
//
// 三套主题共用这一个场景构建器，材质与灯光按主题给不同配置 —— 同一份几何，
// 三种质感：控制台=线框自发光，琉璃=玻璃高光+加色辉光，手记=纸面哑光。

import * as THREE from '../vendor/three.module.min.js';

export const THEME_LOOK = {
  console: {
    bg: null, fogNear: 900, fogFar: 2600,
    node: { metalness: 0.1, roughness: 0.85, emissiveK: 0.55, flat: true },
    edge: { opacity: 0.30, additive: false, width: 1 },
    halo: 0.0, ambient: 0.75, key: 0.5, rim: 0.25,
  },
  glass: {
    bg: null, fogNear: 1100, fogFar: 3200,
    node: { metalness: 0.35, roughness: 0.18, emissiveK: 0.85, flat: false },
    edge: { opacity: 0.42, additive: true, width: 1 },
    halo: 1.0, ambient: 0.35, key: 1.15, rim: 0.9,
  },
  journal: {
    bg: null, fogNear: 800, fogFar: 2400,
    node: { metalness: 0.0, roughness: 1.0, emissiveK: 0.18, flat: false },
    edge: { opacity: 0.22, additive: false, width: 1 },
    halo: 0.0, ambient: 0.9, key: 0.65, rim: 0.15,
  },
};

/** 辉光贴图：一张径向渐变的小画布。比装 postprocessing 便宜得多，效果够用。 */
function haloTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.25, 'rgba(255,255,255,.42)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/**
 * 建一个耦合星图场景。
 * nodes: [{id,label,kind,w,x,y,z,color}]   edges: [{a,b,w}]
 * 返回 { mount, dispose, setHover, resize, camera, tick }
 */
export function buildGraphScene(canvas, nodes, edges, opts = {}) {
  const look = THEME_LOOK[opts.theme] || THEME_LOOK.glass;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(2, devicePixelRatio || 1));
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x000000, look.fogNear, look.fogFar);

  const camera = new THREE.PerspectiveCamera(46, 1, 1, 6000);
  const orbit = { yaw: -0.6, pitch: 0.28, dist: opts.dist || 820 };

  scene.add(new THREE.AmbientLight(0xffffff, look.ambient));
  const key = new THREE.DirectionalLight(0xffffff, look.key);
  key.position.set(1, 1.4, 0.8);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x88aaff, look.rim);
  rim.position.set(-1, -0.6, -1);
  scene.add(rim);

  const maxW = Math.max(1, ...nodes.map(n => n.w));
  const geo = new THREE.SphereGeometry(1, look.node.flat ? 8 : 20, look.node.flat ? 6 : 14);
  // emissive 在 InstancedMesh 上不跟随实例色，所以自发光靠 onBeforeCompile 注入：
  // 把实例色按比例直接加到 outgoingLight 上，暗背景下节点才不会糊成一团。
  const mat = new THREE.MeshStandardMaterial({
    metalness: look.node.metalness, roughness: look.node.roughness,
    flatShading: !!look.node.flat, transparent: true, opacity: 1,
  });
  const emissiveK = look.node.emissiveK;
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uEmissiveK = { value: emissiveK };
    shader.fragmentShader = shader.fragmentShader
      .replace('void main() {', 'uniform float uEmissiveK;\nvoid main() {')
      .replace('#include <opaque_fragment>',
        'outgoingLight += diffuseColor.rgb * uEmissiveK;\n#include <opaque_fragment>');
  };
  const inst = new THREE.InstancedMesh(geo, mat, nodes.length);
  inst.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const colorAttr = new Float32Array(nodes.length * 3);
  const dummy = new THREE.Object3D();
  const baseScale = [];
  nodes.forEach((n, i) => {
    const r = 5 + 22 * Math.sqrt(n.w / maxW);
    baseScale.push(r);
    dummy.position.set(n.x, n.y, n.z);
    dummy.scale.setScalar(r);
    dummy.updateMatrix();
    inst.setMatrixAt(i, dummy.matrix);
    const c = new THREE.Color(n.color || '#7cc4ff');
    colorAttr[i * 3] = c.r; colorAttr[i * 3 + 1] = c.g; colorAttr[i * 3 + 2] = c.b;
  });
  inst.instanceColor = new THREE.InstancedBufferAttribute(colorAttr, 3);
  inst.instanceColor.setUsage(THREE.DynamicDrawUsage);
  scene.add(inst);

  // 边：一条 LineSegments 装全部，比每条一个对象快得多
  const idx = new Map(nodes.map((n, i) => [n.id, i]));
  const pos = [], ecol = [];
  const maxE = Math.max(1, ...edges.map(e => e.w));
  for (const e of edges) {
    const a = nodes[idx.get(e.a)], b = nodes[idx.get(e.b)];
    if (!a || !b) continue;
    pos.push(a.x, a.y, a.z, b.x, b.y, b.z);
    const ca = new THREE.Color(a.color || '#7cc4ff'), cb = new THREE.Color(b.color || '#b58cff');
    const k = 0.25 + 0.75 * (e.w / maxE);
    ecol.push(ca.r * k, ca.g * k, ca.b * k, cb.r * k, cb.g * k, cb.b * k);
  }
  const egeo = new THREE.BufferGeometry();
  egeo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  egeo.setAttribute('color', new THREE.Float32BufferAttribute(ecol, 3));
  const emat = new THREE.LineBasicMaterial({
    vertexColors: true, transparent: true, opacity: look.edge.opacity,
    blending: look.edge.additive ? THREE.AdditiveBlending : THREE.NormalBlending,
    depthWrite: false,
  });
  const lines = new THREE.LineSegments(egeo, emat);
  scene.add(lines);

  // 辉光：加色 Points，只有琉璃开
  let halo = null;
  if (look.halo > 0) {
    const hgeo = new THREE.BufferGeometry();
    const hp = [], hc = [], hs = [];
    nodes.forEach((n, i) => {
      hp.push(n.x, n.y, n.z);
      const c = new THREE.Color(n.color || '#7cc4ff');
      hc.push(c.r, c.g, c.b);
      hs.push(baseScale[i] * 10);
    });
    hgeo.setAttribute('position', new THREE.Float32BufferAttribute(hp, 3));
    hgeo.setAttribute('color', new THREE.Float32BufferAttribute(hc, 3));
    hgeo.setAttribute('size', new THREE.Float32BufferAttribute(hs, 1));
    const hmat = new THREE.PointsMaterial({
      map: haloTexture(), vertexColors: true, size: 60, sizeAttenuation: true,
      transparent: true, opacity: 0.46 * look.halo, blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    halo = new THREE.Points(hgeo, hmat);
    scene.add(halo);
  }

  const ray = new THREE.Raycaster();
  ray.params.Points = { threshold: 14 };
  const ndc = new THREE.Vector2(-2, -2);
  let hoverIdx = -1;

  function resize() {
    const w = Math.max(120, canvas.clientWidth), h = Math.max(120, canvas.clientHeight);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function setPointer(x, y) {
    const r = canvas.getBoundingClientRect();
    ndc.x = ((x - r.left) / r.width) * 2 - 1;
    ndc.y = -((y - r.top) / r.height) * 2 + 1;
  }
  function clearPointer() { ndc.set(-2, -2); }

  function updateCamera() {
    const cp = Math.cos(orbit.pitch), sp = Math.sin(orbit.pitch);
    camera.position.set(
      Math.sin(orbit.yaw) * cp * orbit.dist,
      sp * orbit.dist,
      Math.cos(orbit.yaw) * cp * orbit.dist);
    camera.lookAt(0, 0, 0);
  }

  const tmp = new THREE.Object3D();
  function tick(dt, spin) {
    if (spin) orbit.yaw += 0.00035 * dt;
    updateCamera();

    // 命中检测：把 raycaster 打到实例网格上
    let hit = -1;
    if (ndc.x > -1.5) {
      ray.setFromCamera(ndc, camera);
      const res = ray.intersectObject(inst, false);
      if (res.length) hit = res[0].instanceId;
    }
    if (hit !== hoverIdx) {
      hoverIdx = hit;
      const near = new Set();
      if (hit >= 0) {
        const id = nodes[hit].id;
        for (const e of edges) {
          if (e.a === id) near.add(e.b);
          else if (e.b === id) near.add(e.a);
        }
        near.add(id);
      }
      nodes.forEach((n, i) => {
        const on = hit < 0 || near.has(n.id);
        const boost = i === hit ? 1.5 : 1;
        tmp.position.set(n.x, n.y, n.z);
        tmp.scale.setScalar(baseScale[i] * boost * (on ? 1 : 0.55));
        tmp.updateMatrix();
        inst.setMatrixAt(i, tmp.matrix);
        const c = new THREE.Color(n.color || '#7cc4ff');
        const k = on ? (i === hit ? 1.35 : 1) : 0.22;
        colorAttr[i * 3] = c.r * k; colorAttr[i * 3 + 1] = c.g * k; colorAttr[i * 3 + 2] = c.b * k;
      });
      inst.instanceMatrix.needsUpdate = true;
      inst.instanceColor.needsUpdate = true;
      emat.opacity = hit >= 0 ? look.edge.opacity * 0.35 : look.edge.opacity;
      if (halo) halo.material.opacity = (hit >= 0 ? 0.22 : 0.46) * look.halo;
    }
    renderer.render(scene, camera);
    return hoverIdx;
  }

  function dispose() {
    geo.dispose(); mat.dispose(); egeo.dispose(); emat.dispose();
    if (halo) { halo.geometry.dispose(); halo.material.map.dispose(); halo.material.dispose(); }
    renderer.dispose();
  }

  resize();
  updateCamera();
  return { scene, camera, orbit, resize, setPointer, clearPointer, tick, dispose,
           hovered: () => hoverIdx };
}
