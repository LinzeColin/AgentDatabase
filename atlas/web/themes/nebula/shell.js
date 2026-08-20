import { esc, S, toggleRail, reduced } from '../../core/app.js';
export const css = 'themes/nebula/shell.css';

let cosmos = null, raf = 0, onScroll = null, onResize = null, last = 0;

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
  stopCosmos();
  const cv = document.getElementById('cosmos');
  if (!cv || !S.atlas) return;
  const { buildCosmos } = await import('../../core/cosmos.js');
  cosmos = buildCosmos(cv, S.atlas, { mode: S.mode });
  // 样式落地后再量一次：首帧量到的可能还是 canvas 的默认 300×150。
  requestAnimationFrame(() => { if (cosmos) cosmos.resize(); });
  const hud = document.getElementById('hud');

  // 滚动即穿越：页面滚到哪，相机就飞到那一段时间。
  // 这是这套主题的主张 —— 时间是一个可以飞进去的方向，不是一根横条。
  onScroll = () => {
    const max = Math.max(1, document.body.scrollHeight - innerHeight);
    const p = Math.min(1, Math.max(0, scrollY / max));
    cosmos.flyTo(1 - p);          // 往下滚 = 往回飞
  };
  addEventListener('scroll', onScroll, { passive: true });
  onResize = () => fit();
  addEventListener('resize', onResize);

  const st = cosmos.stats;
  const tick = now => {
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
  cancelAnimationFrame(raf); raf = 0;
  if (onScroll) { removeEventListener('scroll', onScroll); onScroll = null; }
  if (onResize) { removeEventListener('resize', onResize); onResize = null; }
  if (cosmos) { cosmos.dispose(); cosmos = null; }
}

/** 视图可以直接把某一天推到镜头前 —— 点日历上的一格，星图就飞过去。 */
export function flyToDay(iso) { if (cosmos) cosmos.flyToDay(iso); }

/** 主题切走时必须把 WebGL 场景收掉，否则显卡资源会一直占着。 */
export function bindKeys() { return () => stopCosmos(); }
