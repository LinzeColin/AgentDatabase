// 手记主题的组件词汇。只属于这个主题。
// 特点：数字写进句子里；排行用细横线不用色块；旁注浮在正文栏外；图有图注。
import { esc, fmt, pct } from '../../core/app.js';

export const sec = (t, hint) =>
  `<div class="sec">${esc(t)}</div>${hint ? `<p class="hint">${hint}</p>` : ''}`;

export const lede = html => `<p class="body lede">${html}</p>`;
export const p = html => `<p class="body">${html}</p>`;
export const n = v => `<span class="n">${typeof v === 'number' ? fmt(v) : esc(v)}</span>`;
export const big = v => `<span class="big">${esc(v)}</span>`;
export const aside = html => `<div class="aside">${html}</div>`;
export const note = html => `<div class="note">${html}</div>`;

export const figure = (body, caption) =>
  `<figure><div class="fbody">${body}</div>${caption ? `<figcaption>${caption}</figcaption>` : ''}</figure>`;

/** 排行：名次 + 名称 + 一条细线 + 数值。手记不用色块条。 */
export const rank = rows => {
  const mx = Math.max(1, ...rows.map(r => r.v));
  return `<div class="rank">${rows.map((r, i) => `
    <span class="rk">${String(i + 1).padStart(2, '0')}</span>
    <span class="rl" ${r.attr || ''}>${r.attr ? `<span class="lnk">${esc(r.k)}</span>` : esc(r.k)}<i style="width:${(r.v / mx * 46).toFixed(0)}%"></i></span>
    <span class="rv">${r.label != null ? r.label : fmt(r.v)}</span>`).join('')}</div>`;
};

/** 行内火花线：手记把趋势直接放进句子里。 */
const S = '▁▂▃▄▅▆▇█';
export const spark = arr => {
  if (!arr || !arr.length) return '—';
  const mx = Math.max(...arr, 1);
  return `<span style="letter-spacing:-.5px;color:var(--acc)">${arr.map(v => S[Math.min(7, Math.floor(v / mx * 7.99))]).join('')}</span>`;
};

export const table = (cols, rows) => `<table><thead><tr>${
  cols.map(c => `<th class="${c.r ? 'r' : ''}">${esc(c.t)}</th>`).join('')
}</tr></thead><tbody>${rows.map(r => `<tr>${
  r.map((cell, i) => `<td class="${cols[i] && cols[i].r ? 'r' : ''}">${cell}</td>`).join('')}</tr>`).join('')}</tbody></table>`;

export const state = s => `<span class="st" data-s="${s}">${s}</span>`;
export const rate = v => v == null ? state('不确定') : pct(v);
export const kw = t => `<span class="kw">${esc(t)}</span>`;
