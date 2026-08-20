import { esc, S, toggleRail } from '../../core/app.js';
export const css = 'themes/journal/shell.css';

export function chrome(mount) {
  mount.innerHTML = `
    <canvas id="fxlayer"></canvas>
    <div id="shell">
      <aside id="rail">
        <div class="brandrow">
          <span class="brand">Memory&nbsp;Atlas</span>
          <button id="railtog" title="收起目录">收起</button>
        </div>
        <nav id="nav"></nav>
        <div id="tools"></div>
        <div id="railfoot"></div>
      </aside>
      <header id="masthead">
        <button id="openrail" title="展开目录">目录</button>
        <span class="mt">一个人的三个月，逐日成刊</span>
        <span id="stamp"></span>
      </header>
      <main id="view"></main>
      <footer id="foot"></footer>
    </div>`;
  const t = mount.querySelector('#railtog');
  t.onclick = () => toggleRail();
  mount.querySelector('#openrail').onclick = () => toggleRail();
}
