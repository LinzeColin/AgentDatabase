import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, lede, p, n, big, aside, note, figure, rank, spark, table, rate, state } from '../kit.js';

export async function render(host) {
  const T = D.tokens(), t = T.total;
  let mode = 'slice';

  host.innerHTML = `
${sec('Token 与缓存')}
${lede(`一共读进 ${big(fmt(t.input_total))} 个 token（这个口径<b>含</b>缓存命中），
  其中 ${n(t.cached)} 个是缓存直接命中的，真正重新读进去的只有 ${n(t.input_excl)} 个。
  模型写出来 ${n(t.output)} 个。整体缓存命中率 ${big(rate(t.hit_rate))}。`)}
${aside(`口径：${esc(T.metric)}<br>时区：${esc(T.timezone)}`)}
${note(`<b>但这个总数不能拿来比较。</b>它被 claude-code 的体量压住了 —— 那边几乎全部走缓存；
  codex 在 96% 上下。要比就比下面按来源那张表。<br>
  另有 <b>${T.no_usage}</b> 场会话根本没有用量记录（ChatGPT 导出与 claude-desktop 元数据不含 token），
  它们的命中率写<b>不确定</b>，不是 0 —— 这两件事在表里长得一样，意思完全相反。`)}

${sec('按来源')}
${figure(table([{ t: '来源' }, { t: '会话', r: true }, { t: '有用量', r: true }, { t: '输入(含缓存)', r: true },
  { t: '缓存', r: true }, { t: '输出', r: true }, { t: '命中率', r: true }],
  T.by_source.map(r => [esc(r.s), String(r.sessions), String(r.measured), fmt(r.input_total),
    fmt(r.cached), fmt(r.output), rate(r.hit_rate)])),
  '来源之间才可比。「不确定」＝这个来源的记录里没有 token 字段。')}

${sec('按类型')}
${figure(rank(T.by_kind.map(r => ({
  k: ({ human: '你开口的', auto: '批处理／单轮', fanout: 'agent 扇出' })[r.k] || r.k,
  v: r.input_total, label: `${fmt(r.input_total)}　${rate(r.hit_rate)}` }))),
  '你开口的 vs 机器跑的，谁更烧 token。')}

${sec('切片', '两种切法：按时间，或按会话。')}
<div class="ctl">
  <button data-m="slice" aria-pressed="true">按时间切片</button>
  <button data-m="session" aria-pressed="false">按会话切片</button>
  <span id="cnt"></span>
</div>
<div id="slot"></div>`;

  const slot = host.querySelector('#slot'), cnt = host.querySelector('#cnt');
  const bySlice = () => {
    cnt.textContent = `${T.by_slice.length} 个时段 · ${T.by_week.length} 周 · ${T.by_day.length} 天`;
    return `
${figure(rank(T.by_slice.map(r => ({ k: r.slice, v: r.input_total,
  label: `${fmt(r.input_total)}　${rate(r.hit_rate)}` }))), '按悉尼时段。')}
${p(`逐周输入量的起伏：${spark(T.by_week.map(r => r.input_total))}　
  命中率的起伏：${spark(T.by_week.map(r => (r.hit_rate || 0) * 100))}`)}
${figure(table([{ t: '周' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '输出', r: true }, { t: '命中率', r: true }],
  T.by_week.slice().reverse().map(r => [r.w, String(r.sessions), fmt(r.input_total), fmt(r.output), rate(r.hit_rate)])), '逐周。')}
${figure(table([{ t: '日期' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '缓存', r: true }, { t: '命中率', r: true }],
  T.by_day.slice(-40).reverse().map(r => [`<span class="lnk" data-day="${r.d}">${r.d}</span>`,
    String(r.sessions), fmt(r.input_total), fmt(r.cached), rate(r.hit_rate)])), '最近四十天逐日。')}`;
  };
  const bySession = () => {
    cnt.textContent = `${T.sessions.length} 场有用量（共 ${T.sessions_total} 场）`;
    return figure(table([{ t: '时间' }, { t: '来源' }, { t: '项目' }, { t: '标题' }, { t: '你说', r: true },
      { t: '输入(含缓存)', r: true }, { t: '缓存', r: true }, { t: '命中率', r: true }],
      T.sessions.slice(0, 200).map(r => [`<span class="lnk" data-day="${r.day}">${esc(r.at)}</span>`,
        esc(r.src), esc(r.project || '—'), esc((r.title || '(无标题)').slice(0, 34)),
        String(r.turns), fmt(r.input_total), fmt(r.cached), rate(r.hit)])),
      '按输入量降序，前 200 场。');
  };
  const drawSlot = () => { slot.innerHTML = mode === 'slice' ? bySlice() : bySession(); enter('figure', slot); };
  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-m]'); if (!b) return;
    mode = b.dataset.m;
    host.querySelectorAll('[data-m]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.m === mode)));
    drawSlot();
  });
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  drawSlot();
  enter('.sec, p.body, figure, .aside', host);
}
