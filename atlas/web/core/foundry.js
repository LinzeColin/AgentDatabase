// core/foundry.js —— 「鎏金」的持久 3D 场景：记忆碑林。
//
// 和 cosmos.js（星云宇宙）是两套完全不同的手法，不是同一张图换皮：
//   cosmos  Points 点精灵 + AdditiveBlending + 无光源自发光 + 沿时间轴穿越
//   foundry InstancedMesh 实体棱柱 + PBR 三点布光 + 倒影/阴影 + 绕碑林摇臂
//
// 一根柱 = 一天。高 = 你亲自开口的场数，截面 = 那天的 token，
// 金脉密度 = 人的占比（机器代跑的日子近乎素铜），顶端嵌片 = 那天的主话题，
// 地面上的金线 = 你反复问过的同一个问题（踩过的坑用金缮补上）。
// 数据是空的，厅就该是空的。
//
// three.js 本地 vendor 是 core-only：没有 EffectComposer / UnrealBloomPass。
// 所以后期处理是手写的 4 个 pass（见 §后期）—— 这不是偷懒，是 CSP 只允许 'self'。

import * as THREE from '../vendor/three.module.min.js';

const TOPIC_HEX = {
  '修bug': 0xff6b6b, '部署上线': 0x4ec9a7, '重构简化': 0xc48fff, '测试验收': 0xffd166,
  '数据': 0x63d2ff, '自动化': 0x5ce6b4, '治理规范': 0xffa94d, '文档': 0x9aa5b1,
  '前端界面': 0xff9ecb, '办公文书': 0xa0d8b3, '业务方案': 0xffc078, '赚钱': 0xffe066,
  '找工作': 0x74c0fc, '学习': 0xb197fc,
};
const FALLBACK_TOPIC = 0xb9a882;

/** 确定性伪随机：同一份数据每次得到同一座厅，不会今天一个样明天一个样。 */
function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

/** 切角棱柱：4 个侧面 + 4 个倒角面 + 1 个顶面 = 18 三角形。
 *  单位尺寸（x,z ∈ [-.5,.5]，y ∈ [0,1]），实例矩阵负责真正的高与粗。
 *  倒角是这套主题的形状母题 —— 面板、铭牌、按钮全用同一个 45° 切角。 */
function steleGeometry(chamfer = 0.16) {
  const c = chamfer, h1 = 1 - c, i = 0.5 - c;
  const pos = [], nrm = [], uv = [];
  const quad = (a, b, cc, d, n) => {
    for (const [p, u] of [[a, [0, 0]], [b, [1, 0]], [cc, [1, 1]], [a, [0, 0]], [cc, [1, 1]], [d, [0, 1]]]) {
      pos.push(p[0], p[1], p[2]); nrm.push(n[0], n[1], n[2]); uv.push(u[0], u[1]);
    }
  };
  const s = 0.5;
  // 四个侧面
  quad([-s, 0, s], [s, 0, s], [s, h1, s], [-s, h1, s], [0, 0, 1]);
  quad([s, 0, -s], [-s, 0, -s], [-s, h1, -s], [s, h1, -s], [0, 0, -1]);
  quad([s, 0, s], [s, 0, -s], [s, h1, -s], [s, h1, s], [1, 0, 0]);
  quad([-s, 0, -s], [-s, 0, s], [-s, h1, s], [-s, h1, -s], [-1, 0, 0]);
  // 四个倒角面
  const k = Math.SQRT1_2;
  quad([-s, h1, s], [s, h1, s], [i, 1, i], [-i, 1, i], [0, k, k]);
  quad([s, h1, -s], [-s, h1, -s], [-i, 1, -i], [i, 1, -i], [0, k, -k]);
  quad([s, h1, s], [s, h1, -s], [i, 1, -i], [i, 1, i], [k, k, 0]);
  quad([-s, h1, -s], [-s, h1, s], [-i, 1, i], [-i, 1, -i], [-k, k, 0]);
  // 顶面
  quad([-i, 1, i], [i, 1, i], [i, 1, -i], [-i, 1, -i], [0, 1, 0]);

  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pos), 3));
  g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(nrm), 3));
  g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(uv), 2));
  return g;
}

