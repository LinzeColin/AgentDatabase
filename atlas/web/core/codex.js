// core/codex.js —— 鎏金主题的三维：**一本册子的书口（fore-edge）**。
//
// 和星云那套的分工是硬的：
//   星云的三维 = 一片**可以飞进去的空间**，透视相机，滚动就是穿行。
//   鎏金的三维 = 一件**可以翻动的物件**，正交相机，翻页就是掠过金箔。
// 两者共用 three.js，但从相机类型到交互隐喻没有一处相同 —— 这才叫两套主题。
//
// **每一片金页都是一天**：
//   沿书口排开的顺序 = 时间顺序
//   页的厚度         = 那天你自己开口了多少次（人的量，不是机器的量）
//   页的外凸         = 那天的 token 量（对数压缩，否则一天独吞整本书）
//   页面的粗糙度     = 那天工具失败的密度（越糙越哑光，磕碰过的页不反光）
// 数据是空的，书口就该是平的 —— 不做假的凹凸。
//
// 一条实测出来的硬规矩：**金属没有环境贴图就是死黑的**。
// 所以这里必须自己烘一张 PMREM，不能指望灯光把金属照亮。
// （EffectComposer 不在 vendor 里，所以也没有 bloom —— 靠材质本身立住。）

import * as THREE from '../vendor/three.module.min.js';

