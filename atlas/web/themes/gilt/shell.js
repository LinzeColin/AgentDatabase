// 鎏金的外壳 —— 「金册」。v0.7.0 推翻重做。
//
// **和另外两套主题不共用任何标记。**
// 琉璃是左轨 + 便当格，星云是天幕 + 中央台面，这里是**一本可以翻的册子**：
// 书眉、册页、页码、目录页 —— 纸书有什么，这里就有什么，没有的就没有。
//
// 最要紧的一条：**页面不滚动。** 视图把内容切成册页，←/→ 翻。
// 一屏放不下的部分由视图自己决定怎么分页，而不是靠用户一直往下滚。
import { esc, S, NAV, VIEW_LIST, GROUP_OF, go, reduced } from '../../core/app.js';

export const css = 'themes/gilt/shell.css';

let codex = null, onResize = null, onVis = null, raf = 0, gen = 0;
let page = 0, pages = 1;

export function chrome(mount) {
  mount.innerHTML = `
    <canvas id="codexcv"></canvas>
    <div id="shell">
      <header id="head">
        <span class="fish" aria-hidden="true"></span>
        <span class="ttl" id="htitle">Memory Atlas</span>
        <span class="grp" id="hgrp"></span>
        <span class="sp"></span>
        <div id="stamp"></div>
        <button id="tocbtn" aria-haspopup="dialog">目录</button>
        <div id="tools"></div>
      </header>
      <div id="book"><div id="leaves"><main id="view"></main></div></div>
      <footer id="folio">
        <button id="prev" aria-label="上一页">◀ 前页</button>
        <span class="no" id="pno"></span>
        <button id="next" aria-label="下一页">后页 ▶</button>
      </footer>
      <div id="foot"></div>
    </div>
    <div id="toc" role="dialog" aria-modal="true" aria-label="目录"><div class="in"></div></div>`;

  buildToc(mount);
  mount.querySelector('#prev').onclick = () => turn(page - 1);
  mount.querySelector('#next').onclick = () => turn(page + 1);
  bindSwipe(mount.querySelector('#book'));
  addEventListener('hashchange', () => { paintHead(); });
  paintHead();
  startCodex();
}

/* ── 分页。core/app.js 每次渲染完视图会调这里 ── */
export function afterRender() { relayout(); }

function relayout() {
  const leaves = document.getElementById('leaves');
  const view = document.getElementById('view');
  if (!leaves || !view) return;
  // 视图可以自己吐 .leaf；没吐就把整个 #view 当成单页。
  const own = view.querySelectorAll(':scope > .leaf');
  if (own.length) {
    // 把视图产的册页提到 #leaves 下，#view 退成一个空壳容器
    leaves.innerHTML = '';
    own.forEach(l => leaves.appendChild(l));
    leaves.appendChild(view);
    view.style.display = 'none';
  } else {
    view.style.display = '';
    view.classList.add('leaf');
  }
  pages = Math.max(1, leaves.querySelectorAll('.leaf').length);
  page = 0;
  leaves.classList.add('noanim');
  apply();
  requestAnimationFrame(() => leaves.classList.remove('noanim'));
}

function apply() {
  const leaves = document.getElementById('leaves');
  if (leaves) leaves.style.transform = `translateX(${-page * 100}%)`;
  const pno = document.getElementById('pno');
  if (pno) pno.innerHTML = `第 <b>${page + 1}</b> 页 / 共 ${pages} 页`;
  const p = document.getElementById('prev'), n = document.getElementById('next');
  if (p) p.disabled = page <= 0;
  if (n) n.disabled = page >= pages - 1;
  if (codex && codex.turnTo) codex.turnTo(pages > 1 ? page / (pages - 1) : 0);
}

function turn(to) {
  const t = Math.max(0, Math.min(pages - 1, to));
  if (t === page) return;
  page = t;
  apply();
  // 翻页后把新页滚回顶部 —— 纸书翻页不会停在半截
  const cur = document.getElementById('leaves')?.children[page];
  if (cur) cur.scrollTop = 0;
}

