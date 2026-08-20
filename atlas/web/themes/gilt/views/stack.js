import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

// Token 与栈。三页：成本口径 / 归日 / 按应用与模型。
export async function render(host) {
  const K = D.A().stack, T = D.tokens(), t = T.total;
  const C = T.cost || {}, A = T.attribution || {}, Fo = T.fanout || {};
  const llm = K.harness.filter(r => r.kind === 'llm');

  host.innerHTML =
    leaf({
      title: '钱花在看不见的那一栏',
      lead: `旧口径「成本 = 输入 + 输出」只看得到十分之一的账单 —— 而缓存读取才是大头。`,
      body: plate({ k: '旧口径能看到的成本', big: true,
        v: C.coverage_by_cost != null ? pct(C.coverage_by_cost) : '说不准',
        n: C.coverage_by_volume != null ? `按 token 条数算只有 ${pct(C.coverage_by_volume)} —— 只看条数会以为没漏` : '' })
        + plates([
          { k: '价格加权 token', v: fmt(C.bie_total || 0), n: 'BIE，无量纲、跨时间可比' },
          { k: '缓存读取占成本', v: C.bie_total ? pct(C.by_field.cache_read / C.bie_total) : '—',
            n: fmt((C.by_field || {}).cache_read || 0) },
          { k: '缓存写入', v: fmt((C.by_field || {}).cache_write || 0), n: '单价最高的那类输入' },
          { k: '没有价目表', v: `${(C.no_price || {}).sessions ?? '—'} 场`, size: 'sm',
            n: Object.keys((C.no_price || {}).sources || {}).join('、') || '—' },
          { k: '没量到 token', v: `${(C.no_usage || {}).sessions ?? '—'} 场`, size: 'sm',
            n: '有价目表，但日志里一个都没记' },
        ])
        + warn(`<b>${esc(Fo.state || '说不准')}：扇出成本。</b>${esc(Fo.why || '')}<br>${esc(Fo.impact || '')}`)
        + marginal(`<b>这些数不能跨家相加。</b>${(C.caveats || []).map(esc).join('<br>')}`),
    })
    + (A.state === '通' ? leaf({
      title: 'token 记在哪一天',
      lead: esc(A.note || ''),
      body: plate({ k: '记错日子的 token', v: pct(A.moved_share), big: true,
        n: `只能靠猜的：${pct(A.guessed_share)}` })
        + plates([
          { k: '最贵的一天 · 修前', v: esc(A.peak_before.d), size: 'sm', n: fmt(A.peak_before.tok) },
          { k: '最贵的一天 · 修后', v: esc(A.peak_after.d), size: 'sm', n: fmt(A.peak_after.tok) },
          { k: '变了多少', v: (A.peak_delta * 100).toFixed(1) + '%', n: esc(A.verdict) },
        ]),
    }) : '')
    + leaf({
      title: '按应用与模型', lead: '标 tool 的不是 LLM，不产生 token，单独列不混进分母。',
      cols: false,
      body: carve(llm.map(r => ({
          k: `${r.label}（${r.vendor}）`, v: r.input_total,
          label: `${fmt(r.input_total)}　命中 ${rate(r.hit_rate)}　${r.sessions} 场`,
        })))
        + h2('按模型')
        + rub([{ t: '模型' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '命中率', r: true }],
            K.model.map(r => [esc(r.model), r.sessions.toFixed(1), fmt(r.input_total), rate(r.hit_rate)]))
        + h2('按哪几家的价算的')
        + rub([{ t: '厂商' }, { t: '可信度' }, { t: '抓取日期' }, { t: '缓存读倍数', r: true }],
            (C.prices || []).map(x => [esc(x.provider),
              `${esc(x.confidence)}${seal(x.confidence === 'verified' ? '通' : '说不准')}`,
              esc(x.fetched), String(x.mult.cache_read)])),
    });
}