export function buildCodex(canvas, atlas, opts = {}) {
  const light = (opts.mode || 'dark') === 'light';
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(2, devicePixelRatio || 1));
  renderer.setClearColor(0x000000, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = light ? 1.2 : 1.35;

  const scene = new THREE.Scene();

  // ── 自己烘环境：六块自发光面片。没有它，金属渲出来是纯黑的。 ──
  {
    const env = new THREE.Scene();
    const panel = (x, y, z, w, h, hex, rx = 0, ry = 0) => {
      const m = new THREE.Mesh(
        new THREE.PlaneGeometry(w, h),
        new THREE.MeshBasicMaterial({ color: hex, side: THREE.DoubleSide }));
      m.position.set(x, y, z);
      if (rx) m.rotation.x = rx;
      if (ry) m.rotation.y = ry;
      env.add(m);
      return m;
    };
    const warm = light ? 0xfff8ec : 0xffeecb;
    const cool = light ? 0xeef2fb : 0x8fa6c8;
    panel(0, 30, -160, 520, 300, warm);                       // 主光墙（暖，来自读书人那一侧）
    panel(0, 30, 160, 520, 300, light ? 0xfaf6ec : 0x3a2f1c); // 背墙：两面都要有东西可反
    panel(-190, 20, 0, 360, 280, cool, 0, Math.PI / 2);       // 冷侧墙给金一点层次
    panel(190, 20, 0, 360, 280, cool, 0, Math.PI / 2);
    panel(0, 175, 0, 520, 520, light ? 0xffffff : 0x4a3a20).rotation.x = -Math.PI / 2;
    panel(0, -120, 0, 520, 520, light ? 0xded5c0 : 0x0d0a05).rotation.x = -Math.PI / 2;
    const pmrem = new THREE.PMREMGenerator(renderer);
    pmrem.compileEquirectangularShader();
    scene.environment = pmrem.fromScene(env, 0.02).texture;   // 0.05 会触发 sigmaRadians 裁剪告警
    scene.environmentIntensity = light ? 1.2 : 2.8;
    pmrem.dispose();
    env.traverse(o => { if (o.geometry) { o.geometry.dispose(); o.material.dispose(); } });
  }

  // 正交相机：册子是一个物件，不是一个可以走进去的空间。透视会让它变成隧道。
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -800, 1600);
  // 看向书口**上方**的一点：这样册子会落在画面下缘，
  // 把上半屏整块让给正文。三维在这套主题里是配角材质，不是舞台。
  // 书口**竖着立在画面右缘**，正文在左。
  // 试过让它横躺在下缘：那条带正好是页码条的位置，两者互相吃 ——
  // 要么书口被挡住，要么翻页按钮读不出来。竖立之后两者永不相交。
  // 相机中心要在书口**左边**，书口才会出现在画面右侧。
  // 反过来写过一版：书口跑到左边压住正文，找了半天以为是渲染没跑。
  camera.position.set(-56, 104, 340);
  camera.lookAt(-224, 24, 0);   // 书口贴在正文右侧之外，露出整叠页而不压字

  const days = (atlas.days || []).filter(d => d && d.d);
  const N = Math.max(1, days.length);
  const maxHuman = Math.max(1, ...days.map(d => d.human || 0));
  const maxTok = Math.max(1, ...days.map(d => (d.tok_in || 0) + (d.tok_cache_r || 0)));
  const maxErr = Math.max(1, ...days.map(d => d.errors_tool || 0));

  // ── 书口：一天一片金页 ──
  const BOOK_W = 300;                       // 书口总长
  const step = BOOK_W / N;
  const geo = new THREE.BoxGeometry(1, 1, 1);
  const mat = new THREE.MeshStandardMaterial({
    color: light ? 0xb98f37 : 0xd8b35e,
    metalness: 0.88,
    roughness: 0.3,
    envMapIntensity: light ? 1.2 : 2.4,
    // **自发光地板**。金属只靠环境反射时，环境稍暗一点整块就是死黑的 ——
    // 而「渲成黑」和「没渲」在屏幕上长得一模一样，查起来极贵（这一版查了很久）。
    // 给一个不依赖任何光源的下限：哪怕环境全灭，书口仍然看得见是金的。
    emissive: new THREE.Color(light ? 0x3a2a08 : 0x6b4f16),
    emissiveIntensity: light ? 0.4 : 1.15,
  });
  // 每片页自己的粗糙度：磕碰过的页不反光。逐实例改 roughness 要注入 shader，
  // PointsMaterial 那套注入法在这里同样适用。
  const aRough = new Float32Array(N);
  const aWarm = new Float32Array(N);
  mat.onBeforeCompile = sh => {
    sh.vertexShader = 'attribute float aRough;\nattribute float aWarm;\nvarying float vR;\nvarying float vW;\n'
      + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n\tvR = aRough;\n\tvW = aWarm;');
    sh.fragmentShader = 'varying float vR;\nvarying float vW;\n'
      + sh.fragmentShader
        .replace('#include <roughnessmap_fragment>',
          '#include <roughnessmap_fragment>\n\troughnessFactor = clamp(roughnessFactor + vR, 0.05, 0.95);')
        // 主题色偏移：越靠近「今天」越亮，最早那批发暗 —— 时间在金上留下的氧化
        .replace('#include <color_fragment>',
          '#include <color_fragment>\n\tdiffuseColor.rgb *= mix(0.55, 1.15, vW);');
  };

  const leaves = new THREE.InstancedMesh(geo, mat, N);
  leaves.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const m4 = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const pos = new THREE.Vector3();
  const scl = new THREE.Vector3();
  for (let i = 0; i < N; i++) {
    const d = days[i] || {};
    const human = d.human || 0;
    const tok = (d.tok_in || 0) + (d.tok_cache_r || 0);
    // 厚度 = 你开口的次数；外凸 = token（取对数，否则 15.6B 那天独吞整本书）
    const thick = step * (0.34 + 0.66 * (human / maxHuman));
    const out = 20 + 104 * (Math.log10(1 + tok) / Math.log10(1 + maxTok));
    const h = 92;
    pos.set(-BOOK_W / 2 + i * step + step / 2, 0, out / 2 - 30);
    scl.set(Math.max(0.6, thick), h, Math.max(1.2, out));
    q.identity();
    leaves.setMatrixAt(i, m4.compose(pos, q, scl));
    aRough[i] = 0.42 * ((d.errors_tool || 0) / maxErr);      // 磕碰过的页发哑
    aWarm[i] = N > 1 ? i / (N - 1) : 1;
  }
  geo.setAttribute('aRough', new THREE.InstancedBufferAttribute(aRough, 1));
  geo.setAttribute('aWarm', new THREE.InstancedBufferAttribute(aWarm, 1));
  leaves.instanceMatrix.needsUpdate = true;
  scene.add(leaves);

  // 封面与封底：两块暗色板，把书口夹住 —— 没有它书口是悬空的一排片
  const boardMat = new THREE.MeshStandardMaterial({
    color: light ? 0x8a7350 : 0x2a2115, metalness: 0.3, roughness: 0.72,
  });
  const board = (x) => {
    const b = new THREE.Mesh(new THREE.BoxGeometry(6, 104, 96), boardMat);
    b.position.set(x, 0, 4);
    scene.add(b);
    return b;
  };
  const boards = [board(-BOOK_W / 2 - 5), board(BOOK_W / 2 + 5)];

  // 读书光：一束沿书口移动的高光。翻页时它跟着走 —— **翻页在物理上被看见**
  const key = new THREE.DirectionalLight(light ? 0xfff6e2 : 0xffe6b0, light ? 1.5 : 2.1);
  key.position.set(-120, 200, 220);
  scene.add(key);
  const readLamp = new THREE.PointLight(0xffd98a, 0, 190, 2);
  scene.add(readLamp);
  scene.add(new THREE.AmbientLight(light ? 0xffffff : 0x2b2418, light ? 0.5 : 0.7));

  const book = new THREE.Group();
  scene.add(book);

  let t = 0, target = 0, tilt = 0, disposed = false;

  function resize() {
    const r = canvas.getBoundingClientRect();
    const w = Math.max(120, Math.round(r.width) || innerWidth);
    const h = Math.max(120, Math.round(r.height) || innerHeight);
    renderer.setSize(w, h, false);
    // 正交视野按**高**定，宽按比例展开 —— 教科书写法。
    // 上一版写成 `Math.max(1, aspect)` 那一串：布局还没落地时 rect 是方的，
    // aspect=1 于是视锥被算成 ±175 而不是 ±311，书口整根被挤出右边界。
    // 屏幕上什么都没有、而 renderer.info 显示 1536 个三角形一直在画 —— 就是这么来的。
    const aspect = (w > 0 && h > 0) ? w / h : 1;
    const half = 150;   // 视野收一点：书口在屏幕上要读得出是「一叠页」，不是一道光
    camera.left = -half * aspect;
    camera.right = half * aspect;
    camera.top = half;
    camera.bottom = -half;
    camera.updateProjectionMatrix();
  }

  function frame(dt) {
    if (disposed) return;
    t += (target - t) * 0.08;
    // 翻页时册子会轻轻侧一下，像手压着书脊。位移很小 —— 金属不该有夸张的晃动。
    tilt += ((target - t) * 2.4 - tilt) * 0.1;
    // z 轴转 90°：书口竖起来，一页一页自上而下排 —— 时间从上往下走，
    // 和左边正文的阅读方向一致。
    leaves.rotation.z = Math.PI / 2;
    leaves.rotation.y = -0.34 + tilt * 0.1;
    leaves.rotation.x = -0.1;
    leaves.position.set(0, 30, 0);
    boards.forEach((b, i) => {
      b.rotation.copy(leaves.rotation);
      b.position.set(0, 30 + (i ? 1 : -1) * (BOOK_W / 2 + 5), 4);
    });
    // 读书光顺着书口上下走：翻页时**在物理上看得见**走到了哪一页。
    // t=0 是第一页（书口顶端），t=1 是最后一页。
    const yi = 30 + BOOK_W / 2 - t * BOOK_W;
    readLamp.position.set(34, yi, 92);
    readLamp.intensity = light ? 260 : 420;
    renderer.render(scene, camera);
  }

  resize();
  // 再补一次：构造时布局可能还没落地，第一次 resize 会拿到一个方形 rect。
  // 这一帧之后的尺寸才是真的。
  requestAnimationFrame(() => { if (!disposed) resize(); });

  return {
    resize, frame,
    /** 0 = 第一页，1 = 最后一页。翻页时由外壳调进来。 */
    turnTo(v) { target = Math.max(0, Math.min(1, v)); },
    at() { return t; },
    stats: { leaves: N, days: days.length },
    /**
     * 排障用。**别删** —— 这一版就是靠它才找到问题的。
     * 症状：屏幕上什么都没有。看起来像「没渲染」，实际上
     * `renderer.info` 一直报 1536 个三角形 —— 一直在画，只是画到了屏幕外，
     * 因为 resize() 在布局落地前跑，把视锥算成了 ±175 而不是 ±311。
     *
     * 另一个配套手法（页面在后台标签时 rAF 不跑、截图抓不到 WebGL 画布）：
     *   s.frame(16); 立刻 drawImage 到一张 2D canvas，再 toDataURL 贴成 <img>。
     * 这样渲染结果被固化成静态图，截图才看得见。
     */
    debug() {
      const b = new THREE.Box3().setFromObject(leaves);
      return {
        calls: renderer.info.render.calls, tris: renderer.info.render.triangles,
        camPos: camera.position.toArray().map(Math.round),
        frustum: [camera.left | 0, camera.right | 0, camera.top | 0, camera.bottom | 0],
        boxMin: b.min.toArray().map(Math.round), boxMax: b.max.toArray().map(Math.round),
        leavesVisible: leaves.visible, count: leaves.count,
        rot: [leaves.rotation.x.toFixed(2), leaves.rotation.y.toFixed(2), leaves.rotation.z.toFixed(2)],
      };
    },
    dispose() {
      disposed = true;
      geo.dispose(); mat.dispose(); boardMat.dispose();
      boards.forEach(b => b.geometry.dispose());
      if (scene.environment) scene.environment.dispose();
      renderer.dispose();
    },
  };
}