/* ── 目录页。**整页的目录，不是侧栏** ── */
function buildToc(root) {
  const toc = root.querySelector('#toc');
  const box = toc.querySelector('.in');
  const paint = () => {
    const cur = (location.hash.replace(/^#\/?/, '').split('/')[0]) || 'overview';
    let n = 0;
    box.innerHTML = `<div class="shutbar"><button class="shut">合上 ✕</button></div>
      <h1>目录</h1>
      <p class="sub">${esc((S.atlas && S.atlas.meta && S.atlas.meta.first_day) || '')} 起　共 ${VIEW_LIST.length} 篇</p>`
      + NAV.map(g => `<div class="grp"><div class="gh">${esc(g.label)}</div>${
        g.views.map(([v, l]) => {
          n += 1;
          return `<a href="#/${v}" data-v="${v}" ${v === cur ? 'aria-current="true"' : ''}>
            <span>${esc(l)}</span><span class="dots"></span><span class="pg">${n}</span></a>`;
        }).join('')}</div>`).join('');
  };
  root.querySelector('#tocbtn').onclick = () => { paint(); toc.classList.add('on'); };
  toc.addEventListener('click', e => {
    if (e.target.closest('.shut') || e.target === toc) return toc.classList.remove('on');
    if (e.target.closest('a[data-v]')) toc.classList.remove('on');
  });
}

function paintHead() {
  const cur = (location.hash.replace(/^#\/?/, '').split('/')[0]) || 'overview';
  const v = VIEW_LIST.find(x => x[0] === cur);
  const g = NAV.find(x => x.id === GROUP_OF[cur]);
  const t = document.getElementById('htitle'), gr = document.getElementById('hgrp');
  if (t) t.textContent = v ? v[1] : 'Memory Atlas';
  if (gr) gr.textContent = g ? g.label : '';
}

/* ── 翻页手势。册子必须能划 ── */
function bindSwipe(el) {
  if (!el) return;
  let x0 = null, y0 = null;
  el.addEventListener('touchstart', e => {
    const t = e.touches[0]; x0 = t.clientX; y0 = t.clientY;
  }, { passive: true });
  el.addEventListener('touchend', e => {
    if (x0 == null) return;
    const t = e.changedTouches[0];
    const dx = t.clientX - x0, dy = t.clientY - y0;
    // 竖向位移更大就是在读，不是在翻 —— 别把滚动当成翻页
    if (Math.abs(dx) > 56 && Math.abs(dx) > Math.abs(dy) * 1.6) turn(page + (dx < 0 ? 1 : -1));
    x0 = y0 = null;
  }, { passive: true });
}

export function bindKeys(views, api) {
  const onKey = e => {
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    if (e.key === 'Escape') { document.getElementById('toc')?.classList.remove('on'); return; }
    if (e.key === 'm' || e.key === 'M') { e.preventDefault(); document.getElementById('tocbtn')?.click(); return; }
    if (e.key === 't' || e.key === 'T') { e.preventDefault(); api.cycleTheme(); return; }
    if (e.key === 'ArrowRight' || e.key === 'PageDown') { e.preventDefault(); turn(page + 1); }
    if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); turn(page - 1); }
  };
  addEventListener('keydown', onKey);
  return () => { removeEventListener('keydown', onKey); stopCodex(); };
}

/* ── 金页。三维在这套主题里是**物件的材质**，不是可以飞进去的空间 ── */
async function startCodex() {
  stopCodex();
  const my = ++gen;
  if (reduced()) return;
  try {
    const { buildCodex } = await import('../../core/codex.js');
    if (my !== gen) return;
    const cv = document.getElementById('codexcv');
    if (!cv || !S.atlas) return;
    const built = buildCodex(cv, S.atlas, { mode: S.mode });
    if (my !== gen) { try { built.dispose(); } catch { /* 收摊失败不拖垮切换 */ } return; }
    codex = built;
  } catch (e) {
    console.warn('[gilt] 金页点不起来，退回纯二维：', e && e.message);
    codex = null;
    return;
  }
  // 先同步画一帧：页面在后台标签加载时 rAF 一次都不触发，
  // 画布会永远是空的而代码看起来完全正常。
  try { codex.frame(0); } catch { /* 首帧失败不拦后面 */ }

  let last = performance.now();
  (function tick(now) {
    if (my !== gen || !codex) return;
    const dt = Math.min(64, now - last); last = now;
    if (!document.hidden) { try { codex.frame(dt); } catch { /* 单帧失败不拆循环 */ } }
    raf = requestAnimationFrame(tick);
  })(last);

  onVis = () => {
    if (document.hidden || my !== gen || !codex) return;
    last = performance.now();
    try { codex.frame(0); } catch { /* 同上 */ }
  };
  document.addEventListener('visibilitychange', onVis);
  onResize = () => { try { codex.resize(); } catch { /* 同上 */ } };
  addEventListener('resize', onResize);
}

function stopCodex() {
  gen++;
  if (raf) { cancelAnimationFrame(raf); raf = 0; }
  if (onResize) { removeEventListener('resize', onResize); onResize = null; }
  if (onVis) { document.removeEventListener('visibilitychange', onVis); onVis = null; }
  if (codex) { try { codex.dispose(); } catch { /* 已经没了 */ } codex = null; }
}

export function scene() { return codex; }
