import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, kv, table, meter, spark, warn, state } from '../kit.js';
import { cssVar } from '../../../core/g3d.js';

// 会话记录只能证明你在做，GitHub 才能证明你做出来了。这一屏把两条曲线并排。
export async function render(host) {
  const V = D.A().delivery || {}, G = D.A().github || {};
  if (V.state !== '通') {
    host.innerHTML = sec('DELIVERY') + warn(`<b>状态：不确定。</b>${esc(V.why || '没有 GitHub 数据')}<br>
      每日流水线里 <code>github.py</code> 拉取失败时会走到这里 —— 不会拿一个空壳假装有数据。`);
    return;
  }
  const t = V.totals, days = V.days;

  host.innerHTML = `
${sec('DELIVERY', '两个独立来源：本机会话记录证明你在做，GitHub 提交证明你做出来了。')}
${kv([
  ['有会话的天', String(t.days_talked), ''],
  ['有提交的天', String(t.days_shipped), ''],
  ['两者都有', String(t.days_both), 'acc'],
  ['只聊没交付', String(t.days_talk_only), 'warn'],
  ['只交付没聊', String(t.days_ship_only), ''],
  ['重合率', pct(t.overlap_rate), 'acc'],
  ['会话总数', String(t.sessions), ''],
  ['提交总数', String(t.commits), ''],
  ['每场会话产出', t.commits_per_session + ' 条提交', 'warn'],
])}
${warn(`<b>「只聊没交付」不等于白干。</b>那天可能在读、在想、在做仓外的事（Excel、方案、视频都不进 git）。
  但它是「建设 : 交付」那个比例最直接的证据 —— 而且是两个互不知情的数据源对出来的，不是我推的。
  ${G.failed_repos && G.failed_repos.length ? `另有 ${G.failed_repos.length} 个仓拉取失败，已标不确定。` : ''}`)}

${sec('SESSIONS vs COMMITS', '按天并排。上排是你开的会话，下排是当天属于你的提交。')}
<canvas class="viz" id="cv" height="230"></canvas>
<p class="hint">最近 60 天　会话 ${spark(days.slice(-60).map(r => r.sessions))}　提交 ${spark(days.slice(-60).map(r => r.commits))}</p>

${sec('BY REPO')}
${table([{ t: '仓' }, { t: '私有' }, { t: '提交', r: true }, { t: 'PR', r: true }, { t: '已合', r: true },
         { t: 'Release', r: true }, { t: '最后推送' }, { t: '' }],
  (G.repos || []).map(r => [esc(r.repo), r.private ? '是' : '否', String(r.commits),
    String(r.prs), String(r.merged), String(r.releases), `<span class="tag">${esc(r.pushed || '—')}</span>`,
    meter(r.commits, Math.max(1, ...(G.repos || []).map(x => x.commits)), 100)]))}

${sec('PROJECT ↔ REPO', '会话里的项目名能和仓名对上的，才能算「这些话变成了这些提交」。')}
${table([{ t: '项目' }, { t: '仓' }, { t: '会话', r: true }, { t: '提交', r: true }, { t: '每场提交', r: true }],
  (V.projects || []).map(r => [esc(r.project), esc(r.repo), String(r.sessions), String(r.commits),
    `<b>${r.per_session}</b>`]))}
${(V.unmatched_projects || []).length ? warn(`<b>对不上仓名的项目（会话 ≥3）：</b>
  ${V.unmatched_projects.map(x => `${esc(x.project)}（${x.sessions}）`).join('、')}。
  不硬凑 —— 它们要么不是 git 项目，要么在别的账号下。`) : ''}

${sec('DAY BY DAY', '最近 60 天。')}
${table([{ t: '日期' }, { t: '会话', r: true }, { t: '你说话', r: true }, { t: '提交', r: true },
         { t: 'PR', r: true }, { t: '已合', r: true }, { t: 'Release', r: true }, { t: '碰过的仓' }],
  days.slice(-60).reverse().map(r => [
    `<span class="lnk" data-day="${r.d}">${r.d}</span>`, String(r.sessions), String(r.turns),
    r.commits ? `<b>${r.commits}</b>` : '<span class="tag">0</span>',
    String(r.prs), String(r.merged), String(r.releases),
    Object.entries(r.repos || {}).map(([k, v]) => `<span class="tag">${esc(k)} ${v}</span>`).join('')]))}
<p class="hint">${esc(V.note)}</p>`;

  const cv = host.querySelector('#cv');
  const css = k => cssVar(k);
  const draw = () => {
    const dpr = Math.min(2, devicePixelRatio || 1);
    const w = Math.max(200, cv.clientWidth), h = 230;
    cv.width = w * dpr; cv.height = h * dpr;
    const ctx = cv.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const rows = days.slice(-90);
    const bw = w / Math.max(1, rows.length);
    const mid = h / 2, maxS = Math.max(1, ...rows.map(r => r.sessions)), maxC = Math.max(1, ...rows.map(r => r.commits));
    ctx.strokeStyle = css('--hair'); ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(w, mid); ctx.stroke();
    rows.forEach((r, i) => {
      const x = i * bw;
      if (r.sessions) {
        ctx.fillStyle = css('--acc');
        const bh = (r.sessions / maxS) * (mid - 16);
        ctx.fillRect(x, mid - bh, Math.max(1, bw - 1), bh);
      }
      if (r.commits) {
        ctx.fillStyle = css('--ok');
        const bh = (r.commits / maxC) * (mid - 16);
        ctx.fillRect(x, mid, Math.max(1, bw - 1), bh);
      }
    });
    ctx.fillStyle = css('--dim2'); ctx.font = '10px ui-monospace, monospace';
    ctx.fillText('会话 ↑', 4, 12); ctx.fillText('提交 ↓', 4, h - 5);
    const step = Math.ceil(rows.length / 10);
    rows.forEach((r, i) => { if (i % step === 0) ctx.fillText(r.d.slice(5), i * bw, mid + 11); });
  };
  draw();
  const onR = () => draw();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  enter('.sec, .kv > div, tbody tr', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
