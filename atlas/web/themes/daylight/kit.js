// 白昼的组件词汇：栅格、发丝线、编号。没有卡片、没有圆角、没有阴影。
import { esc, fmt, pct } from '../../core/app.js';

export const hero = (eyebrow, title, lead) => `<header class="hero">
  <div class="eyebrow">${esc(eyebrow)}</div>
  <h1>${esc(title)}</h1>${lead ? `<p>${lead}</p>` : ''}</header>`;

export const sec = (t, hint) =>
  `<div class="sec">${esc(t)}</div>${hint ? `<p class="hint">${hint}</p>` : ''}`;

export const grid = cells => `<div class="grid">${cells.map(c =>
  `<div class="cell ${c.w ? 'w' + c.w : ''}">
     <div class="ck">${c.kHtml || esc(c.k)}</div>
     <div class="cv ${c.tone || ''}">${c.v}</div>
     <div class="cn">${c.n || ''}</div>${c.extra || ''}</div>`).join('')}</div>`;

export const orbit = rows => {
  const mx = Math.max(1, ...rows.map(r => r.v));
  return `<div class="orbit">${rows.map(r => `
    <div class="orow" ${r.attr || ''}>
      <span class="olabel" title="${esc(r.k)}">${esc(r.k)}</span>
      <span class="otrack"><span class="ofill" style="width:${(r.v / mx * 100).toFixed(1)}%"></span></span>
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
export const state = s => `<span class="st" data-s="${s}">${s}</span>`;
export const rate = v => v == null ? state('说不准') : pct(v);
