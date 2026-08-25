import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

export async function render(host) {
  const C = D.A().compounding, O = D.A().outward;
  if (!C) { host.innerHTML = leaf({ title: '转化', lead: '这一版的数据里还没有成果复利投影。' }); return; }
  const S = C.stage_labels || {};

  host.innerHTML =
    (O ? leaf({
      title: '有没有一个动作的收件人不是我自己',
      lead: `其余每一页回答的都是「我做了多少」。<b>只有这一页回答「有没有走出去」。</b>
             它上来就很大说明判据写错了，不是说明干得好。`,
      body: plate({ k: `过去 ${O.window_days} 天走出去过吗`, v: esc(O.headline.state), big: true,
        n: esc(O.headline.basis) })
        + plates([{ k: '公开仓', v: `${O.public_repos} / ${O.repos_total}`, n: '能被别人看到的那几个' }]
          .concat((O.signals || []).filter(x => x.strength !== 'hard').map(x => ({
            k: x.label, v: esc(x.state), size: 'sm',
            n: x.n_all == null ? '没信号源' : `全期 ${x.n_all} 次`,
          }))))
        + warn(`<b>这三件事这里测不到，别把上面的数读成它们：</b><br>${(O.not_measurable || []).map(esc).join('<br>')}`),
    }) : '')
    + (C.champion ? leaf({
      title: '这周最值得转化的一件事',
      lead: `现在这一步：<b>${esc(S[C.champion.stage] || C.champion.stage)}</b>`,
      body: plate({ k: '是什么', v: esc(C.champion.problem || '—'), size: 'sm', big: true, plain: true,
        n: esc(C.champion.why_now || '') })
        + (C.champion.next_7d ? marginal(`<b>7 天要做的</b><br>${esc(C.champion.next_7d)}`) : '')
        + (C.champion.next_30d ? marginal(`<b>30 天要看到的</b><br>${esc(C.champion.next_30d)}`) : '')
        + (C.champion.stop_rule ? marginal(`<b>什么情况下停手</b><br>${esc(C.champion.stop_rule)}`) : ''),
    }) : '')
    + leaf({
      title: '漏斗', lead: esc(C.clamp_note || ''), cols: false,
      body: carve((C.stages || []).map(st => ({ k: S[st.stage] || st.stage, v: st.n, label: `${st.n} 条` })))
        + h2('做了很多，但还没变成结果')
        + rub([{ t: '事' }, { t: '证据' }],
            (C.debt || []).map(x => [`<b>${esc(x.title || x.problem || '—')}</b>`,
              esc((x.evidence || []).join('；').slice(0, 110) || '—')]))
        + ((C.clamps || []).length ? h2(`被压回去的 ${C.clamps.length} 条`)
          + rub([{ t: '事' }, { t: '声称' }, { t: '压到' }, { t: '为什么' }],
              C.clamps.map(x => [esc(x.id || '—'), esc(x.claimed || '—'), esc(x.ceiling || '—'), esc(x.reason || '—')]))
          : marginal('<b>这一轮没有被压回去的条目。</b>声称的等级都有证据撑得住。')),
    });
}
