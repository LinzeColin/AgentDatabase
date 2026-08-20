// 控制台主题的组件词汇。**只属于这个主题**，其它主题不复用一行。
// 特点：没有卡片，一切是行、规则线、等宽数字；标题是 ASCII 规则线。
import { esc, fmt, pct } from '../../core/app.js';

export const sec = (t, hint) =>
  `<div class="sec">${esc(t)}</div>${hint ? `<p class="hint">${hint}</p>` : ''}`;

export const kv = rows => `<div class="kv">${rows.map(r =>
  `<div><span class="k">${esc(r[0])}</span><span class="v ${r[2] || ''}">${r[1]}</span></div>`).join('')}</div>`;

export const meter = (v, max, w = 90) =>
  `<span class="meter" style="width:${Math.max(1, Math.round(v / (max || 1) * w))}px"></span>`;

/** ASCII 火花线。控制台主题不画 SVG 图表 —— 用字符，密度更高也更贴气质。 */
const SPARK = '▁▂▃▄▅▆▇█';
export const spark = arr => {
  if (!arr || !arr.length) return '<span class="tag">无数据</span>';
  const mx = Math.max(...arr, 1);
  return `<span class="sparkcell">${arr.map(v => SPARK[Math.min(7, Math.floor(v / mx * 7.99))]).join('')}</span>`;
};

export const table = (cols, rows) => `<table><thead><tr>${
  cols.map(c => `<th class="${c.r ? 'r' : ''}" ${c.w ? `style="width:${c.w}"` : ''}>${esc(c.t)}</th>`).join('')
}</tr></thead><tbody>${rows.map(r => `<tr>${
  r.map((cell, i) => `<td class="${cols[i] && cols[i].r ? 'r' : ''}">${cell}</td>`).join('')
}</tr>`).join('')}</tbody></table>`;

export const state = s => `<span class="st" data-s="${s}">${s}</span>`;
export const warn = html => `<div class="warnbox">${html}</div>`;
export const tag = t => `<span class="tag">${esc(t)}</span>`;
export const link = (text, attrs) => `<span class="lnk" ${attrs}>${esc(text)}</span>`;
export const num = n => fmt(n);
export const rate = v => v == null ? `<span class="st" data-s="不确定">不确定</span>` : pct(v);
