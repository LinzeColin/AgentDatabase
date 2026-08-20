// 琉璃主题的组件词汇。只属于这个主题。
// 主表面不放表格 —— 数字先变成轨道条、弧、卡片，明细收进抽屉。
import { esc, fmt, pct } from '../../core/app.js';

export const sec = (t, hint) =>
  `<div class="sec">${esc(t)}</div>${hint ? `<p class="hint">${hint}</p>` : ''}`;

export const bento = cards => `<div class="bento">${cards.map(c =>
  `<div class="card ${c.w ? 'w' + c.w : ''} ${c.alt ? 'alt' : ''}">
     <div class="ck">${esc(c.k)}</div>
     <div class="cv ${c.tone || ''}">${c.v}</div>
     <div class="cn">${c.n || ''}</div>
     ${c.extra || ''}</div>`).join('')}</div>`;

/** 轨道条：琉璃用它代替排行表。 */
export const orbit = rows => {
  const mx = Math.max(1, ...rows.map(r => r.v));
  return `<div class="orbit">${rows.map(r => `
    <div class="orow" ${r.attr || ''}>
      <span class="olabel" title="${esc(r.k)}">${esc(r.k)}</span>
      <span class="otrack"><span class="ofill" style="width:${(r.v / mx * 100).toFixed(1)}%;
        background:linear-gradient(90deg,${r.c || 'var(--acc)'},${r.c2 || r.c || 'var(--acc2)'})"></span></span>
      <span class="oval">${r.label != null ? r.label : fmt(r.v)}</span>
    </div>`).join('')}</div>`;
};

export const drawer = (title, inner) =>
  `<details class="drawer"><summary>${esc(title)}</summary><div class="inner">${inner}</div></details>`;

export const table = (cols, rows) => `<table><thead><tr>${
  cols.map(c => `<th class="${c.r ? 'r' : ''}">${esc(c.t)}</th>`).join('')
}</tr></thead><tbody>${rows.map(r => `<tr>${
  r.map((cell, i) => `<td class="${cols[i] && cols[i].r ? 'r' : ''}">${cell}</td>`).join('')}</tr>`).join('')}</tbody></table>`;

export const warn = html => `<div class="warnbox">${html}</div>`;
export const pill = t => `<span class="pill">${esc(t)}</span>`;
export const state = s => `<span class="st" data-s="${s}">${s}</span>`;
export const rate = v => v == null ? state('不确定') : pct(v);
