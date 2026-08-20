// app.js —— 路由与共享状态。视图各自一个模块，按需 import()。
// CSP 是 script-src 'self'：没有内联脚本、没有 CDN、没有构建步骤。

export const S = { atlas: null, dayCache: new Map() };

export const TOPIC_COLORS = {
  '修bug': '#ff6b6b', '部署上线': '#4ec9a7', '重构简化': '#c48fff', '测试验收': '#ffd166',
  '数据': '#5aa9ff', '自动化': '#63d2ff', '治理规范': '#9aa7b5', '文档': '#8fd694',
  '前端界面': '#ff9ecb', '办公文书': '#ffa94d', '业务方案': '#ffe066', '赚钱': '#4ade80',
  '找工作': '#f472b6', '学习': '#a5b4fc',
};
export const topicColor = t => TOPIC_COLORS[t] || '#6b7684';

export const fmt = n => n >= 1e9 ? (n / 1e9).toFixed(1) + 'B'
  : n >= 1e6 ? (n / 1e6).toFixed(1) + 'M'
  : n >= 1e3 ? (n / 1e3).toFixed(1) + 'k' : String(n);

export const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

// 记录是 UTC，Owner 在悉尼。固定 +10，不猜夏令时 —— 猜错比差一小时更糟。
export const TZ = 10;
export function local(iso) {
  const d = new Date(iso);
  return new Date(d.getTime() + TZ * 3600e3);
}
export const hhmm = iso => local(iso).toISOString().slice(11, 16);

export async function day(d) {
  if (S.dayCache.has(d)) return S.dayCache.get(d);
  const r = await fetch(`atlas/day/${d}.json`, { cache: 'no-store' });
  if (!r.ok) throw new Error(`那一天没有记录：${d}`);
  const j = await r.json();
  S.dayCache.set(d, j);
  return j;
}

const VIEWS = [
  ['overview', '概览'], ['calendar', '日历'], ['day', '一天'], ['timeline', '时间轴'],
  ['grid', '网格'], ['universe', '宇宙'], ['replay', '回放'], ['analysis', '分析'],
  ['lessons', '沉淀'], ['method', '口径'],
];

function parseHash() {
  const raw = location.hash.replace(/^#\/?/, '');
  const [name, arg] = raw.split('/');
  return { name: VIEWS.some(v => v[0] === name) ? name : 'overview', arg: arg || '' };
}

export function go(name, arg) {
  location.hash = '#/' + name + (arg ? '/' + arg : '');
}

async function render() {
  const { name, arg } = parseHash();
  document.querySelectorAll('#nav button').forEach(b =>
    b.setAttribute('aria-current', String(b.dataset.v === name)));
  const host = document.getElementById('view');
  host.innerHTML = '<div class="loading">读取中…</div>';
  try {
    const mod = await import(`./views/${name}.js`);
    host.innerHTML = '';
    await mod.render(host, arg);
    window.scrollTo(0, 0);
  } catch (e) {
    host.innerHTML = `<div class="note warn"><b>这个视图打不开。</b><br>${esc(e.message || e)}</div>`;
  }
}

async function boot() {
  const nav = document.getElementById('nav');
  nav.innerHTML = VIEWS.map(([v, label]) =>
    `<button data-v="${v}">${label}</button>`).join('');
  nav.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (b) go(b.dataset.v);
  });

  try {
    const r = await fetch('atlas/atlas.json', { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    S.atlas = await r.json();
  } catch (e) {
    document.getElementById('view').innerHTML =
      `<div class="note warn"><b>数据没读到。</b>状态：断了。<br>${esc(e.message)}</div>`;
    document.getElementById('stamp').textContent = '断了';
    return;
  }
  const m = S.atlas.meta;
  const built = local(m.generated_at).toISOString().slice(0, 16).replace('T', ' ');
  document.getElementById('stamp').textContent = `数据截至 ${m.last_day} · 生成于 ${built}`;
  document.getElementById('foot').textContent =
    `${m.sessions_total} 场会话 · ${m.days_active} 个有记录的日子 · ${m.first_day} 起 · 运行期不调用任何模型`;
  addEventListener('hashchange', render);
  render();
}

boot();
