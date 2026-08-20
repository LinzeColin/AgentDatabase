import { esc, S, toggleRail, reduced } from '../../core/app.js';
export const css = 'themes/nebula/shell.css';

let cosmos = null, raf = 0, onScroll = null, onResize = null, last = 0;

// 每次启动发一个号。startCosmos 是异步的（要 import three.js），
// 而 applyTheme 可能在它落地之前又跑一遍 —— 首屏恢复上次主题 + 用户手动切
// 就是这个时序。两次交错的后果实测过：两套场景同时存在，
// 模块里的 cosmos 指向已经脱离 DOM 的那一份，屏幕上跑的是另一份 ——
// 于是 flyToDay 全部落空（HUD 停在 2026-07-27 不动），
// 而作废那份的 rAF 还在后台烧显卡，每切一次主题泄一份。
// 号对不上就整份作废，这是唯一可靠的判据。
let gen = 0;

// 相机默认由滚动开。但「回放」和「一天」是视图自己在开镜头 ——
// 两个司机同时踩油门的后果实测过：按下播放跳到 W22，随手滚一下页面，
// 镜头立刻被拉回最新那天，回放等于失效。所以接管期间把滚动那条线断开。
let held = false;

export function chrome(mount) {
  mount.innerHTML = `
    <canvas id="cosmos"></canvas>
    <div id="shell">
      <aside id="rail">
        <div class="brandrow">
          <span class="brand">Memory Atlas</span>
          <button id="railtog" title="折叠／展开">◀</button>
        </div>
        <nav id="nav"></nav>
        <div id="tools"></div>
        <div id="railfoot"></div>
      </aside>
      <div id="stamp"></div>
      <div id="hud"></div>
      <main id="view"></main>
      <footer id="foot"></footer>
    </div>`;
  const t = mount.querySelector('#railtog');
  t.textContent = S.railOpen ? '◀' : '▶';
  t.onclick = () => { toggleRail(); t.textContent = S.railOpen ? '◀' : '▶'; setTimeout(fit, 520); };
  startCosmos();
}

function fit() { if (cosmos) cosmos.resize(); }

async function startCosmos() {
  stopCosmos();               // 先收摊（它会 gen++ 让在途的那份作废）
  const my = ++gen;           // 再领号 —— 顺序反了就会把自己也作废掉
  const cv = document.getElementById('cosmos');
  if (!cv || !S.atlas) return;
  const { buildCosmos } = await import('../../core/cosmos.js');
  if (my !== gen) return;                       // 等 import 的工夫又切了一次，这份作废
  cosmos = buildCosmos(cv, S.atlas, { mode: S.mode });
  // 样式落地后再量一次：首帧量到的可能还是 canvas 的默认 300×150。
  requestAnimationFrame(() => { if (my === gen && cosmos) cosmos.resize(); });
  const hud = document.getElementById('hud');

  // 滚动即穿越：页面滚到哪，相机就飞到那一段时间。
  // 这是这套主题的主张 —— 时间是一个可以飞进去的方向，不是一根横条。
  onScroll = () => {
    if (held || !cosmos) return;  // 视图正在开镜头，滚动不抢方向盘
    const max = Math.max(1, document.body.scrollHeight - innerHeight);
    const p = Math.min(1, Math.max(0, scrollY / max));
    cosmos.flyTo(1 - p);          // 往下滚 = 往回飞
  };
  addEventListener('scroll', onScroll, { passive: true });
  onResize = () => fit();
  addEventListener('resize', onResize);

  const st = cosmos.stats;
  const tick = now => {
    if (my !== gen || !cosmos) return;           // 已经被下一份接替，安静退出
    const dt = Math.min(80, now - (last || now)); last = now;
    cosmos.frame(reduced() ? 0 : dt);
    if (hud) {
      hud.innerHTML = `飞到 <b>${esc(cosmos.dayAt() || '—')}</b><br>
        ${st.stars} 颗星 · ${st.clouds} 团星云 · ${st.days} 天`;
    }
    raf = requestAnimationFrame(tick);
  };
  raf = requestAnimationFrame(tick);
}

function stopCosmos() {
  gen++;                                         // 让在途的那一份自己作废
  cancelAnimationFrame(raf); raf = 0;
  if (onScroll) { removeEventListener('scroll', onScroll); onScroll = null; }
  if (onResize) { removeEventListener('resize', onResize); onResize = null; }
  if (cosmos) { cosmos.dispose(); cosmos = null; }
}

/** 视图可以直接把某一天推到镜头前 —— 点日历上的一格，星图就飞过去。 */
export function flyToDay(iso) { if (cosmos) cosmos.flyToDay(iso); }

/** 接管／交还相机。接管的视图必须在 dispose 里交还，否则下一屏滚动就死了。 */
export function holdCamera(on) { held = !!on; }

/** 主题切走时必须把 WebGL 场景收掉，否则显卡资源会一直占着。 */
export function bindKeys() { return () => { held = false; stopCosmos(); }; }
