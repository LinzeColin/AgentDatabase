import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, seal } from '../kit.js';

// 方向 / 路径 / 范围。三页：断在哪 → 九个切片 → 三个词的定义。
export async function render(host) {
  const V = D.A().direction;
  if (!V) { host.innerHTML = leaf({ title: '方向', lead: '这一版还没有这块数据' }); return; }
  const broken = (V.chain || []).find(c => c.state === '断了');

  host.innerHTML =
    leaf({
      title: '从造出来到换到钱，断在哪一环',
      lead: esc(V.verdict),
      body: (broken ? plate({ k: '第一个断口', v: esc(broken.step), size: 'sm', big: true,
        n: `${esc(broken.value)} —— ${esc(broken.why)}` }) : '')
        + plates((V.chain || []).map(c => ({
            k: c.step, v: `${esc(c.value)}`, size: 'sm',
            n: `${c.state}　${esc(c.why)}` })))
        + (broken ? warn(`<b>下一步</b><br>${esc(V.next_action)}`) : '')
        + (V.repeats_debt ? marginal(`另外还有 <b>${V.repeats_debt}</b> 组问题隔天又问了一遍。
            它们不在这条链上，但每一组都是一次重复付出的 token。`) : ''),
    })
    + leaf({
      title: '九个切片', lead: esc(V.note), cols: false,
      body: rub(
        [{ t: '切片' }, { t: '你开口', r: true }, { t: '项目', r: true }, { t: '主题', r: true },
         { t: '最重的三件事' }, { t: '造→交', r: true }, { t: '交→换钱', r: true }],
        (V.rows || []).map(r => [`<b>${esc(r.label)}</b>`, String(r.human), String(r.projects),
          String(r.topics_n), esc((r.top_topics || []).join('、')),
          r.build_to_ship == null ? '—' : pct(r.build_to_ship),
          r.ship_to_money == null ? '—' : pct(r.ship_to_money)]))
        + h2('主题的进出')
        + rub([{ t: '切片' }, { t: '进来了' }, { t: '出去了' }],
            (V.rows || []).map(r => [esc(r.label),
              esc((r.entered || []).join('、')) || '—', esc((r.left || []).join('、')) || '—'])),
    })
    + leaf({
      title: '这三个词各自是什么意思',
      lead: '先定义再计算 —— 否则就是又三个说不清的指标。',
      body: Object.entries(V.definitions || {}).map(([k, v]) =>
        plate({ k, v: esc(v), size: 'sm', plain: true, big: true })).join('')
        + (V.widest ? marginal(`范围最宽的一段是「${esc(V.widest.label)}」——
            ${V.widest.projects} 个项目、${V.widest.topics_n} 个主题。
            <b>范围宽不等于走得远</b>：走得远不远看「交→换钱」那一列。`) : ''),
    });
}
