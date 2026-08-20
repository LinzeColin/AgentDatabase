import { esc, S, toggleRail } from '../../core/app.js';
export const css = 'themes/console/shell.css';

export function chrome(mount) {
  mount.innerHTML = `
    <canvas id="fxlayer"></canvas>
    <div id="shell">
      <aside id="rail">
        <div class="brandrow">
          <span class="brand">MEMORY ATLAS</span>
          <button id="railtog" title="折叠／展开侧栏">◀</button>
        </div>
        <nav id="nav"></nav>
        <div id="tools"></div>
        <div id="railfoot"></div>
      </aside>
      <main id="view"></main>
      <footer id="foot"></footer>
    </div>
    <div id="statusline">
      <span id="stamp"></span><span style="flex:1"></span>
      <span><b>[</b> 折叠侧栏</span><span><b>d</b> 深浅</span><span><b>t</b> 主题</span>
    </div>`;
  const t = mount.querySelector('#railtog');
  t.textContent = S.railOpen ? '◀' : '▶';
  t.onclick = () => { toggleRail(); t.textContent = S.railOpen ? '◀' : '▶'; };
}

/** 键盘优先是这套主题的交互主张。 */
export function bindKeys(views, { go, setTheme, cycleTheme }) {
  const onKey = e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.isContentEditable)) return;
    if (e.key === '[') { toggleRail();
      const b = document.getElementById('railtog'); if (b) b.textContent = S.railOpen ? '◀' : '▶';
      e.preventDefault(); return; }
    if (e.key === 'd') { setTheme(null, S.mode === 'dark' ? 'light' : 'dark'); e.preventDefault(); }
    if (e.key === 't') { cycleTheme(); e.preventDefault(); }
  };
  addEventListener('keydown', onKey);
  return () => removeEventListener('keydown', onKey);
}
