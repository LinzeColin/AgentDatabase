import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { flyToDay } from '../shell.js';
import { hero, sec, grid, orbit, drawer, table, warn, pill, state } from '../kit.js';

// 两个互不知情的来源对出来的：本机会话证明你在做，GitHub 提交证明你做出来了。
export async function render(host) {
  const V = D.A().delivery || {}, G = D.A().github || {};
  if (V.state !== '通') {
    host.innerHTML = hero('交付', '这块对不上', '')
      + warn(`<b>说不准。</b>${esc(V.why || '没读到 GitHub 数据')}`);
    enter('.hero', host); return;
  }
  const t = V.totals, days = V.days;

  host.innerHTML = `
${hero('交付', '说过的话，有多少变成了东西', `左边是你在本机说的话，右边是 GitHub 上真提交的代码。
  两边谁都不知道对方存在 —— 所以对出来的差距是真的。`)}
${grid([
  { k: '只聊没交付', v: `${t.days_talk_only} 天`, n: `有会话的一共 ${t.days_talked} 天`, w: 3, tone: 'warn' },
  { k: '两边都有的日子占', v: pct(t.overlap_rate), n: `重合 ${t.days_both} 天`, w: 3, alt: true },
  { k: '会话', v: String(t.sessions), n: `真交付的天数 ${t.days_shipped}` },
  { k: '提交', v: String(t.commits), n: `只交付没聊 ${t.days_ship_only} 天` },
  { k: '每场会话换来', v: String(t.commits_per_session), n: '条提交', tone: 'acc' },
])}
${warn(`<b>「只聊没交付」不等于白干。</b>那天可能在读、在想、在做不进 git 的事 —— Excel、方案、剪视频都不会留下提交。
  但它仍然是「造东西 : 交出去」最直接的证据，而且是两个互不知情的来源对出来的，不是我推的。`)}

${sec('说的话 vs 交的东西', '上半截是会话，下半截是提交。中间那条线是同一天。')}
<div class="slab" style="padding:10px 12px 6px"><canvas class="viz" id="cv" style="border:0;background:none" role="img" aria-label="会话与提交的逐日对照图。逐日明细见下方表格。"></canvas></div>

${sec('哪个仓在动')}
${orbit((G.repos || []).map(r => ({ k: r.repo, v: r.commits,
  label: `${r.commits} 提交 · ${r.merged}/${r.prs} PR · ${r.releases} 个发布`,
  c: r.private ? 'var(--acc2)' : 'var(--acc)' })))}

${sec('话 ↔ 仓', '会话里的项目名能和仓名对上，才算「这些话变成了这些提交」。对不上的不硬凑。')}
${orbit((V.projects || []).map(r => ({ k: r.project, v: r.sessions,
  label: `聊 ${r.sessions} 场 → 提交 ${r.commits} 条（每场 ${r.per_session}）`, c: 'var(--ok)' })))}
${(V.unmatched_projects || []).length ? warn(`<b>对不上仓名的：</b>
  ${V.unmatched_projects.map(x => `${esc(x.project)}（${x.sessions} 场）`).join('、')}
  —— 这些留在这里，不硬塞进某个仓。`) : ''}

${drawer('摊开逐日明细（最近 60 天）', table(
  [{ t: '日期' }, { t: '会话', r: true }, { t: '你说话', r: true }, { t: '提交', r: true },
   { t: 'PR', r: true }, { t: '已合', r: true }, { t: '动了哪些仓' }],
  days.slice(-60).reverse().map(r => [`<span class="lnk" data-day="${r.d}">${r.d}</span>`,
    String(r.sessions), String(r.turns), r.commits ? `<b>${r.commits}</b>` : '0',
    String(r.prs), String(r.merged),
    Object.entries(r.repos || {}).map(([k, v]) => pill(`${k} ${v}`)).join('')])))}
<p class="hint">${esc(V.note)}</p>`;

  const cv = host.querySelector('#cv');
  const draw = () => {
    const H = 250, { ctx, w } = fitCanvas(cv, H);
    const rows = days.slice(-90), bw = w / Math.max(1, rows.length), mid = H / 2;
    ctx.clearRect(0, 0, w, H);
    const maxS = Math.max(1, ...rows.map(r => r.sessions)), maxC = Math.max(1, ...rows.map(r => r.commits));
    ctx.globalCompositeOperation = 'lighter';
    rows.forEach((r, i) => {
      const x = i * bw + bw / 2;
      const bar = (val, max, up, col) => {
        if (!val) return;
        const bh = (val / max) * (mid - 22);
        const g = up ? ctx.createLinearGradient(0, mid - bh, 0, mid)
                     : ctx.createLinearGradient(0, mid, 0, mid + bh);
        g.addColorStop(0, up ? col : col); g.addColorStop(1, 'transparent');
        ctx.fillStyle = g; ctx.globalAlpha = .88;
        ctx.beginPath();
        ctx.roundRect(x - bw * .34, up ? mid - bh : mid, Math.max(1.5, bw * .68), bh, 3);
        ctx.fill();
      };
      bar(r.sessions, maxS, true, cssVar('--acc'));
      bar(r.commits, maxC, false, cssVar('--ok'));
    });
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
    ctx.strokeStyle = cssVar('--line');
    ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(w, mid); ctx.stroke();
    ctx.fillStyle = cssVar('--dim2'); ctx.font = '11px -apple-system, system-ui, sans-serif';
    ctx.fillText('说的话 ↑', 6, 15);
    ctx.fillText('交的东西 ↓', 6, H - 6);
  };
  draw();
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  host.addEventListener('mouseover', e => {
    const d = e.target.closest('[data-day]'); if (d) flyToDay(d.dataset.day);
  });
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day);
  });
  enter('.hero, .sec, .cell, .orow, .slab', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
