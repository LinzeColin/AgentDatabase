import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 转化。头条是「有没有一个动作的收件人不是我自己」——
// 它很可能是 0，**0 才是它的价值**。
export async function render(host) {
  const C = D.A().compounding, O = D.A().outward;
  if (!C) { host.innerHTML = stage({ title: '转化', hint: '这一版的数据里还没有成果复利投影。' }); return; }
  const S = C.stage_labels || {};

  hud(O ? [{ k: `近 ${O.window_days} 天对外`, v: esc(O.headline.state) }] : []);

  host.innerHTML = stage({
    eyebrow: '档案 · 转化',
    title: '有没有一个动作的收件人不是我自己',
    hint: `下面所有的数回答的都是「我做了多少」。<b>只有这一块回答「有没有走出去」。</b>
           它上来就很大说明判据写错了，不是说明干得好。`,
    body: (O ? headline(`过去 ${O.window_days} 天走出去过吗`, esc(O.headline.state), esc(O.headline.basis))
      + reads([
        { k: '公开仓', v: `${O.public_repos} / ${O.repos_total}`, n: '能被别人看到的那几个' },
      ].concat((O.signals || []).filter(x => x.strength !== 'hard').map(x => ({
        k: x.label, size: 'sm', v: esc(x.state), n: x.n_all == null ? '没信号源' : `全期 ${x.n_all} 次`,
      }))))
      + warn(`<b>这三件事这里测不到，别把上面的数读成它们：</b><br>${(O.not_measurable || []).map(esc).join('<br>')}`)
      : '')
      + (C.champion ? `<p class="hint" style="margin-top:26px">这周最值得转化的一件事 —— 现在这一步：
          <b style="color:var(--acc)">${esc(S[C.champion.stage] || C.champion.stage)}</b></p>
          <p class="hint"><b>${esc(C.champion.problem || '—')}</b><br>${esc(C.champion.why_now || '')}</p>` : '')
      + beams((C.stages || []).map(st => ({
          k: S[st.stage] || st.stage, v: st.n, label: `${st.n} 条`, c: 'var(--acc2)',
        })))
      + sheet('做了很多但还没变成结果', table(
          [{ t: '事' }, { t: '证据' }],
          (C.debt || []).map(x => [`<b>${esc(x.title || x.problem || '—')}</b>`,
            esc((x.evidence || []).join('；').slice(0, 120) || '—')])))
      + (C.clamps && C.clamps.length ? sheet(`被压回去的 ${C.clamps.length} 条`, table(
          [{ t: '事' }, { t: '声称' }, { t: '压到' }, { t: '为什么' }],
          C.clamps.map(x => [esc(x.id || '—'), esc(x.claimed || '—'), esc(x.ceiling || '—'), esc(x.reason || '—')]))) : ''),
  });
  enter('.headline, .read, .beam, .warnbox', host);
}
