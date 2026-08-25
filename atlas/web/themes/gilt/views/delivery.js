import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

export async function render(host) {
  const V = D.A().delivery || {};
  if (V.state !== '通') {
    host.innerHTML = leaf({ title: '交付', lead: `状态：${esc(V.state || '不确定')}。${esc(V.why || '')}` });
    return;
  }
  const t = V.totals, DN = V.denominators || {};
  host.innerHTML =
    leaf({
      title: '聊了多少天，真的交出去了几天',
      lead: `会话记录只能证明你<b>在做</b>，GitHub 才能证明你<b>做出来了</b>。
             两条曲线放一起，那个比例才不是自说自话。`,
      body: plate({ k: '聊过又交付的天数占比', v: pct(t.overlap_rate), big: true,
        n: `${t.days_both} 天两样都有 · ${t.days_talk_only} 天只聊没交付` })
        + plates([
          { k: '提交', v: String(t.commits), n: `每场 ${t.commits_per_session}` },
          { k: '合并 PR', v: String(t.merged ?? '—'), n: t.merge_rate != null ? `合并率 ${pct(t.merge_rate)}` : '' },
          { k: '一个 PR 几条提交', v: String(t.commits_per_merged ?? '—'), n: 'commit 粒度不均匀' },
          { k: '只交付没聊', v: String(t.days_ship_only), n: '手写的那部分' },
        ])
        + (DN.note ? marginal(`<b>两个分母并列，不替换。</b>${esc(DN.note)}<br>
            commit：${esc(DN.commit.caveat)}<br>merged PR：${esc(DN.merged_pr.caveat)}`) : ''),
    })
    + leaf({
      title: '按项目与按天', lead: '会话里提到的项目名与仓名能对上的才算，对不上的单独列，不硬凑。',
      cols: false,
      body: carve((V.projects || []).map(p => ({
          k: p.project, v: p.commits, label: `${p.commits} 提交　${p.sessions} 场　每场 ${p.per_session}`,
        })))
        + ((V.unmatched_projects || []).length ? h2('对不上的') + rub([{ t: '项目' }, { t: '会话', r: true }],
            V.unmatched_projects.map(p => [esc(p.project), String(p.sessions)])) : '')
        + h2('按天')
        + rub([{ t: '日期' }, { t: '会话', r: true }, { t: '提交', r: true }, { t: 'PR', r: true }, { t: '合并', r: true }],
            V.days.slice().reverse().slice(0, 60).map(d => [esc(d.d), String(d.sessions),
              String(d.commits), String(d.prs), String(d.merged)])),
    });
}
