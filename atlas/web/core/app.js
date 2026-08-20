// core/app.js —— 启动、主题、路由。
// 三套主题各自拥有 shell.css + shell.js + views/*，**不共享任何样式或标记**；
// 共享的只有 core/select.js 里的纯数据选择器。
// CSP 是 script-src 'self'：无内联脚本、无 CDN，GSAP 已 vendor。

export const S = { atlas: null, dayCache: new Map(), theme: 'nebula', mode: 'dark' };

export const THEMES = [
  ['console', '控制台'],
  ['nebula', '星域'],
  ['journal', '手记'],
];

export const VIEW_LIST = [
  ['overview', '概览'], ['calendar', '日历'], ['day', '一天'], ['timeline', '时间轴'],
  ['grid', '网格'], ['universe', '宇宙'], ['replay', '回放'],
  ['economics', '经济'], ['tokens', 'Token'], ['lessons', '沉淀'], ['method', '口径'],
];

export const TOPIC_COLORS = {
  '修bug': '#ff6b6b', '部署上线': '#4ec9a7', '重构简化': '#c48fff', '测试验收': '#ffd166',
  '数据': '#5aa9ff', '自动化': '#63d2ff', '治理规范': '#9aa7b5', '文档': '#8fd694',
  '前端界面': '#ff9ecb', '办公文书': '#ffa94d', '业务方案': '#ffe066', '赚钱': '#4ade80',
  '找工作': '#f472b6', '学习': '#a5b4fc',
};
export const topicColor = t => TOPIC_COLORS[t] || '#6b7684';
export const KIND_COLORS = { source: '#63d2ff', project: '#ffd166', topic: '#ff9ecb' };

export const fmt = n => n == null ? '—'
  : n >= 1e9 ? (n / 1e9).toFixed(2) + 'B'
  : n >= 1e6 ? (n / 1e6).toFixed(1) + 'M'
  : n >= 1e3 ? (n / 1e3).toFixed(1) + 'k' : String(Math.round(n));
export const pct = v => v == null ? '不确定' : (v * 100).toFixed(v > 0.99 ? 2 : 1) + '%';
export const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

// 记录是 UTC，Owner 在悉尼。固定 +10，不猜夏令时 —— 猜错比差一小时更糟。
export const TZ = 10;
export const local = iso => new Date(new Date(iso).getTime() + TZ * 3600e3);
export const hhmm = iso => local(iso).toISOString().slice(11, 16);
export const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

export async function day(d) {
  if (S.dayCache.has(d)) return S.dayCache.get(d);
  const r = await fetch(`atlas/day/${d}.json`, { cache: 'no-store' });
  if (!r.ok) throw new Error(`那一天没有记录：${d}`);
  const j = await r.json();
  S.dayCache.set(d, j);
  return j;
}

export function go(name, arg) { location.hash = '#/' + name + (arg ? '/' + arg : ''); }

// 三套主题的动效性格。这是「完全不一样」里最容易被省掉、也最能被身体感觉到的一半。
export function motion() {
  return {
    console: { d: .14, ease: 'power2.out', stagger: .010, cap: .22, y: 5, s: 1, blur: 0 },
    nebula: { d: .70, ease: 'back.out(1.3)', stagger: .055, cap: .62, y: 34, s: .93, blur: 8 },
    journal: { d: .48, ease: 'power1.out', stagger: .07, cap: .45, y: 14, s: 1, blur: 0 },
  }[S.theme];
}
export function enter(sel, host) {
  const g = window.gsap;
  const nodes = [...(host || document).querySelectorAll(sel)];
  if (!nodes.length) return;
  const done = () => nodes.forEach(n => {
    n.style.opacity = ''; n.style.transform = ''; n.style.filter = '';
  });
  // 标签页不可见时浏览器会冻结 rAF，GSAP ticker 停住 —— fromTo 的起始态
  // （opacity:0）就永远留在那儿，用户切回来看到的是一片空白。
  // 实测 document.visibilityState="hidden" 时 ticker 冻在第 10 帧。
  // 所以：不可见就直接给终态，一帧动画都不做。
  if (!g || reduced() || document.hidden) return done();
  const m = motion();
  g.killTweensOf(nodes);
  // stagger 用 amount 而不是 each：**总时长封顶**。
  // 用 each 的话 100 行表格 × 0.01s = 整整一秒内容不可见 —— 实测就是这个毛病。
  const total = Math.min(m.cap, nodes.length * m.stagger);
  const from = { opacity: 0, y: m.y, scale: m.s };
  if (m.blur) from.filter = `blur(${m.blur}px)`;
  const to = { opacity: 1, y: 0, scale: 1, duration: m.d, ease: m.ease,
    stagger: { amount: total }, clearProps: 'filter,transform,opacity' };
  if (m.blur) to.filter = 'blur(0px)';
  g.fromTo(nodes, from, to);
  // 看门狗：无论什么原因动画没跑完，到点强制显示。
  // 「内容永远看不见」是最坏的失败形态，宁可动画不好看也不能空白。
  clearTimeout(nodes.__wd);
  setTimeout(done, (m.d + total) * 1000 + 400);
}
export function countUp(el, to, digits = 0) {
  const g = window.gsap;
  const set = v => { el.textContent = digits ? v.toFixed(digits) : String(Math.round(v)); };
  if (!g || reduced() || document.hidden) return set(to);
  const o = { v: 0 };
  g.to(o, { v: to, duration: motion().d * 2.2, ease: 'power2.out', onUpdate: () => set(o.v) });
  setTimeout(() => set(to), motion().d * 2200 + 400);   // 同样的看门狗
}

// ── 主题切换：换 CSS、重建外壳、重绘当前视图 ──
const LS = 'atlas.theme.v3';
let themeMod = null, disposeChrome = null;

