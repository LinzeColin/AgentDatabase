import { esc, S, toggleRail } from '../../core/app.js';
export const css = 'themes/glass/shell.css';

export function chrome(mount) {
  mount.innerHTML = `
    <canvas id="fxlayer"></canvas>
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
      <main id="view"></main>
      <footer id="foot"></footer>
    </div>`;
  const t = mount.querySelector('#railtog');
  t.textContent = S.railOpen ? '◀' : '▶';
  t.onclick = () => { toggleRail(); t.textContent = S.railOpen ? '◀' : '▶'; };
}
