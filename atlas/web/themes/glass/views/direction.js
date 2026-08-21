import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, bento, orbit, drawer, table, warn, pill, state } from '../kit.js';

// 方向 / 路径 / 范围。**这一屏回答的是你最初那句 prompt 的最后一句**：
// 「三个月了，我依旧不能用它去创造实际的经济价值，去帮我赚钱。」
// 所以链条放在最前面 —— 先看断在哪，再看九个切片。
export async function render(host) {
  const V = D.A().direction;
  if (!V) { host.innerHTML = sec('方向', '这一版还没有这块数据'); enter('.sec', host); return; }
  const broken = (V.chain || []).find(c => c.state === '断了');

  host.innerHTML = `
${sec('从造出来到换到钱，断在哪一环', V.verdict)}
${bento((V.chain || []).map((c, i, a) => ({
  kHtml: `${state(c.state)}　${esc(c.step)}`, k: c.step,
  v: esc(c.value), size: 'sm', n: esc(c.why),
  w: i === a.length - 1 && a.length % 2 ? 6 : 3,
  tone: c.state === '断了' ? 'warn' : (c.state === '通' ? 'acc' : ''),
})))}
${broken ? warn(`<b>下一步</b><br>${esc(V.next_action)}`) : ''}

${sec('方向 / 路径 / 范围', Object.entries(V.definitions || {})
  .map(([k, v]) => `<b>${esc(k)}</b>：${esc(v)}`).join('<br>'))}
${warn(esc(V.note))}
${table(
  [{ t: '切片' }, { t: '你开口', r: true }, { t: '项目', r: true }, { t: '主题', r: true },
   { t: '最重的三件事' }, { t: '进来了' }, { t: '出去了' },
   { t: '造→交', r: true }, { t: '交→换钱', r: true }],
  (V.rows || []).map(r => [
    `<b>${esc(r.label)}</b><div class="hint">${esc(r.from || '')} 起</div>`,
    String(r.human), String(r.projects), String(r.topics_n),
    (r.top_topics || []).map(t => pill(t)).join(''),
    (r.entered || []).map(t => pill(t)).join('') || '—',
    (r.left || []).map(t => pill(t)).join('') || '—',
    r.build_to_ship == null ? '—' : pct(r.build_to_ship),
    r.ship_to_money == null ? '—' : pct(r.ship_to_money)]))}
${V.widest ? warn(`<b>范围最宽的一段是「${esc(V.widest.label)}」</b> —— ${V.widest.projects} 个项目、${V.widest.topics_n} 个主题。
  范围宽不等于走得远：上面那张表里「交→换钱」那一列才是走得远不远。`) : ''}
${V.repeats_debt ? warn(`<b>另外还有 ${V.repeats_debt} 组问题隔天又问了一遍。</b>
  它们不在这条链上，但每一组都是一次重复付出的 token。`) : ''}`;
  enter('.sec, .card, tbody tr', host);
}
