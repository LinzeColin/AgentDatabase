import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// Token 与栈。**这一屏的头条是成本口径，不是总量** ——
// 总量看着大，但旧口径只覆盖其中一小部分，那才是要先讲的事。
export async function render(host) {
  const K = D.A().stack, T = D.tokens(), t = T.total;
  const C = T.cost || {}, A = T.attribution || {}, F = T.fanout || {};
  const llm = K.harness.filter(r => r.kind === 'llm');

  hud([
    { k: '缓存命中率', v: rate(t.hit_rate) },
    { k: '输入(含缓存)', v: fmt(t.input_total) },
  ]);

  host.innerHTML = stage({
    eyebrow: '经济 · Token 与栈',
    title: '钱花在看不见的那一栏',
    hint: `旧口径 <code>成本 = 输入 + 输出</code>，只看得到十分之一的账单 ——
           而缓存读取才是大头。<b>下面这个百分比是这一屏的全部重点。</b>`,
    body: headline('旧口径能看到的成本', C.coverage_by_cost != null ? pct(C.coverage_by_cost) : '说不准',
      C.coverage_by_volume != null ? `按 token 条数算只有 ${pct(C.coverage_by_volume)} —— 只看条数会以为没漏` : '')
      + reads([
        { k: '价格加权 token', v: fmt(C.bie_total || 0), tone: 'acc', n: 'BIE，无量纲、跨时间可比' },
        { k: '缓存读取占成本', v: C.bie_total ? pct(C.by_field.cache_read / C.bie_total) : '—', n: fmt((C.by_field || {}).cache_read || 0) },
        { k: '缓存写入', v: fmt((C.by_field || {}).cache_write || 0), n: '单价最高的那类输入' },
        { k: '没量到 token', v: `${(C.no_usage || {}).sessions ?? '—'} 场`, n: '不是没花钱，是日志里没记' },
      ])
      + (A.state === '通' ? warn(`<b>token 以前记错了日子。</b>${pct(A.moved_share)} 的 token 被整块记在会话开始那天。
          最贵的一天从 ${esc(A.peak_before.d)}（${fmt(A.peak_before.tok)}）变成
          ${esc(A.peak_after.d)}（${fmt(A.peak_after.tok)}），差 ${(A.peak_delta * 100).toFixed(1)}%。
          ${esc(A.verdict || '')}`) : '')
      + warn(`<b>${esc(F.state || '说不准')}：扇出成本。</b>${esc(F.why || '')}<br>${esc(F.impact || '')}`)
      + `<p class="hint" style="margin-top:22px">按应用，长度是输入总量（含缓存）。</p>`
      + beams(llm.map(r => ({
          k: r.label, v: r.input_total, sub: `${r.vendor} · ${r.sessions} 场`,
          label: `${fmt(r.input_total)}　${rate(r.hit_rate)}`, c: 'var(--acc3)',
        })))
      + sheet('按模型', table(
          [{ t: '模型' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '命中率', r: true }],
          K.model.map(r => [esc(r.model), r.sessions.toFixed(1), fmt(r.input_total), rate(r.hit_rate)])))
      + sheet('按哪几家的价算的', table(
          [{ t: '厂商' }, { t: '可信度' }, { t: '抓取日期' }, { t: '缓存读倍数', r: true }],
          (C.prices || []).map(x => [esc(x.provider),
            `<span class="st" data-s="${x.confidence === 'verified' ? '通' : '不确定'}">${esc(x.confidence)}</span>`,
            esc(x.fetched), String(x.mult.cache_read)]))),
  });
  enter('.headline, .read, .beam, .warnbox', host);
}
