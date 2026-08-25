// 鎏金的组件词汇。**只属于这个主题。**
//
// 隐喻是**刻本**，不是仪表盘：
//   leaf     一页。视图自己决定内容切成几页 —— 这套主题不滚，靠翻。
//   plate    金版：数字压在一块倒角金板上，字是金箔渐变不是纯色
//   carve    阴刻条：排行不发光，是凹进纸面的刻痕
//   marginal 眉批：贴在版心外的小字注，用朱线起头
//   seal     朱印：状态。颜色只是辅助，每个都带字
//   rub      拓片：表格
//   fold     折页：默认收起的明细
import { esc, fmt, pct } from '../../core/app.js';

/**
 * 一页。**分页是视图的责任** —— 一页塞不下就自己再开一页，
 * 不许指望用户往下滚（这套主题的 body 是 overflow:hidden）。
 * cols=true 走两栏界行版式；表格页建议单栏，否则会被切断在栏间。
 */
export const leaf = ({ title, lead, body = '', cols = true }) => `
<section class="leaf">
  <div class="${cols ? 'cols' : ''}">
    ${title ? `<h1>${esc(title)}</h1>` : ''}
    ${lead ? `<p class="lead">${lead}</p>` : ''}
    ${body}
  </div>
</section>`;

export const h2 = t => `<h2>${esc(t)}</h2>`;

/** 金版。big=true 时横跨两栏 —— 一页最多一块 big，那是这一页的题眼。 */
export const plate = ({ k, v, n, big, size, plain }) => `
<div class="plate ${big ? 'big' : ''}">
  <div class="k">${esc(k)}</div>
  <div class="v ${size || ''} ${plain ? 'plain' : ''}">${v}</div>
  ${n ? `<div class="n">${n}</div>` : ''}
</div>`;

export const plates = rows => rows.map(plate).join('');

/** 阴刻条。可点的行给 attr，键盘由 core 那座桥接管。 */
export const carve = rows => {
  const mx = Math.max(1, ...rows.map(r => Math.abs(r.v || 0)));
  return `<div class="carve">${rows.map(r => `
    <div class="crow" ${r.attr || ''} ${r.attr ? 'role="button" tabindex="0"' : ''}>
      <span class="ck" title="${esc(r.k)}">${esc(r.k)}</span>
      <span class="cv">${r.label != null ? r.label : fmt(r.v)}</span>
      <span class="ctrack"><span class="cfill" style="transform:scaleX(${(Math.abs(r.v || 0) / mx).toFixed(4)})"></span></span>
    </div>`).join('')}</div>`;
};

export const marginal = html => `<div class="marginal">${html}</div>`;
export const warn = html => `<div class="warnbox">${html}</div>`;

export const rub = (cols, rows) => `<div class="tw"><table><thead><tr>${
  cols.map(c => `<th class="${c.r ? 'r' : ''}">${esc(c.t)}</th>`).join('')
}</tr></thead><tbody>${rows.map(r => `<tr>${
  r.map((cell, i) => `<td class="${cols[i] && cols[i].r ? 'r' : ''}">${cell}</td>`).join('')
}</tr>`).join('')}</tbody></table></div>`;

export const fold = (title, inner) =>
  `<details class="fold"><summary>${esc(title)}</summary><div>${inner}</div></details>`;

export const chip = t => `<span class="chip">${esc(t)}</span>`;
export const seal = s => `<span class="seal" data-s="${s}">${s}</span>`;
export const rate = v => v == null ? seal('说不准') : pct(v);
