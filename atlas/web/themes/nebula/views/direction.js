import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, hud } from '../kit.js';

export async function render(host) {
  const V = D.A().direction;
  if (!V) { host.innerHTML = stage({ title: '方向', hint: '这一版还没有这块数据' }); return; }
  const broken = (V.chain || []).find(c => c.state === '断了');
  hud([{ k: '断口', v: broken ? esc(broken.step.replace(/^[①-⑤]\s*/, '')) : '没认出' }]);

  host.innerHTML = stage({
    eyebrow: '概览 · 方向',
    title: '从造出来到换到钱，断在哪一环',
    hint: esc(V.verdict),
    body: headline(broken ? '第一个断口' : '链条状态',
      broken ? esc(broken.value) : '说不准',
      broken ? esc(broken.step) : '')
      + reads((V.chain || []).map(c => ({
          k: c.step, v: esc(c.value), size: 'sm',
          tone: c.state === '断了' ? 'warn' : (c.state === '通' ? 'acc' : ''),
          n: esc(c.state) })))
      + (broken ? warn(`<b>下一步</b><br>${esc(V.next_action)}`) : '')
      + `<p class="hint" style="margin-top:24px">九个切片，同一套定义，可以横着比。</p>`
      + beams((V.rows || []).map(r => ({
          k: r.label, v: r.human,
          sub: `${(r.top_topics || []).join('、')}　${r.projects} 个项目`,
          label: `造→交 ${r.build_to_ship == null ? '—' : pct(r.build_to_ship)}　交→换钱 ${
            r.ship_to_money == null ? '—' : pct(r.ship_to_money)}`,
          c: 'var(--acc2)' })))
      + warn(esc(V.note))
      + sheet('三个词各自的定义', Object.entries(V.definitions || {})
          .map(([k, v]) => `<p><b>${esc(k)}</b>：${esc(v)}</p>`).join(''))
      + sheet('切片明细', table(
          [{ t: '切片' }, { t: '你开口', r: true }, { t: '项目', r: true }, { t: '主题', r: true },
           { t: '进来了' }, { t: '出去了' }],
          (V.rows || []).map(r => [esc(r.label), String(r.human), String(r.projects),
            String(r.topics_n), (r.entered || []).join('、') || '—', (r.left || []).join('、') || '—']))),
  });
  enter('.headline, .read, .beam, .warnbox', host);
}
