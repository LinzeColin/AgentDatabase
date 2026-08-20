// 星云宇宙的外壳 —— 「观星台」。v0.7.0 推翻重做。
//
// **和另外两套主题不共用任何标记。** 上一版之所以跟琉璃几乎一样，
// 就是因为三套 shell.js 吐的是同一份 DOM（左轨 + stamp + view + foot），
// 只有背景画布不同。换皮不是换主题。
//
// 这一版没有 #rail。导航全在底部的指令坞与 `/` 命令面板里，
// 整块屏幕留给天幕和中央那一个台面。
import { esc, S, NAV, VIEW_LIST, GROUP_OF, go, reduced } from '../../core/app.js';

export const css = 'themes/nebula/shell.css';

let cosmos = null, onResize = null, onScroll = null, onVis = null, raf = 0;
// 每次启动发一个号：startCosmos 是异步的（要 import three.js），
// 而 applyTheme 可能在它落地之前又跑一遍。号对不上就整份作废 ——
// 否则两套场景同时活着，一份在屏幕上跑、另一份在后台烧显卡，每切一次主题泄一份。
let gen = 0;
let held = false;          // 视图接管镜头期间，滚动那条线断开

export function chrome(mount) {
  mount.innerHTML = `
    <canvas id="cosmos"></canvas>
    <div id="shell">
      <div id="stamp"></div>
      <div id="hud"></div>
      <main id="view"></main>
      <div id="foot"></div>
      <div id="keyhint">← → 移动焦点　/ 直达　T 换主题</div>
    </div>
    <div id="sub" role="group" aria-label="二级导航"></div>
    <nav id="dock" aria-label="主导航"></nav>
    <div id="pal" role="dialog" aria-modal="true" aria-label="直达">
      <div class="box">
        <input id="palq" type="text" placeholder="输入去哪儿 —— 日历、转化、口径…" autocomplete="off">
        <div class="hits" id="palh"></div>
      </div>
    </div>`;
  buildDock(mount);
  bindPalette(mount);
  startCosmos();
}

