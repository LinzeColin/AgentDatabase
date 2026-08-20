import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, lede, p, n, big, aside, note, figure, rank, spark, table, rate, state } from '../kit.js';

export async function render(host) {
  const K = D.A().stack, T = D.tokens(), t = T.total;
  const llm = K.harness.filter(r => r.kind === 'llm');
  const tools = K.harness.filter(r => r.kind === 'tool');
  let mode = 'slice';

  host.innerHTML = `
${sec('技术栈与 Token')}
${lede(`你手上有 ${big(llm.length)} 个真正在调模型的应用，另外 ${n(tools.length)} 个只是工具 ——
  它们不产生 token，所以单独列出来，不混进任何分母。
  加起来一共读进 ${big(fmt(t.input_total))} 个 token（含缓存命中），
  其中 ${n(fmt(t.cached))} 个是缓存直接命中的，整体命中率 ${big(rate(t.hit_rate))}。`)}
${aside(esc(K.note))}
${tools.length ? note(`<b>不是 LLM 的：</b>${tools.map(r =>
  `${esc(r.label)}（${r.sessions} 场）—— ${esc(r.note)}`).join('；')}`) : ''}

${sec('按应用')}
${figure(table([{ t: '应用' }, { t: '厂商' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true },
  { t: '输出', r: true }, { t: '命中率', r: true }, { t: '模型' }],
  llm.map(r => [`<b>${esc(r.label)}</b>`, esc(r.vendor), String(r.sessions), fmt(r.input_total),
    fmt(r.output), rate(r.hit_rate), r.models.map(m => `<span class="kw">${esc(m)}</span>`).join('')])),
  'harness = 你操作的那个应用。命中率写「不确定」的，是那份记录里根本没有 token 字段。')}

${sec('按厂商')}
${figure(rank(K.provider.map(r => ({ k: r.provider, v: r.input_total,
  label: `${fmt(r.input_total)}　${rate(r.hit_rate)}` }))), 'provider = 谁在服务这个模型。')}

${sec('按模型')}
${figure(rank(K.model.map(r => ({ k: r.model, v: r.input_total,
  label: `${fmt(r.input_total)}　${r.sessions.toFixed(1)} 场` }))),
  '一场会话换过模型的按模型数均分 —— 每个都记全量会把总量放大成模型个数倍。')}
${figure(table([{ t: '厂商' }, { t: '模型' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '命中率', r: true }],
  K.provider_model.map(r => [esc(r.provider), esc(r.model), r.sessions.toFixed(1), fmt(r.input_total), rate(r.hit_rate)])),
  '厂商 × 模型。')}

${sec('切片')}
<div class="ctl">
  <button data-m="slice" aria-pressed="true">按时间切片</button>
  <button data-m="session" aria-pressed="false">按会话切片</button>
  <span id="cnt"></span>
</div>
<div id="slot"></div>`;

  const slot = host.querySelector('#slot'), cnt = host.querySelector('#cnt');
  const bySlice = () => {
    cnt.textContent = `${T.by_slice.length} 时段 · ${T.by_week.length} 周 · ${T.by_day.length} 天`;
    return figure(rank(T.by_slice.map(r => ({ k: r.slice, v: r.input_total,
      label: `${fmt(r.input_total)}　${rate(r.hit_rate)}` }))), '按悉尼时段。')
      + p(`逐周输入量 ${spark(T.by_week.map(r => r.input_total))}　命中率 ${spark(T.by_week.map(r => (r.hit_rate || 0) * 100))}`)
      + figure(table([{ t: '日期' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '缓存', r: true }, { t: '命中率', r: true }],
        T.by_day.slice(-40).reverse().map(r => [`<span class="lnk" data-day="${r.d}">${r.d}</span>`,
          String(r.sessions), fmt(r.input_total), fmt(r.cached), rate(r.hit_rate)])), '最近四十天逐日。');
  };
  const bySession = () => {
    cnt.textContent = `${T.sessions.length} 场有用量 / 共 ${T.sessions_total} 场`;
    return figure(table([{ t: '时间' }, { t: '应用' }, { t: '模型' }, { t: '标题' },
      { t: '输入(含缓存)', r: true }, { t: '命中率', r: true }],
      T.sessions.slice(0, 200).map(r => [`<span class="lnk" data-day="${r.day}">${esc(r.at)}</span>`,
        esc(r.src), (r.models || []).map(m => `<span class="kw">${esc(m)}</span>`).join('') || '<span class="kw">未记录</span>',
        esc((r.title || '(无标题)').slice(0, 32)), fmt(r.input_total), rate(r.hit)])),
      '按输入量降序，前 200 场。');
  };
  const draw = () => { slot.innerHTML = mode === 'slice' ? bySlice() : bySession(); enter('figure', slot); };
  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-m]'); if (!b) return;
    mode = b.dataset.m;
    host.querySelectorAll('[data-m]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.m === mode)));
    draw();
  });
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  draw(); enter('.sec, p.body, figure, .aside', host);
}