async function applyTheme() {
  const el = document.documentElement;
  el.dataset.theme = S.theme;
  el.dataset.mode = S.mode;
  localStorage.setItem(LS, JSON.stringify({ t: S.theme, m: S.mode }));

  themeMod = await import(`../themes/${S.theme}/shell.js`);
  const link = document.getElementById('themecss');
  await new Promise(res => {
    if (link.getAttribute('href') === themeMod.css) return res();
    link.onload = link.onerror = res;
    link.setAttribute('href', themeMod.css);
  });

  if (disposeChrome) { try { disposeChrome(); } catch { /* 外壳清理失败不该拖垮切换 */ } disposeChrome = null; }
  themeMod.chrome(document.getElementById('root'));

  const nav = document.getElementById('nav');
  nav.innerHTML = themeMod.navMarkup ? themeMod.navMarkup(VIEW_LIST)
    : VIEW_LIST.map(([v, l]) => `<button data-v="${v}">${esc(l)}</button>`).join('');
  nav.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (b) go(b.dataset.v);
  });

  const tools = document.getElementById('tools');
  if (tools) {
    tools.innerHTML = `
      <div class="seg" role="group" aria-label="主题">${
        THEMES.map(([k, l]) => `<button data-theme-btn="${k}">${l}</button>`).join('')}</div>
      <div class="seg" role="group" aria-label="明暗">
        <button data-mode-btn="dark">深</button><button data-mode-btn="light">浅</button></div>`;
    tools.addEventListener('click', e => {
      const t = e.target.closest('[data-theme-btn]'), m = e.target.closest('[data-mode-btn]');
      if (t) setTheme(t.dataset.themeBtn, null);
      if (m) setTheme(null, m.dataset.modeBtn);
    });
  }
  document.querySelectorAll('[data-theme-btn]').forEach(b =>
    b.setAttribute('aria-pressed', String(b.dataset.themeBtn === S.theme)));
  document.querySelectorAll('[data-mode-btn]').forEach(b =>
    b.setAttribute('aria-pressed', String(b.dataset.modeBtn === S.mode)));

  if (themeMod.bindKeys) {
    disposeChrome = themeMod.bindKeys(VIEW_LIST, { go, setTheme, cycleTheme });
  }
  stampAndFoot();
  const { initFX } = await import('./fx.js');
  initFX();
  window.dispatchEvent(new CustomEvent('atlas:theme'));
}

export async function setTheme(theme, mode) {
  if (theme) S.theme = theme;
  if (mode) S.mode = mode;
  await applyTheme();
  await render();
}
export function cycleTheme() {
  const i = THEMES.findIndex(t => t[0] === S.theme);
  setTheme(THEMES[(i + 1) % THEMES.length][0], null);
}

function stampAndFoot() {
  const m = S.atlas && S.atlas.meta;
  if (!m) return;
  const built = local(m.generated_at).toISOString().slice(0, 16).replace('T', ' ');
  const stamp = document.getElementById('stamp');
  if (stamp) {
    stamp.textContent = `数据截至 ${m.last_day} · ${built} 生成`;
    // 流水线停了必须看得出来。静默陈旧 + 页面一切正常 = 最坏的一种假绿。
    const ageH = (Date.now() - new Date(m.generated_at).getTime()) / 3600e3;
    if (ageH > 48) {
      stamp.textContent += `　⚠ 断了 ${Math.floor(ageH / 24)} 天`;
      stamp.style.color = 'var(--warn)';
    }
  }
  const foot = document.getElementById('foot');
  if (foot) foot.textContent =
    `${m.sessions_total} 场会话 · ${m.days_active} 天 · ${m.first_day} 起 · 运行期不调用任何模型`;
}

// ── 路由 ──
function parseHash() {
  const raw = location.hash.replace(/^#\/?/, '');
  const [name, ...rest] = raw.split('/');
  return { name: VIEW_LIST.some(v => v[0] === name) ? name : 'overview', arg: rest.join('/') };
}

let current = null;
export async function render() {
  const { name, arg } = parseHash();
  document.querySelectorAll('#nav button').forEach(b =>
    b.setAttribute('aria-current', String(b.dataset.v === name)));
  const host = document.getElementById('view');
  if (!host) return;
  if (current && current.dispose) { try { current.dispose(); } catch { /* 视图清理失败不拖垮路由 */ } }
  current = null;
  host.innerHTML = '';
  try {
    const mod = await import(`../themes/${S.theme}/views/${name}.js`);
    current = (await mod.render(host, arg)) || null;
    scrollTo(0, 0);
  } catch (e) {
    host.innerHTML = `<div class="warnbox"><b>这个视图打不开。</b>状态：断了。<br>${esc(e.message || e)}</div>`;
  }
}

async function boot() {
  try {
    const v = JSON.parse(localStorage.getItem(LS) || '{}');
    if (THEMES.some(t => t[0] === v.t)) S.theme = v.t;
    if (v.m === 'light' || v.m === 'dark') S.mode = v.m;
  } catch { /* 存坏了就用默认 */ }

  try {
    const r = await fetch('atlas/atlas.json', { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    S.atlas = await r.json();
  } catch (e) {
    document.getElementById('root').innerHTML =
      `<div style="padding:40px;font:14px system-ui;color:#c33">数据没读到。状态：断了。<br>${esc(e.message)}</div>`;
    return;
  }
  await applyTheme();
  // 从隐藏切回可见时，把可能卡在起始态的节点强制显示一次
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) return;
    document.querySelectorAll('#view [style*="opacity"]').forEach(n => {
      n.style.opacity = ''; n.style.transform = ''; n.style.filter = '';
    });
  });
  addEventListener('hashchange', render);
  render();
}

boot();
