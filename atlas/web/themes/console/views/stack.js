import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, kv, table, meter, spark, warn, rate, state } from '../kit.js';

// Owner 的原话：dws 只是 cli 工具不是 LLM，openchatcut 也只是工具。
// 所以这一屏按 harness / provider / model 三层拆，工具单独列，不混进分母。
export async function render(host) {
  const K = D.A().stack, T = D.tokens(), t = T.total;
  const llm = K.harness.filter(r => r.kind === 'llm');
  const tools = K.harness.filter(r => r.kind === 'tool');
  let mode = 'slice';

  host.innerHTML = `
${sec('STACK', esc(K.note))}
${kv([
  ['输入（含缓存）', fmt(t.input_total), 'acc'],
  ['其中缓存命中', fmt(t.cached), ''],
  ['输入（不含缓存）', fmt(t.input_excl), ''],
  ['输出', fmt(t.output), ''],
  ['缓存命中率', rate(t.hit_rate), 'acc'],
  ['LLM harness', String(llm.length), ''],
  ['工具（不产生 token）', String(tools.length), 'warn'],
  ['无用量会话', String(T.no_usage), 'warn'],
])}

${sec('BY HARNESS', 'harness = 你操作的那个应用。')}
${table([{ t: '应用' }, { t: '厂商' }, { t: '会话', r: true }, { t: '有用量', r: true },
         { t: '输入(含缓存)', r: true }, { t: '输出', r: true }, { t: '命中率', r: true }, { t: '用到的模型' }],
  llm.map(r => [`<b>${esc(r.label)}</b>`, esc(r.vendor), String(r.sessions), String(r.measured),
    fmt(r.input_total), fmt(r.output), rate(r.hit_rate),
    r.models.map(m => `<span class="tag">${esc(m)}</span>`).join('')]))}
${tools.length ? warn(`<b>下面这两个不是 LLM，不产生 token</b> —— 单独列出来，不混进上面的分母：<br>
  ${tools.map(r => `<b>${esc(r.label)}</b>（${r.sessions} 场）—— ${esc(r.note)}`).join('<br>')}`) : ''}

${sec('BY PROVIDER', 'provider = 谁在服务这个模型。')}
${table([{ t: '厂商' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '缓存', r: true },
         { t: '输出', r: true }, { t: '命中率', r: true }, { t: '' }],
  K.provider.map(r => [`<b>${esc(r.provider)}</b>`, r.sessions.toFixed(0), fmt(r.input_total),
    fmt(r.cached), fmt(r.output), rate(r.hit_rate),
    meter(r.input_total, Math.max(1, ...K.provider.map(x => x.input_total)), 100)]))}

${sec('BY MODEL', '一场会话换过模型的，按模型数均分 —— 每个都记全量会把总量放大成模型个数倍。')}
${table([{ t: '模型' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '输出', r: true },
         { t: '命中率', r: true }, { t: '' }],
  K.model.map(r => [`<b>${esc(r.model)}</b>`, r.sessions.toFixed(1), fmt(r.input_total), fmt(r.output),
    rate(r.hit_rate), meter(r.input_total, Math.max(1, ...K.model.map(x => x.input_total)), 100)]))}

${sec('PROVIDER × MODEL')}
${table([{ t: '厂商' }, { t: '模型' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '命中率', r: true }],
  K.provider_model.map(r => [esc(r.provider), esc(r.model), r.sessions.toFixed(1),
    fmt(r.input_total), rate(r.hit_rate)]))}

${sec('SLICES')}
<div class="ctl">
  <button data-m="slice" aria-pressed="true">按时间切片</button>
  <button data-m="session" aria-pressed="false">按会话切片</button>
  <span class="tag" id="cnt"></span>
</div>
<div id="slot"></div>`;

  const slot = host.querySelector('#slot'), cnt = host.querySelector('#cnt');
  const bySlice = () => {
    cnt.textContent = `${T.by_slice.length} 时段 · ${T.by_week.length} 周 · ${T.by_day.length} 天`;
    return table([{ t: '悉尼时段' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true },
      { t: '缓存', r: true }, { t: '命中率', r: true }, { t: '' }],
      T.by_slice.map(r => [r.slice, String(r.sessions), fmt(r.input_total), fmt(r.cached),
        rate(r.hit_rate), r.hit_rate == null ? '' : meter(r.hit_rate, 1, 100)]))
      + '<div class="sec">BY WEEK</div>' + table(
        [{ t: '周' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '输出', r: true }, { t: '命中率', r: true }],
        T.by_week.slice().reverse().map(r => [r.w, String(r.sessions), fmt(r.input_total), fmt(r.output), rate(r.hit_rate)]))
      + '<div class="sec">BY DAY · 最近 45 天</div>'
      + `<p class="hint">输入 ${spark(T.by_day.slice(-45).map(r => r.input_total))}　命中率 ${spark(T.by_day.slice(-45).map(r => (r.hit_rate || 0) * 100))}</p>`
      + table([{ t: '日期' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '缓存', r: true }, { t: '命中率', r: true }],
        T.by_day.slice(-45).reverse().map(r => [`<span class="lnk" data-day="${r.d}">${r.d}</span>`,
          String(r.sessions), fmt(r.input_total), fmt(r.cached), rate(r.hit_rate)]));
  };
  const bySession = () => {
    cnt.textContent = `${T.sessions.length} 场有用量 / 共 ${T.sessions_total} 场`;
    return table([{ t: '时间' }, { t: '应用' }, { t: '模型' }, { t: '项目' }, { t: '标题' },
      { t: '你说', r: true }, { t: '输入(含缓存)', r: true }, { t: '缓存', r: true }, { t: '命中率', r: true }],
      T.sessions.slice(0, 400).map(r => [
        `<span class="lnk" data-day="${r.day}">${esc(r.at)}</span>`, esc(r.src),
        (r.models || []).map(m => `<span class="tag">${esc(m)}</span>`).join('') || '<span class="tag">未记录</span>',
        `<span class="tag">${esc(r.project || '—')}</span>`,
        `<span class="tag">${esc((r.title || '(无标题)').slice(0, 30))}</span>`,
        String(r.turns), fmt(r.input_total), fmt(r.cached), rate(r.hit)]));
  };
  const draw = () => { slot.innerHTML = mode === 'slice' ? bySlice() : bySession(); enter('tbody tr', slot); };
  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-m]'); if (!b) return;
    mode = b.dataset.m;
    host.querySelectorAll('[data-m]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.m === mode)));
    draw();
  });
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  draw(); enter('.sec, .kv > div', host);
}
