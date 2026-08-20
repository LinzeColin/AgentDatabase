import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 交付与 ROI。头条是「聊了多少天里真正交付了几天」——
// 这个比例是两个互不知情的来源对出来的，不是推的。
export async function render(host) {
  const V = D.A().delivery || {};
  if (V.state !== '通') {
    host.innerHTML = stage({ eyebrow: '经济 · 交付', title: '交付', hint: `状态：${esc(V.state || '不确定')}。${esc(V.why || '')}` });
    return;
  }
  const t = V.totals, DN = V.denominators || {};
  hud([{ k: '提交', v: String(t.commits) }, { k: '合并 PR', v: String(t.merged ?? '—') }]);

  host.innerHTML = stage({
    eyebrow: '经济 · 交付与 ROI',
    title: '聊了多少天，真的交出去了几天',
    hint: '会话记录只能证明你<b>在做</b>，GitHub 才能证明你<b>做出来了</b>。两条曲线放一起，那个比例才不是自说自话。',
    body: headline('聊过又交付的天数占比', pct(t.overlap_rate),
      `${t.days_both} 天两样都有 · ${t.days_talk_only} 天只聊没交付`)
      + reads([
        { k: '提交', v: String(t.commits), n: `每场 ${t.commits_per_session}` },
        { k: '合并 PR', v: String(t.merged ?? '—'), n: t.merge_rate != null ? `合并率 ${pct(t.merge_rate)}` : '' },
        { k: '一个 PR 几条提交', v: String(t.commits_per_merged ?? '—'), n: 'commit 粒度不均匀' },
        { k: '只交付没聊', v: String(t.days_ship_only), n: '手写的那部分' },
      ])
      + (DN.note ? warn(`<b>两个分母并列，不替换。</b>${esc(DN.note)}<br>
          commit：${esc(DN.commit.caveat)}<br>merged PR：${esc(DN.merged_pr.caveat)}`) : '')
      + `<p class="hint" style="margin-top:22px">按项目 —— 会话里提到的项目名与仓名能对上的才算。</p>`
      + beams((V.projects || []).map(p => ({
          k: p.project, v: p.commits, sub: `${p.sessions} 场会话`,
          label: `${p.commits} 提交　每场 ${p.per_session}`, c: 'var(--acc3)',
        })))
      + ((V.unmatched_projects || []).length ? sheet('项目名和仓名对不上的（不硬凑）',
          table([{ t: '项目' }, { t: '会话', r: true }],
            V.unmatched_projects.map(p => [esc(p.project), String(p.sessions)]))) : '')
      + sheet('按天', table([{ t: '日期' }, { t: '会话', r: true }, { t: '提交', r: true }, { t: 'PR', r: true }, { t: '合并', r: true }],
          V.days.slice().reverse().slice(0, 90).map(d => [esc(d.d), String(d.sessions),
            String(d.commits), String(d.prs), String(d.merged)]))),
  });
  enter('.headline, .read, .beam, .warnbox', host);
}
