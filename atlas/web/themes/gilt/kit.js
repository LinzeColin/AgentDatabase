// 鎏金的组件词汇。签名与 nebula 完全一致，所以 12 个视图可以零改动移植。
// 差别在于每一件东西长什么样：漆面、切角、错金、阴刻，没有一处毛玻璃。
import { esc, fmt, pct } from '../../core/app.js';

// 匾额：小方章取标题首字当印文，鎏金衬线大字，底下一条双线。
export const hero = (eyebrow, title, lead) => `<header class="hero">
  <div class="eyebrow" data-seal="${esc((title || '·').slice(0, 1))}">${esc(eyebrow)}</div>
  <h1>${esc(title)}</h1>${lead ? `<p>${lead}</p>` : ''}</header>`;

export const sec = (t, hint) =>
  `<div class="sec">${esc(t)}</div>${hint ? `<p class="hint">${hint}</p>` : ''}`;

export const grid = cells => `<div class="grid">${cells.map(c =>
  `<div class="cell ${c.w ? 'w' + c.w : ''}">
     <div class="ck">${c.kHtml || esc(c.k)}</div>
     <div class="cv ${c.tone || ''} ${c.size || ''}">${c.v}</div>
     <div class="cn">${c.n || ''}</div>${c.extra || ''}</div>`).join('')}</div>`;

// 错金条：任何进来的纯色都自动「铸」一遍 —— 高光、本色、暗部三段，
// 这样主题色进来也不会是一块平涂，而是一根有厚度的金属条。
const cast = c => c
  ? `linear-gradient(180deg, color-mix(in srgb,${c} 70%,#fff) 0%, ${c} 55%, color-mix(in srgb,${c} 62%,#000) 100%)`
  : 'var(--gold)';

export const orbit = rows => {
  const mx = Math.max(1, ...rows.map(r => r.v));
  return `<div class="orbit">${rows.map(r => `
    <div class="orow" ${r.attr || ''} ${r.attr ? 'role="button" tabindex="0"' : ''}>
      <span class="olabel" title="${esc(r.k)}">${esc(r.k)}</span>
      <span class="otrack"><span class="ofill" style="transform:scaleX(${(r.v / mx).toFixed(4)});
        background:${cast(r.c)}"></span></span>
      <span class="oval">${r.label != null ? r.label : fmt(r.v)}</span>
    </div>`).join('')}</div>`;
};

export const slab = html => `<div class="slab">${html}</div>`;
export const drawer = (title, inner) =>
  `<details class="drawer"><summary>${esc(title)}</summary><div class="inner">${inner}</div></details>`;
export const table = (cols, rows) => `<table><thead><tr>${
  cols.map(c => `<th class="${c.r ? 'r' : ''}">${esc(c.t)}</th>`).join('')
}</tr></thead><tbody>${rows.map(r => `<tr>${
  r.map((cell, i) => `<td class="${cols[i] && cols[i].r ? 'r' : ''}">${cell}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
export const warn = html => `<div class="warnbox">${html}</div>`;
export const pill = t => `<span class="pill">${esc(t)}</span>`;

// 四态印：文字永远在，前置刻符是第二冗余通道，颜色只是第三。
// 实测本项目 15 组配色对比度全部不到 3:1 —— 只靠颜色的状态等于没有状态。
const MARK = { '通': '●', '断了': '✕', '没做': '○', '说不准': '◐', '看这里': '◆' };
export const state = s => `<span class="st" data-s="${s}" data-m="${MARK[s] || '·'}">${s}</span>`;
export const rate = v => v == null ? state('说不准') : pct(v);