/** 往 MeshStandardMaterial 里注错金着色。走 onBeforeCompile，不自己写整套 PBR。 */
function giltShader(mat, uni) {
  mat.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, uni);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>
        attribute float aGold;
        attribute float aChip;
        attribute vec3 aTopic;
        varying float vGold;
        varying float vChip;
        varying vec3 vTopic;
        varying vec3 vLocal;`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        vGold = aGold; vChip = aChip; vTopic = aTopic; vLocal = transformed;`);

    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
        uniform float uGlow;
        uniform vec3 uGold;
        uniform vec3 uBase;
        varying float vGold;
        varying float vChip;
        varying vec3 vTopic;
        varying vec3 vLocal;
        float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
        float vnoise(vec2 p){
          vec2 i = floor(p), f = fract(p);
          vec2 u = f * f * (3.0 - 2.0 * f);
          return mix(mix(h21(i), h21(i + vec2(1,0)), u.x),
                     mix(h21(i + vec2(0,1)), h21(i + vec2(1,1)), u.x), u.y);
        }
        float fbm(vec2 p){ return vnoise(p) * 0.62 + vnoise(p * 2.17) * 0.26 + vnoise(p * 4.4) * 0.12; }`)
      // 金脉：取 fbm 的等值线窄带，只在这条带上把青铜换成金。
      // 用等值线而不是阈值，出来的才是「脉」而不是「斑」。
      .replace('vec4 diffuseColor = vec4( diffuse, opacity );', `
        float vein = smoothstep(0.030, 0.0, abs(fbm(vLocal.xz * 5.2 + vLocal.y * 1.7) - 0.5));
        vein *= vGold;
        vec3 base = mix(uBase, uGold, vein);
        float topMask = step(0.86, vLocal.y);
        base = mix(base, vTopic, topMask * 0.82);
        if (vChip > 0.5 && vLocal.y > 0.9 && (vLocal.x + vLocal.z) > 0.52) discard;
        vec4 diffuseColor = vec4( base, opacity );
        float vVein = vein;`)
      .replace('vec3 totalEmissiveRadiance = emissive;', `
        vec3 totalEmissiveRadiance = emissive + uGold * vVein * uGlow;`);
  };
  mat.customProgramCacheKey = () => 'gilt-v1';
  return mat;
}

const FS_VERT = `varying vec2 vUv;
void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

