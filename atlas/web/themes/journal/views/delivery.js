import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, lede, p, n, big, aside, note, figure, rank, spark, table } from '../kit.js';

export async function render(host) {
  const V = D.A().delivery || {}, G = D.A().github || {};
  if (V.state !== '通') {
    host.innerHTML = sec('交付') + note(`<b>状态：不确定。</b>${esc(V.why || '没有 GitHub 数据')}`);
    return;
  }
  const t = V.totals, days = V.days;
  host.innerHTML = `
${sec('交付')}
${lede(`会话记录只能证明你<b>在做</b>，GitHub 才能证明你<b>做出来了</b>。
  把两边并起来数：有会话的日子 ${big(t.days_talked)} 天，有提交的日子只有 ${big(t.days_shipped)} 天，
  两者都有的 ${n(t.days_both)} 天 —— 也就是说，有 ${big(t.days_talk_only)} 天你聊了，但那天一条提交都没有。`)}
${aside(`重合率 ${pct(t.overlap_rate)}。<br>${n(t.sessions)} 场会话 → ${n(t.commits)} 条提交，
  平均每场 <b>${t.commits_per_session}</b> 条。`)}
${note(`<b>「只聊没交付」不等于白干。</b>那天可能在读、在想、在做仓外的事 —— Excel、方案、视频都不进 git。
  但这是「建设 : 交付」最直接的证据，而且是两个互不知情的数据源对出来的，不是推的。`)}
${p(`最近六十天，会话的起伏是 ${spark(days.slice(-60).map(r => r.sessions))}，
  提交的起伏是 ${spark(days.slice(-60).map(r => r.commits))}。两条线什么时候合上、什么时候分开，一眼能看出来。`)}

${sec('按仓')}
${figure(rank((G.repos || []).map(r => ({ k: r.repo, v: r.commits,
  label: `${r.commits} 提交 · ${r.merged}/${r.prs} PR · ${r.releases} Release` }))),
  `${G.totals ? G.totals.repos : 0} 个仓，共 ${G.totals ? G.totals.commits : 0} 条属于你的提交。`)}

${sec('项目 ↔ 仓')}
${p(`会话里的项目名能和仓名对上的，才算「这些话变成了这些提交」：`)}
${figure(rank((V.projects || []).map(r => ({ k: `${r.project} → ${r.repo}`, v: r.sessions,
  label: `会话 ${r.sessions} → 提交 ${r.commits}（每场 ${r.per_session}）` }))), '能对上的项目。')}
${(V.unmatched_projects || []).length ? aside(`对不上仓名的：
  ${V.unmatched_projects.map(x => esc(x.project)).join('、')} —— 不硬凑。`) : ''}

${sec('逐日')}
${figure(table([{ t: '日期' }, { t: '会话', r: true }, { t: '你说话', r: true }, { t: '提交', r: true },
  { t: 'PR', r: true }, { t: '已合', r: true }, { t: '碰过的仓' }],
  days.slice(-50).reverse().map(r => [`<span class="lnk" data-day="${r.d}">${r.d}</span>`,
    String(r.sessions), String(r.turns), r.commits ? `<b>${r.commits}</b>` : '0',
    String(r.prs), String(r.merged),
    Object.entries(r.repos || {}).map(([k, v]) => `<span class="kw">${esc(k)} ${v}</span>`).join('')])),
  esc(V.note))}`;
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  enter('.sec, p.body, figure, .aside', host);
}
