// 星云宇宙的组件词汇。**只属于这个主题。**
//
// 上一版的 kit 是 hero/sec/grid/orbit/slab/drawer/table —— 和鎏金逐字相同、
// 和琉璃只差两个名字。同一套词汇必然长出同一套界面，那就是「三个主题看起来一样」的机制。
//
// 这一版的词汇来自另一个隐喻：**观星**。
//   stage    中央台面：一次只讲一件事，有眉题、标题、一句解释
//   headline 头条数：大到没有第二个焦点。琉璃用便当格摊开，这里只留一个
//   reads    一排小读数：横向一条，不是网格 —— 它是头条的注脚，不是并列项
//   beams    射线：一条数据一条光，靠 ← → 在其间移动焦点，不靠眼睛扫
//   sheet    明细：从下方升起，默认收起 —— 这套主题的信息密度是**刻意低**的
import { esc, fmt, pct } from '../../core/app.js';

/** 中央台面。每个视图**只调一次** —— 一屏两个台面就说明这一屏想讲两件事。 */
export const stage = ({ eyebrow, title, hint, body = '' }) => `
<div class="stage">
  ${eyebrow ? `<div class="eyebrow">${esc(eyebrow)}</div>` : ''}
  ${title ? `<h1>${esc(title)}</h1>` : ''}
  ${hint ? `<p class="hint">${hint}</p>` : ''}
  ${body}
</div>`;

/** 头条数。**一屏一个。** 有第二个就说明没想清楚这屏在回答什么问题。 */
export const headline = (k, v, n) => `
<div class="headline">
  <div class="k">${esc(k)}</div>
  <div class="v">${v}</div>
  ${n ? `<div class="n">${n}</div>` : ''}
</div>`;

/** 一排小读数。横向一条，是头条的注脚 —— 不要拿它当便当格用。 */
export const reads = rows => `<div class="reads">${rows.map(r => `
  <div class="read">
    <div class="k">${esc(r.k)}</div>
    <div class="v ${r.tone || ''} ${r.size || ''}">${r.v}</div>
    ${r.n ? `<div class="n">${r.n}</div>` : ''}
  </div>`).join('')}</div>`;

/**
 * 射线。一条数据一条光，长度是相对量，颜色是它自己的属性。
 * 可点的行必须给 attr，同时会自动挂上 role=button —— 键盘走 core 里那座桥。
 */
export const beams = rows => {
  const mx = Math.max(1, ...rows.map(r => Math.abs(r.v || 0)));
  return `<div class="beams">${rows.map(r => `
    <div class="beam" ${r.attr || ''} ${r.attr ? 'role="button" tabindex="0"' : ''}
         style="--w:${((Math.abs(r.v || 0) / mx) * 100).toFixed(2)}%;--c:${r.c || 'var(--acc)'}">
      <span class="k" title="${esc(r.k)}">${esc(r.k)}${r.sub ? `<span class="sub">${esc(r.sub)}</span>` : ''}</span>
      <span class="v">${r.label != null ? r.label : fmt(r.v)}</span>
    </div>`).join('')}</div>`;
};

/** 明细。默认收起是这套主题的性格，不是偷懒。 */
export const sheet = (title, inner) =>
  `<details class="sheet"><summary>${esc(title)}</summary><div class="inner">${inner}</div></details>`;

export const table = (cols, rows) => `<div class="tw"><table><thead><tr>${
  cols.map(c => `<th class="${c.r ? 'r' : ''}">${esc(c.t)}</th>`).join('')
}</tr></thead><tbody>${rows.map(r => `<tr>${
  r.map((cell, i) => `<td class="${cols[i] && cols[i].r ? 'r' : ''}">${cell}</td>`).join('')
}</tr>`).join('')}</tbody></table></div>`;

export const warn = html => `<div class="warnbox">${html}</div>`;
export const pill = t => `<span class="pill">${esc(t)}</span>`;
export const state = s => `<span class="st" data-s="${s}">${s}</span>`;
export const rate = v => v == null ? state('说不准') : pct(v);

/** 角落读数。写进 #hud，不占中央 —— 中央永远只有一件事。 */
export const hud = rows => {
  const el = document.getElementById('hud');
  if (!el) return;
  el.innerHTML = rows.map(r =>
    `<div class="r"><b>${r.v}</b><span>${esc(r.k)}</span></div>`).join('');
};
