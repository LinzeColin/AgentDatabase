// 控制台主题的外壳：左命令轨 + 底部状态行 + 键盘优先。
import { S, esc, VIEW_LIST } from '../../core/app.js';

export const css = 'themes/console/shell.css';

export function chrome(mount) {
  mount.innerHTML = `
    <canvas id="fxlayer"></canvas>
    <div id="shell">
      <aside id="topbar">
        <div class="brand">MEMORY ATLAS</div>
        <nav id="nav"></nav>
        <div id="tools"></div>
      </aside>
      <main id="view"></main>
      <footer id="foot"></footer>
    </div>
    <div id="statusline">
      <span id="stamp"></span>
      <span style="flex:1"></span>
      <span><b>1-9</b> 切视图</span><span><b>d</b> 深浅</span><span><b>t</b> 主题</span>
    </div>`;
}

export function navMarkup(views) {
  return views.map(([v, l], i) =>
    `<button data-v="${v}" data-k="${i < 9 ? i + 1 : ' '}">${esc(l)}</button>`).join('');
}

/** 键盘优先是这套主题的交互主张：数字键切视图，d 切明暗，t 轮换主题。 */
export function bindKeys(views, { go, setTheme, cycleTheme }) {
  const onKey = e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.isContentEditable)) return;
    const n = parseInt(e.key, 10);
    if (n >= 1 && n <= 9 && views[n - 1]) { go(views[n - 1][0]); e.preventDefault(); return; }
    if (e.key === 'd') { setTheme(null, S.mode === 'dark' ? 'light' : 'dark'); e.preventDefault(); }
    if (e.key === 't') { cycleTheme(); e.preventDefault(); }
  };
  addEventListener('keydown', onKey);
  return () => removeEventListener('keydown', onKey);
}