export function buildFoundry(canvas, atlas, opts = {}) {
  const light = (opts.mode || 'dark') === 'light';
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: !light ? false : true, alpha: false });
  // 深色多 4 个 pass，主动把 DPR 压到 1.5；浅色没有后期，放到 2。
  const DPR_CAP = light ? 2 : 1.5;
  renderer.setPixelRatio(Math.min(DPR_CAP, devicePixelRatio || 1));
  renderer.setClearColor(light ? 0xf5f1e8 : 0x0b0906, 1);
  renderer.toneMapping = light ? THREE.NeutralToneMapping : THREE.NoToneMapping;
  if (light) {
    renderer.shadowMap.enabled = true;         // 必须在任何 castShadow 之前开
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  }

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(light ? 0xf5f1e8 : 0x0b0906, light ? 0.00058 : 0.00068);
  const camera = new THREE.PerspectiveCamera(46, 1, 1, 9000);

  // ── 环境贴图：金属没有漫反射，没有环境可反射就是一片死黑。
  //    core 里没有 RoomEnvironment，就手摆几片发光面自己烘一张，烘完即弃。
  //    这是「金属度 0.78」能成立的前提，不是可选的美化。 ──
  {
    const env = new THREE.Scene();
    const panel = (x, y, z, w, h, hex, ry) => {
      const m = new THREE.Mesh(
        new THREE.PlaneGeometry(w, h),
        new THREE.MeshBasicMaterial({ color: hex, side: THREE.DoubleSide }));
      m.position.set(x, y, z);
      if (ry) m.rotation.y = ry;
      env.add(m);
      return m;
    };
    const warmK = light ? 0xfff6e6 : 0xfff0d2;
    const coolK = light ? 0xe8edf6 : 0x9db6d8;
    const floorK = light ? 0xd9d2c2 : 0x120e08;
    panel(0, 60, -120, 400, 260, warmK);                    // 主光墙
    panel(0, 60, 120, 400, 260, warmK);                     // 背墙（金属两面都要有东西可反）
    panel(-140, 40, 0, 300, 220, coolK, Math.PI / 2);       // 冷侧墙
    panel(140, 40, 0, 300, 220, coolK, Math.PI / 2);
    panel(0, 140, 0, 420, 420, light ? 0xfffdf7 : 0x2b2113).rotation.x = -Math.PI / 2;  // 顶
    panel(0, -80, 0, 420, 420, floorK).rotation.x = -Math.PI / 2;                       // 地
    const pmrem = new THREE.PMREMGenerator(renderer);
    pmrem.compileEquirectangularShader();
    scene.environment = pmrem.fromScene(env, 0.04).texture;
    scene.environmentIntensity = light ? 0.9 : 2.2;
    pmrem.dispose();
    env.traverse(o => { if (o.geometry) { o.geometry.dispose(); o.material.dispose(); } });
  }

  const days = atlas.days || [];
  const dayIdx = new Map(days.map((d, i) => [d.d, i]));
  const N = days.length;
  const span = Math.max(1, N - 1);

  // ── 布局：x = 第几周，z = 星期几。碑林是一片方阵，不是一条隧道。 ──
  const COLW = 40, ROWW = 34;
  const t0 = N ? Date.UTC(...days[0].d.split('-').map((v, i) => i === 1 ? +v - 1 : +v)) : 0;
  const weekOf = iso => {
    const t = Date.UTC(...iso.split('-').map((v, i) => i === 1 ? +v - 1 : +v));
    return Math.floor((t - t0) / 604800000);
  };
  const wdOf = iso => (new Date(iso + 'T00:00:00Z').getUTCDay() + 6) % 7;
  const weeks = N ? weekOf(days[N - 1].d) + 1 : 1;
  const HALLW = weeks * COLW;

  // ── 碑柱 ──
  const geo = steleGeometry();
  const aGold = new Float32Array(N), aChip = new Float32Array(N), aTopic = new Float32Array(N * 3);
  const mat = giltShader(new THREE.MeshStandardMaterial({
    metalness: light ? 0.08 : 0.42,
    roughness: light ? 0.60 : 0.42,
    emissive: 0x000000,
  }), {
    uGlow: { value: light ? 0.0 : 1.05 },
    uGold: { value: new THREE.Color(light ? 0x8a6512 : 0xd9a54d) },
    uBase: { value: new THREE.Color(light ? 0xe8e2d4 : 0x8d7752) },
  });

  const stele = new THREE.InstancedMesh(geo, mat, Math.max(1, N));
  stele.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  if (light) { stele.castShadow = true; stele.receiveShadow = true; }

  const M = new THREE.Matrix4(), Q = new THREE.Quaternion();
  const P = new THREE.Vector3(), S = new THREE.Vector3();
  const col = new THREE.Color();
  const baseScale = new Float32Array(N);
  const rand = rng(N * 7919 + 13);
  let lastIdx = -1;

  days.forEach((d, i) => {
    const human = d.human || 0, all = d.n || 1;
    const tok = (d.tok_in || 0) + (d.tok_out || 0);
    const h = 46 + 38 * Math.sqrt(human);
    const w = Math.min(COLW * 0.66, 12 + 2.8 * Math.log10(tok + 1));
    baseScale[i] = h;
    P.set(weekOf(d.d) * COLW - HALLW / 2, 0, wdOf(d.d) * ROWW - ROWW * 3);
    S.set(w, h, w);
    Q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), (rand() - 0.5) * 0.05);
    M.compose(P, Q, S);
    stele.setMatrixAt(i, M);

    aGold[i] = all ? human / all : 0;
    // 报错最密的日子在顶角崩一个缺口 —— 伤在器物上看得见
    aChip[i] = (d.errors || 0) / Math.max(1, all) > 0.6 ? 1 : 0;
    const tp = Object.entries(d.topics || {}).sort((a, b) => b[1] - a[1])[0];
    col.setHex(tp ? (TOPIC_HEX[tp[0]] ?? FALLBACK_TOPIC) : FALLBACK_TOPIC);
    if (light) col.multiplyScalar(0.62);        // 浅色下嵌片压暗，否则在白玉上发飘
    aTopic[i * 3] = col.r; aTopic[i * 3 + 1] = col.g; aTopic[i * 3 + 2] = col.b;
    if (d.d === (atlas.meta && atlas.meta.last_day)) lastIdx = i;
  });
  geo.setAttribute('aGold', new THREE.InstancedBufferAttribute(aGold, 1));
  geo.setAttribute('aChip', new THREE.InstancedBufferAttribute(aChip, 1));
  geo.setAttribute('aTopic', new THREE.InstancedBufferAttribute(aTopic, 3));
  stele.instanceMatrix.needsUpdate = true;
  stele.count = N;
  scene.add(stele);

  // ── 倒影：同一批柱翻过来再画一遍。它不承载数据，
  //    它的职责是把「抛光石地面」这句材质谎话圆上。成本 = 1 次 draw call。 ──
  let mirror = null;
  if (!light) {
    const mmat = mat.clone();
    giltShader(mmat, {
      uGlow: { value: 0.55 },
      uGold: { value: new THREE.Color(0xd9a54d) },
      uBase: { value: new THREE.Color(0x4a3e2e) },
    });
    mmat.transparent = true; mmat.opacity = 0.14; mmat.depthWrite = false;
    mmat.polygonOffset = true; mmat.polygonOffsetFactor = 1;
    mirror = new THREE.InstancedMesh(geo, mmat, Math.max(1, N));
    mirror.count = N;
    mirror.instanceMatrix = stele.instanceMatrix;
    mirror.scale.y = -1;
    mirror.renderOrder = -1;
    scene.add(mirror);
  }

  // ── 地面 ──
  const groundMat = new THREE.MeshStandardMaterial({
    color: light ? 0xe9e3d5 : 0x151109,
    metalness: light ? 0.0 : 0.42,
    roughness: light ? 0.85 : 0.32,
  });
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(HALLW + 1600, 4200), groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.5;
  if (light) ground.receiveShadow = true;
  scene.add(ground);

  // ── 台基（每周一条低台，merge 成一个 mesh）与月界石 ──
  const plinths = new THREE.Group();
  {
    const pg = new THREE.BoxGeometry(COLW * 0.82, 5, ROWW * 6.4);
    const pm = new THREE.MeshStandardMaterial({
      color: light ? 0xded6c4 : 0x1c1710, metalness: light ? 0 : 0.3, roughness: 0.7,
    });
    const inst = new THREE.InstancedMesh(pg, pm, Math.max(1, weeks));
    for (let w = 0; w < weeks; w++) {
      P.set(w * COLW - HALLW / 2, -3, ROWW * 0.5);
      S.set(1, 1, 1); Q.identity();
      M.compose(P, Q, S);
      inst.setMatrixAt(w, M);
    }
    inst.count = weeks;
    if (light) inst.receiveShadow = true;
    plinths.add(inst);
  }
  scene.add(plinths);

  // ── 金缮裂缝：同一个问题被反复问过的那些天，用金线在地面连起来 ──
  const seams = new THREE.Group();
  {
    const reps = ((atlas.lessons || {}).repeats || []).slice(0, 22);
    const verts = [];
    for (const r of reps) {
      const a = dayIdx.get(r.first), b = dayIdx.get(r.last);
      if (a == null || b == null || a === b) continue;
      const wA = weekOf(days[a].d) * COLW - HALLW / 2, zA = wdOf(days[a].d) * ROWW - ROWW * 3;
      const wB = weekOf(days[b].d) * COLW - HALLW / 2, zB = wdOf(days[b].d) * ROWW - ROWW * 3;
      const half = Math.min(6, 1.1 + Math.sqrt(r.n || 1) * 0.9);   // 宽度 = 被问过几遍
      const dx = wB - wA, dz = zB - zA, len = Math.hypot(dx, dz) || 1;
      const nx = -dz / len * half, nz = dx / len * half;
      verts.push(
        wA + nx, 0.2, zA + nz, wB + nx, 0.2, zB + nz, wB - nx, 0.2, zB - nz,
        wA + nx, 0.2, zA + nz, wB - nx, 0.2, zB - nz, wA - nx, 0.2, zA - nz,
      );
    }
    if (verts.length) {
      const sg = new THREE.BufferGeometry();
      sg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(verts), 3));
      sg.computeVertexNormals();
      const sm = new THREE.MeshBasicMaterial({
        color: light ? 0x8a6512 : 0xd9a54d,
        transparent: true, opacity: light ? 0.32 : 0.55, depthWrite: false,
      });
      seams.add(new THREE.Mesh(sg, sm));
    }
  }
  scene.add(seams);

  // ── 布光：三点。浅色下 key 投影，深色下靠倒影和雾撑深度。 ──
  const amb = new THREE.AmbientLight(light ? 0xfff8ea : 0x3d3122, light ? 1.5 : 1.7);
  scene.add(amb);
  const key = new THREE.DirectionalLight(light ? 0xfff4e0 : 0xffdfae, light ? 2.1 : 3.2);
  key.position.set(HALLW * 0.28, 900, 640);
  if (light) {
    key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    key.shadow.camera.near = 200; key.shadow.camera.far = 2600;
    const e = Math.max(700, HALLW * 0.7);
    key.shadow.camera.left = -e; key.shadow.camera.right = e;
    key.shadow.camera.top = e; key.shadow.camera.bottom = -e;
  }
  scene.add(key);
  const rim = new THREE.DirectionalLight(light ? 0xdfe6f2 : 0x9fb6d8, light ? 0.5 : 1.1);
  rim.position.set(-HALLW * 0.3, 320, -900);
  scene.add(rim);

  // ── 相机：摇臂。绕着一座固定的碑林转与压低，永远不进队列内部。 ──
  const cam = { p: 0, tp: 0, focus: -1, drift: 0 };
  const look = new THREE.Vector3();
  function place() {
    const p = cam.p;
    const yaw = -1.28 + 0.86 * p + Math.sin(cam.drift) * 0.035;
    const h = 214 - 96 * p;
    const dist = 520 - 150 * p;
    // 焦点：默认厅心缓移向最新一列；flyToDay 时锁到那根柱
    let fx = -HALLW / 2 + HALLW * (0.32 + 0.62 * p);
    if (cam.focus >= 0 && days[cam.focus]) fx = weekOf(days[cam.focus].d) * COLW - HALLW / 2;
    look.set(fx, 92, 0);
    camera.position.set(fx + Math.sin(yaw) * dist, h + 108, Math.cos(yaw) * dist);
    camera.lookAt(look);
  }

  // ── 后期：手写 4 pass。core-only 的 three 没有 EffectComposer。 ──
  const fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const fsGeo = new THREE.PlaneGeometry(2, 2);
  const fsScene = new THREE.Scene();
  const fsQuad = new THREE.Mesh(fsGeo, null);
  fsScene.add(fsQuad);
  let rtMain = null, rtA = null, rtB = null, post = null;

  function makeRT(w, h, half) {
    const t = new THREE.WebGLRenderTarget(Math.max(2, w), Math.max(2, h), {
      minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter,
      type: half ? THREE.HalfFloatType : THREE.UnsignedByteType,
      depthBuffer: half,
    });
    return t;
  }
  function buildPost(w, h) {
    disposePost();
    const halfOK = !!renderer.capabilities.isWebGL2;   // 不支持就退 8bit，阈值同步降
    rtMain = makeRT(w, h, halfOK);
    rtA = makeRT(w >> 2, h >> 2, false);
    rtB = makeRT(w >> 2, h >> 2, false);
    const TH = halfOK ? 1.0 : 0.82;
    post = {
      bright: new THREE.ShaderMaterial({
        uniforms: { tD: { value: null }, uTh: { value: TH } },
        vertexShader: FS_VERT,
        fragmentShader: `varying vec2 vUv; uniform sampler2D tD; uniform float uTh;
          void main(){ vec3 c = texture2D(tD, vUv).rgb;
            gl_FragColor = vec4(max(c - uTh, 0.0), 1.0); }`,
      }),
      blur: new THREE.ShaderMaterial({
        uniforms: { tD: { value: null }, uDir: { value: new THREE.Vector2(1, 0) } },
        vertexShader: FS_VERT,
        fragmentShader: `varying vec2 vUv; uniform sampler2D tD; uniform vec2 uDir;
          void main(){
            vec3 s = vec3(0.0);
            float wts[5]; wts[0]=0.227; wts[1]=0.194; wts[2]=0.121; wts[3]=0.054; wts[4]=0.016;
            s += texture2D(tD, vUv).rgb * wts[0];
            for (int i = 1; i < 5; i++) {
              vec2 o = uDir * float(i);
              s += texture2D(tD, vUv + o).rgb * wts[i];
              s += texture2D(tD, vUv - o).rgb * wts[i];
            }
            gl_FragColor = vec4(s, 1.0); }`,
      }),
      comp: new THREE.ShaderMaterial({
        uniforms: {
          tD: { value: null }, tB: { value: null },
          uT: { value: 0 }, uGrain: { value: 0.012 },
        },
        vertexShader: FS_VERT,
        fragmentShader: `varying vec2 vUv; uniform sampler2D tD; uniform sampler2D tB;
          uniform float uT; uniform float uGrain;
          vec3 aces(vec3 x){
            return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14), 0.0, 1.0);
          }
          float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
          void main(){
            vec3 c = texture2D(tD, vUv).rgb + texture2D(tB, vUv).rgb * 0.55;
            c = aces(c);
            float r = distance(vUv, vec2(0.5));
            c *= smoothstep(0.95, 0.35, r) * 0.35 + 0.65;
            c += (h21(vUv * 900.0 + uT) - 0.5) * uGrain;
            gl_FragColor = vec4(c, 1.0); }`,
      }),
    };
  }
  function disposePost() {
    for (const t of [rtMain, rtA, rtB]) if (t) t.dispose();
    if (post) for (const k of Object.keys(post)) post[k].dispose();
    rtMain = rtA = rtB = post = null;
  }

  // ── 降级梯：只降不升，防振荡。档位记 sessionStorage，下次直达。 ──
  const TIER_KEY = 'atlas.gilt.tier.v1';
  let tier = Math.max(0, Math.min(3, +(sessionStorage.getItem(TIER_KEY) || 0)));
  let fpsAcc = 0, fpsN = 0, fpsClock = 0;
  function applyTier() {
    renderer.setPixelRatio(Math.min(
      [DPR_CAP, 1.25, 1, 1][tier], devicePixelRatio || 1));
    if (post) post.comp.uniforms.uGrain.value = tier >= 1 ? 0 : 0.012;
    if (mirror) mirror.visible = tier < 2;
    resize();
  }
  function watchFps(dt) {
    if (light || tier >= 3) return;
    fpsAcc += dt; fpsN++; fpsClock += dt;
    if (fpsClock < 2000) return;
    const fps = 1000 / (fpsAcc / Math.max(1, fpsN));
    fpsAcc = fpsN = fpsClock = 0;
    const want = fps < 38 ? 3 : fps < 45 ? 2 : fps < 50 ? 1 : tier;
    if (want > tier) { tier = want; sessionStorage.setItem(TIER_KEY, String(tier)); applyTier(); }
  }

  let W = 2, H = 2, disposed = false;
  function resize() {
    const r = canvas.getBoundingClientRect();
    W = Math.max(120, Math.round(r.width) || canvas.clientWidth || innerWidth);
    H = Math.max(120, Math.round(r.height) || canvas.clientHeight || innerHeight);
    renderer.setSize(W, H, false);
    camera.aspect = W / H;
    // 窄屏没有「让开左侧」这回事，偏移只在宽屏生效
    if (W >= 900) camera.setViewOffset(W * 1.62, H, 0, 0, W, H);
    else camera.clearViewOffset();
    camera.updateProjectionMatrix();
    if (!light && tier < 3) {
      const dpr = renderer.getPixelRatio();
      buildPost(Math.round(W * dpr), Math.round(H * dpr));
    } else disposePost();
  }

  function frame(dt) {
    if (disposed) return;
    cam.p += (cam.tp - cam.p) * 0.06;
    cam.drift += dt * 0.00004;
    place();
    if (light || !post || tier >= 3) {
      renderer.setRenderTarget(null);
      renderer.render(scene, camera);
    } else {
      renderer.setRenderTarget(rtMain);
      renderer.clear();
      renderer.render(scene, camera);
      fsQuad.material = post.bright; post.bright.uniforms.tD.value = rtMain.texture;
      renderer.setRenderTarget(rtA); renderer.render(fsScene, fsCam);
      const px = 1 / rtA.width, py = 1 / rtA.height;
      fsQuad.material = post.blur;
      post.blur.uniforms.tD.value = rtA.texture; post.blur.uniforms.uDir.value.set(px, 0);
      renderer.setRenderTarget(rtB); renderer.render(fsScene, fsCam);
      post.blur.uniforms.tD.value = rtB.texture; post.blur.uniforms.uDir.value.set(0, py);
      renderer.setRenderTarget(rtA); renderer.render(fsScene, fsCam);
      fsQuad.material = post.comp;
      post.comp.uniforms.tD.value = rtMain.texture;
      post.comp.uniforms.tB.value = rtA.texture;
      post.comp.uniforms.uT.value += dt * 0.001;
      renderer.setRenderTarget(null); renderer.render(fsScene, fsCam);
    }
    watchFps(dt);
  }

  // ── 拾取：hover 哪根柱。Raycaster 对 InstancedMesh 会给出 instanceId。 ──
  const ray = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  function pick(clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    ndc.set(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hit = ray.intersectObject(stele, false)[0];
    return hit && hit.instanceId != null ? hit.instanceId : -1;
  }

  resize();
  applyTier();
  place();

  return {
    resize, frame, pick,
    /** 0 = 最早的机位，1 = 压到最低最近。滚动进度直接喂这里。 */
    flyTo(t) { cam.tp = Math.max(0, Math.min(1, t)); },
    at() { return cam.p; },
    dayOf(i) { return days[i] ? days[i].d : null; },
    dayInfo(i) { return days[i] || null; },
    dayAt() {
      if (cam.focus >= 0 && days[cam.focus]) return days[cam.focus].d;
      return days[Math.round(cam.p * span)] ? days[Math.round(cam.p * span)].d : (days[N - 1] || {}).d;
    },
    /** 把某一天推到镜头前。找不到就停在时间上最接近的一天。 */
    flyToDay(iso) {
      if (!N) return;
      let i = dayIdx.has(iso) ? dayIdx.get(iso) : days.findIndex(d => d.d >= iso);
      if (i < 0) i = N - 1;
      cam.focus = i;
      cam.tp = span ? i / span : 0;
    },
    releaseFocus() { cam.focus = -1; },
    stats: { stele: N, weeks, seams: seams.children.length, tier: () => tier, days: N },
    dispose() {
      disposed = true;
      geo.dispose(); mat.dispose();
      if (mirror) mirror.material.dispose();
      ground.geometry.dispose(); groundMat.dispose();
      plinths.children.forEach(c => { c.geometry.dispose(); c.material.dispose(); });
      seams.children.forEach(c => { c.geometry.dispose(); c.material.dispose(); });
      if (scene.environment) scene.environment.dispose();
      fsGeo.dispose();
      disposePost();
      renderer.dispose();
    },
  };
}
