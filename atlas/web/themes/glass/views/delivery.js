import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas , cssVar } from '../../../core/g3d.js';
import { sec, bento, orbit, drawer, table, warn, pill, state } from '../kit.js';

export async function render(host) {
  const V = D.A().delivery || {}, G = D.A().github || {};
  if (V.state !== '通') {
    host.innerHTML = sec('交付') + warn(`<b>状态：说不准。</b>${esc(V.why || '没有 GitHub 数据')}`);
    return;
  }
  const t = V.totals, days = V.days;
  host.innerHTML = `
${sec('交付', '两个独立来源：本机会话证明你在做，GitHub 提交证明你做出来了。')}
${bento([
  { k: '只聊没交付', v: `${t.days_talk_only} 天`, n: `有会话的 ${t.days_talked} 天里`, w: 3, tone: 'warn' },
  { k: '重合率', v: pct(t.overlap_rate), n: `两者都有 ${t.days_both} 天`, w: 3, alt: true },
  { k: '会话', v: String(t.sessions), n: `有提交的天 ${t.days_shipped}` },
  { k: '提交', v: String(t.commits), n: `只交付没聊 ${t.days_ship_only} 天` },
  { k: '每场会话产出', v: t.commits_per_session, n: '条提交', tone: 'acc' },
])}
${warn(`<b>「只聊没交付」不等于白干。</b>那天可能在读、在想、在做仓外的事（Excel、方案、视频都不进 git）。
  但它是「建设 : 交付」最直接的证据 —— 而且是两个互不知情的数据源对出来的。`)}
${sec('会话 vs 提交', '上半是会话，下半是提交。')}
<canvas class="viz" id="cv" height="240"></canvas>
${sec('按仓')}
${orbit((G.repos || []).map(r => ({ k: r.repo, v: r.commits,
  label: `${r.commits} 提交 · ${r.merged}/${r.prs} PR · ${r.releases} Release`,
  c: r.private ? 'var(--acc2)' : 'var(--acc)' })))}
${sec('项目 ↔ 仓', '会话里的项目名能和仓名对上的，才能算「这些话变成了这些提交」。')}
${orbit((V.projects || []).map(r => ({ k: r.project, v: r.sessions,
  label: `会话 ${r.sessions} → 提交 ${r.commits}（每场 ${r.per_session}）`, c: 'var(--ok)' })))}
${(V.unmatched_projects || []).length ? warn(`<b>对不上仓名的：</b>
  ${V.unmatched_projects.map(x => `${esc(x.project)}（${x.sessions}）`).join('、')} —— 不硬凑。`) : ''}
${drawer('展开逐日明细（最近 60 天）', table(
  [{ t: '日期' }, { t: '会话', r: true }, { t: '你说话', r: true }, { t: '提交', r: true },
   { t: 'PR', r: true }, { t: '已合', r: true }, { t: '碰过的仓' }],
  days.slice(-60).reverse().map(r => [`<span class="lnk" data-day="${r.d}">${r.d}</span>`,
    String(r.sessions), String(r.turns), r.commits ? `<b>${r.commits}</b>` : '0',
    String(r.prs), String(r.merged),
    Object.entries(r.repos || {}).map(([k, v]) => pill(`${k} ${v}`)).join('')])))}
<p class="hint">${esc(V.note)}</p>`;

  const cv = host.querySelector('#cv');
  const css = k => cssVar(k);
  const draw = () => {
    const { ctx, w } = fitCanvas(cv, 240);
    const h = 240, rows = days.slice(-90), bw = w / Math.max(1, rows.length), mid = h / 2;
    ctx.clearRect(0, 0, w, h);
    const maxS = Math.max(1, ...rows.map(r => r.sessions)), maxC = Math.max(1, ...rows.map(r => r.commits));
    ctx.globalCompositeOperation = 'lighter';
    rows.forEach((r, i) => {
      const x = i * bw + bw / 2;
      if (r.sessions) {
        const bh = (r.sessions / maxS) * (mid - 20), c = css('--acc');
        const g = ctx.createLinearGradient(0, mid - bh, 0, mid);
        g.addColorStop(0, c); g.addColorStop(1, 'transparent');
        ctx.fillStyle = g; ctx.globalAlpha = .85;
        ctx.beginPath(); ctx.roundRect(x - bw * .34, mid - bh, Math.max(1.5, bw * .68), bh, 3); ctx.fill();
      }
      if (r.commits) {
        const bh = (r.commits / maxC) * (mid - 20), c = css('--ok');
        const g = ctx.createLinearGradient(0, mid, 0, mid + bh);
        g.addColorStop(0, c); g.addColorStop(1, 'transparent');
        ctx.fillStyle = g; ctx.globalAlpha = .85;
        ctx.beginPath(); ctx.roundRect(x - bw * .34, mid, Math.max(1.5, bw * .68), bh, 3); ctx.fill();
      }
    });
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
    ctx.strokeStyle = css('--line'); ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(w, mid); ctx.stroke();
    ctx.fillStyle = css('--dim2'); ctx.font = '11px -apple-system, system-ui, sans-serif';
    ctx.fillText('会话 ↑', 6, 15); ctx.fillText('提交 ↓', 6, h - 6);
  };
  draw();
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  enter('.sec, .card, .orow', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
