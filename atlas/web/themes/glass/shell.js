import { esc } from '../../core/app.js';
export const css = 'themes/glass/shell.css';
export function chrome(mount) {
  mount.innerHTML = `
    <canvas id="fxlayer"></canvas>
    <div id="shell">
      <header id="topbar">
        <div class="brand">Memory Atlas</div>
        <nav id="nav"></nav>
        <div id="tools"></div>
        <div id="stamp"></div>
      </header>
      <main id="view"></main>
      <footer id="foot"></footer>
    </div>`;
}
export function navMarkup(views) {
  return views.map(([v, l]) => `<button data-v="${v}">${esc(l)}</button>`).join('');
}