/* ── 指令坞。取代左轨的那个东西 ── */
function buildDock(root) {
  const dock = root.querySelector('#dock');
  const sub = root.querySelector('#sub');
  dock.innerHTML = NAV.map(g =>
    `<button class="g" data-g="${g.id}" aria-expanded="false">
       <span class="gi" aria-hidden="true">${g.icon}</span><span class="gl">${esc(g.label)}</span>
     </button>`).join('')
    + `<span class="sep"></span><div id="tools" style="display:flex;gap:2px"></div>`;

  let open = null;
  const paint = () => {
    const cur = (location.hash.replace(/^#\/?/, '').split('/')[0]) || 'overview';
    const grp = GROUP_OF[cur];
    dock.querySelectorAll('.g').forEach(b => {
      b.classList.toggle('on', b.dataset.g === grp && open !== b.dataset.g);
      b.setAttribute('aria-expanded', String(open === b.dataset.g));
    });
    if (!open) { sub.classList.remove('on'); return; }
    const g = NAV.find(x => x.id === open);
    sub.innerHTML = g.views.map(([v, l]) =>
      `<button data-v="${v}" ${v === cur ? 'aria-current="true"' : ''}>${esc(l)}</button>`).join('');
    sub.classList.add('on');
  };

  dock.addEventListener('click', e => {
    const b = e.target.closest('.g');
    if (!b) return;
    const g = NAV.find(x => x.id === b.dataset.g);
    // 只有一个二级的直接跳，不弹二级条 —— 为一个按钮弹一排是噪音
    if (g.views.length === 1) { open = null; paint(); return go(g.views[0][0]); }
    open = (open === b.dataset.g) ? null : b.dataset.g;
    paint();
  });
  sub.addEventListener('click', e => {
    const b = e.target.closest('button[data-v]');
    if (b) { open = null; go(b.dataset.v); paint(); }
  });
  // 点空处收起二级
  document.addEventListener('click', e => {
    if (open && !e.target.closest('#dock') && !e.target.closest('#sub')) { open = null; paint(); }
  });
  addEventListener('hashchange', paint);
  paint();
}

/* ── `/` 命令面板。没有左轨就必须有直达，否则 13 个视图要点两下才到 ── */
function bindPalette(root) {
  const pal = root.querySelector('#pal');
  const q = root.querySelector('#palq');
  const hits = root.querySelector('#palh');
  let idx = 0, list = [];

  const render = () => {
    const s = q.value.trim().toLowerCase();
    list = VIEW_LIST.filter(([v, l]) => !s || l.toLowerCase().includes(s) || v.includes(s));
    idx = Math.min(idx, Math.max(0, list.length - 1));
    hits.innerHTML = list.map(([v, l], i) => {
      const g = NAV.find(x => x.id === GROUP_OF[v]);
      return `<div class="hit${i === idx ? ' on' : ''}" data-v="${v}">
        <span>${esc(l)}</span><span class="g">${esc(g ? g.label : '')}</span></div>`;
    }).join('') || `<div class="hit" style="color:var(--ink3)">没有匹配的视图</div>`;
  };
  const open = () => { pal.classList.add('on'); q.value = ''; idx = 0; render(); q.focus(); };
  const shut = () => pal.classList.remove('on');

  q.addEventListener('input', render);
  hits.addEventListener('click', e => {
    const h = e.target.closest('.hit[data-v]');
    if (h) { shut(); go(h.dataset.v); }
  });
  pal.addEventListener('click', e => { if (e.target === pal) shut(); });
  q.addEventListener('keydown', e => {
    if (e.key === 'Escape') return shut();
    if (e.key === 'ArrowDown') { idx = Math.min(idx + 1, list.length - 1); render(); e.preventDefault(); }
    if (e.key === 'ArrowUp') { idx = Math.max(idx - 1, 0); render(); e.preventDefault(); }
    if (e.key === 'Enter' && list[idx]) { shut(); go(list[idx][0]); }
  });
  root.__palOpen = open;
}

export function bindKeys(views, api) {
  const onKey = e => {
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    if (e.key === '/') { e.preventDefault(); document.getElementById('root').__palOpen?.(); return; }
    if (e.key === 't' || e.key === 'T') { e.preventDefault(); api.cycleTheme(); return; }
    // ← → 在中央台面的射线之间移动焦点。这是这套主题的阅读方式：
    // 不是扫一张表，是一次看透一条。
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      const beams = [...document.querySelectorAll('#view .beam')];
      if (beams.length < 2) return;
      const cur = beams.findIndex(b => b.classList.contains('on'));
      const next = e.key === 'ArrowRight'
        ? (cur + 1) % beams.length
        : (cur <= 0 ? beams.length - 1 : cur - 1);
      beams.forEach(b => b.classList.remove('on'));
      beams[next].classList.add('on');
      beams[next].scrollIntoView({ block: 'nearest', behavior: reduced() ? 'auto' : 'smooth' });
      e.preventDefault();
    }
  };
  addEventListener('keydown', onKey);
  return () => { removeEventListener('keydown', onKey); stopCosmos(); };
}

/* ── 天幕。三维在这套主题里**就是界面本身**，不是背景装饰 ── */
function fit() { if (cosmos) cosmos.resize(); }

async function startCosmos() {
  stopCosmos();
  const my = ++gen;
  if (reduced()) return;                    // 要求减少动效就不点天幕
  try {
    const [{ buildCosmos }] = await Promise.all([import('../../core/cosmos.js')]);
    if (my !== gen) return;                 // 号对不上，这一份已经作废
    const cv = document.getElementById('cosmos');
    if (!cv || !S.atlas) return;
    const built = buildCosmos(cv, S.atlas, { mode: S.mode });
    if (my !== gen) { try { built.dispose(); } catch { /* 收摊失败不拖垮切换 */ } return; }
    cosmos = built;
  } catch (e) {
    console.warn('[nebula] 天幕点不起来，退回纯二维：', e && e.message);
    cosmos = null;
    return;
  }
  // **先同步画一帧，再进 rAF 循环。**
  // 页面在后台标签里加载时 requestAnimationFrame 一次都不会触发 ——
  // 于是画布永远是空的，用户切回来看到一片黑，而代码看起来完全正常。
  // 实测就是这个形态（Browser pane 里 document.hidden 恒为 true，星图一帧没画）。
  // 这一行是「宁可多画一帧，也不能留空白」的同一条规矩。
  try { cosmos.frame(0); } catch { /* 首帧失败也不该拦住后面的循环 */ }

  // rAF 自己驱动。**必须认号** —— 作废那一份的循环不停就会在后台一直烧显卡，
  // 每切一次主题泄一份，这个坑实测踩过。
  let last = performance.now();
  const my2 = my;
  (function tick(now) {
    if (my2 !== gen || !cosmos) return;
    const dt = Math.min(64, now - last); last = now;
    if (!document.hidden) { try { cosmos.frame(dt); } catch { /* 单帧失败不该拆掉整个循环 */ } }
    raf = requestAnimationFrame(tick);
  })(last);

  // 从后台切回来时补一帧并重启循环：rAF 在隐藏期间是冻结的，
  // 光靠它自己恢复，用户会先看见一帧陈旧画面。
  onVis = () => {
    if (document.hidden || my !== gen || !cosmos) return;
    last = performance.now();
    try { cosmos.frame(0); } catch { /* 同上 */ }
    if (!raf) raf = requestAnimationFrame(function again(n) {
      if (my !== gen || !cosmos) return;
      const dt = Math.min(64, n - last); last = n;
      if (!document.hidden) { try { cosmos.frame(dt); } catch { /* 同上 */ } }
      raf = requestAnimationFrame(again);
    });
  };
  document.addEventListener('visibilitychange', onVis);

  onResize = () => fit();
  addEventListener('resize', onResize);
  // 中央台面往下滚 = 沿时间轴往前飞。**这是这套主题里三维和界面真正接上的地方** ——
  // 不是背景在飘，是你在穿过自己的时间。
  onScroll = () => {
    if (held || !cosmos) return;
    const v = document.getElementById('view');
    if (!v) return;
    const max = Math.max(1, v.scrollHeight - v.clientHeight);
    if (max < 40) return;                   // 内容没超出一屏就不劫持镜头
    cosmos.flyTo(v.scrollTop / max);
  };
  document.getElementById('view')?.addEventListener('scroll', onScroll, { passive: true });
}

function stopCosmos() {
  gen++;
  if (raf) { cancelAnimationFrame(raf); raf = 0; }
  if (onResize) { removeEventListener('resize', onResize); onResize = null; }
  if (onScroll) { document.getElementById('view')?.removeEventListener('scroll', onScroll); onScroll = null; }
  if (onVis) { document.removeEventListener('visibilitychange', onVis); onVis = null; }
  if (cosmos) { try { cosmos.dispose(); } catch { /* 已经没了就算了 */ } cosmos = null; }
}

/** 视图要自己开镜头时先 hold，松手记得 release —— 两个司机同时踩油门的后果实测过。 */
export function holdCamera(on) { held = !!on; }
export function scene() { return cosmos; }
