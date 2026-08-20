import { S, toggleRail } from '../../core/app.js';
export const css = 'themes/daylight/shell.css';

// 白昼没有画布层，也没有 WebGL 场景 —— 它的全部主张是版式。
// 唯一的动态是左轨那条随滚动前进的进度线：告诉你这页读到哪了。
let onScroll = null;

export function chrome(mount) {
  mount.innerHTML = `
    <div id="shell">
      <aside id="rail">
        <div class="brandrow">
          <span class="brand">MEMORY ATLAS</span>
          <button id="railtog" title="折叠／展开">◀</button>
        </div>
        <nav id="nav"></nav>
        <div id="tools"></div>
        <div id="railfoot"></div>
      </aside>
      <div id="stamp"></div>
      <div id="prog"></div>
      <main id="view"></main>
      <footer id="foot"></footer>
    </div>`;
  const t = mount.querySelector('#railtog');
  t.textContent = S.railOpen ? '◀' : '▶';
  t.onclick = () => { toggleRail(); t.textContent = S.railOpen ? '◀' : '▶'; };

  const prog = mount.querySelector('#prog');
  if (!prog.dataset.styled) {
    prog.dataset.styled = '1';
    prog.style.cssText = 'position:fixed;left:0;top:0;height:2px;width:0;background:var(--acc);' +
      'z-index:40;transition:width .12s linear;pointer-events:none';
  }
  onScroll = () => {
    const max = Math.max(1, document.body.scrollHeight - innerHeight);
    prog.style.width = (Math.min(1, Math.max(0, scrollY / max)) * 100).toFixed(2) + '%';
  };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

export function bindKeys() {
  return () => { if (onScroll) { removeEventListener('scroll', onScroll); onScroll = null; } };
}
