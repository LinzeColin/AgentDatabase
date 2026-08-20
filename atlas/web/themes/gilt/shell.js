import { esc, fmt, S, toggleRail, reduced, go } from '../../core/app.js';
export const css = 'themes/gilt/shell.css';

let hall = null, raf = 0, onScroll = null, onResize = null, last = 0;

// 相机默认由滚动开（摇臂：滚动=换机位）。视图要接管就得说一声。
// 这条纪律是从星云那边继承来的：两个司机同时踩油门，回放当场失效。
let held = false;

// 发号作废。startFoundry 是异步的（要 import three.js），而 applyTheme
// 可能在它落地之前又跑一遍 —— 首屏恢复上次主题、紧接着用户手动切就是这个时序。
// 号对不上就整份丢弃，否则会出现两套场景：一套在屏幕上跑，另一套接指令。
let gen = 0;

export function chrome(mount) {
  mount.innerHTML = `
    <canvas id="foundry"></canvas>
    <div id="vignette"></div>
    <div id="ribbon"><i></i></div>
    <div id="shell">
      <aside id="rail">
        <div class="brandrow">
          <span class="brand">Memory Atlas</span>
          <button id="railtog" title="折叠／展开" aria-label="折叠或展开左侧目录">◀</button>
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
  t.onclick = () => { toggleRail(); t.textContent = S.railOpen ? '◀' : '▶'; setTimeout(fit, 560); };
  startFoundry();
}

function fit() { if (hall) hall.resize(); }

async function startFoundry() {
  stopFoundry();                 // 先收摊（它会 gen++ 让在途的作废）
  const my = ++gen;              // 再领号 —— 顺序反了会把自己也作废掉
  const cv = document.getElementById('foundry');
  if (!cv || !S.atlas) return;
  const { buildFoundry } = await import('../../core/foundry.js');
  if (my !== gen) return;
  hall = buildFoundry(cv, S.atlas, { mode: S.mode });
  requestAnimationFrame(() => { if (my === gen && hall) hall.resize(); });

  const hud = document.getElementById('hud');
  const ribbon = document.getElementById('ribbon');
  const bar = ribbon && ribbon.querySelector('i');
  const still = reduced();       // 减少动态偏好：滚动不再带动相机（全屏 3D 跟滚是最典型的眩晕源）

  onScroll = () => {
    const max = Math.max(1, document.body.scrollHeight - innerHeight);
    const p = Math.min(1, Math.max(0, scrollY / max));
    if (bar) bar.style.height = (p * 100).toFixed(2) + '%';
    if (ribbon) markRivets(ribbon, max);
    if (held || still || !hall) return;
    hall.flyTo(p);               // 往下滚 = 机位压低、绕到另一侧，绝不进队列内部
  };
  addEventListener('scroll', onScroll, { passive: true });
  onResize = () => fit();
  addEventListener('resize', onResize);

  // 悬停一根柱：浮出当天的三个数。3D 里的可点性必须用文字宣告，不能只靠光效。
  let hover = -1;
  cv.style.cursor = 'grab';
  cv.onpointermove = e => {
    if (!hall) return;
    const i = hall.pick(e.clientX, e.clientY);
    if (i === hover) return;
    hover = i;
    cv.style.cursor = i >= 0 ? 'pointer' : 'grab';
  };
  cv.onpointerleave = () => { hover = -1; cv.style.cursor = 'grab'; };
  cv.onclick = e => {
    if (!hall) return;
    const i = hall.pick(e.clientX, e.clientY);
    const iso = i >= 0 && hall.dayOf(i);
    if (iso) go('day', iso);
  };

  const st = hall.stats;
  const tick = now => {
    if (my !== gen || !hall) return;
    const dt = Math.min(80, now - (last || now)); last = now;
    hall.frame(reduced() ? 0 : dt);
    if (hud) {
      const info = hover >= 0 ? hall.dayInfo(hover) : null;
      hud.innerHTML = info
        ? `<b>${esc(info.d)}</b>　点开这一天<br>
           你开口 ${info.human} · 机器 ${info.n - info.human} · token ${fmt((info.tok_in || 0) + (info.tok_out || 0))}`
        : `停在 <b>${esc(hall.dayAt() || '—')}</b><br>
           ${st.stele} 根碑 · ${st.weeks} 周 · ${st.seams ? '金缮已补' : '暂无金缮'}`;
    }
    raf = requestAnimationFrame(tick);
  };
  raf = requestAnimationFrame(tick);
  onScroll();
}

/** 目次丝带上的铆钉：每个 sec 一颗，滚过变金。 */
function markRivets(ribbon, max) {
  const secs = [...document.querySelectorAll('#view .sec')];
  let riv = [...ribbon.querySelectorAll('u')];
  if (riv.length !== secs.length) {
    riv.forEach(u => u.remove());
    riv = secs.map(() => {
      const u = document.createElement('u');
      ribbon.appendChild(u);
      return u;
    });
  }
  secs.forEach((s, i) => {
    const top = s.getBoundingClientRect().top + scrollY;
    riv[i].style.top = ((top / (max + innerHeight)) * 100).toFixed(2) + '%';
    if (top - scrollY < innerHeight * 0.5) riv[i].setAttribute('data-on', '1');
    else riv[i].removeAttribute('data-on');
  });
}

function stopFoundry() {
  gen++;
  cancelAnimationFrame(raf); raf = 0;
  if (onScroll) { removeEventListener('scroll', onScroll); onScroll = null; }
  if (onResize) { removeEventListener('resize', onResize); onResize = null; }
  if (hall) { hall.dispose(); hall = null; }
}

/** 视图可以直接把某一天推到镜头前 —— 点日历上的一格，碑林就摇过去。 */
export function flyToDay(iso) { if (hall) hall.flyToDay(iso); }

/** 接管／交还相机。接管的视图必须在 dispose 里交还，否则下一屏滚动就死了。 */
export function holdCamera(on) {
  held = !!on;
  if (!on && hall) hall.releaseFocus();
}

export function bindKeys() {
  return () => { held = false; stopFoundry(); };
}
