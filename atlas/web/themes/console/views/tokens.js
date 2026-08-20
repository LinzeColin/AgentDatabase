import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, kv, table, meter, spark, warn, rate } from '../kit.js';

export async function render(host) {
  const T = D.tokens(), t = T.total;
  let mode = 'slice';   // slice = 时间切片 / session = 会话切片

  const head = `
${sec('TOKEN & CACHE')}
<p class="hint">口径：${esc(T.metric)}　时区 ${esc(T.timezone)}</p>
${kv([
  ['输入（含缓存）', fmt(t.input_total), 'acc'],
  ['其中缓存命中', fmt(t.cached), ''],
  ['输入（不含缓存）', fmt(t.input_excl), ''],
  ['缓存写入', fmt(t.cache_write), ''],
  ['输出', fmt(t.output), ''],
  ['缓存命中率', rate(t.hit_rate), 'acc'],
  ['有用量会话', String(t.measured), ''],
  ['无用量会话', String(t.unmeasured), 'warn'],
])}
${warn(`<b>三家的命中率差别很大，不能只看总数。</b>
  总命中率被 claude-code 的体量压住了 —— 它几乎全部走缓存；codex 是 96% 上下。
  下面「按来源」那张表才是可比的。<br>
  另有 <b>${T.no_usage}</b> 场会话根本没有用量记录（chatgpt 导出与 claude-desktop 元数据不含 token），
  它们的命中率写<b>不确定</b>，不是 0 —— 这两件事在看板上长得一样，意思完全相反。`)}

${sec('BY SOURCE', '来源之间才可比。')}
${table([{ t: '来源' }, { t: '会话', r: true }, { t: '有用量', r: true }, { t: '输入(含缓存)', r: true },
         { t: '缓存', r: true }, { t: '输出', r: true }, { t: '命中率', r: true }, { t: '' }],
  T.by_source.map(r => [esc(r.s), String(r.sessions), String(r.measured), fmt(r.input_total),
    fmt(r.cached), fmt(r.output), rate(r.hit_rate),
    r.hit_rate == null ? '' : meter(r.hit_rate, 1, 90)]))}

${sec('BY MODE', '你开口的 vs 机器跑的，谁更烧 token。')}
${table([{ t: '类型' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '输出', r: true }, { t: '命中率', r: true }],
  T.by_kind.map(r => [
    ({ human: '你开口的', auto: '批处理/单轮', fanout: 'agent 扇出' })[r.k] || r.k,
    String(r.sessions), fmt(r.input_total), fmt(r.output), rate(r.hit_rate)]))}
`;

  host.innerHTML = head + `
${sec('SLICES')}
<div class="ctl">
  <button data-m="slice" aria-pressed="true">按时间切片</button>
  <button data-m="session" aria-pressed="false">按会话切片</button>
  <span class="tag" id="cnt"></span>
</div>
<div id="slot"></div>`;

  const slot = host.querySelector('#slot'), cnt = host.querySelector('#cnt');

  const bySlice = () => {
    cnt.textContent = `${T.by_slice.length} 个时段 · ${T.by_day.length} 天 · ${T.by_week.length} 周`;
    return `
${table([{ t: '悉尼时段' }, { t: '会话', r: true }, { t: '有用量', r: true }, { t: '输入(含缓存)', r: true },
         { t: '缓存', r: true }, { t: '命中率', r: true }, { t: '' }],
  T.by_slice.map(r => [r.slice, String(r.sessions), String(r.measured), fmt(r.input_total),
    fmt(r.cached), rate(r.hit_rate), r.hit_rate == null ? '' : meter(r.hit_rate, 1, 100)]))}
<div class="sec">BY WEEK</div>
${table([{ t: '周' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '输出', r: true },
         { t: '命中率', r: true }, { t: '' }],
  T.by_week.slice().reverse().map(r => [r.w, String(r.sessions), fmt(r.input_total), fmt(r.output),
    rate(r.hit_rate), r.hit_rate == null ? '' : meter(r.hit_rate, 1, 90)]))}
<div class="sec">BY DAY · 最近 45 天</div>
<p class="hint">输入量 ${spark(T.by_day.slice(-45).map(r => r.input_total))}　命中率 ${spark(T.by_day.slice(-45).map(r => (r.hit_rate || 0) * 100))}</p>
${table([{ t: '日期' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '缓存', r: true },
         { t: '输出', r: true }, { t: '命中率', r: true }],
  T.by_day.slice(-45).reverse().map(r => [
    `<span class="lnk" data-day="${r.d}">${r.d}</span>`, String(r.sessions),
    fmt(r.input_total), fmt(r.cached), fmt(r.output), rate(r.hit_rate)]))}`;
  };

  const bySession = () => {
    cnt.textContent = `${T.sessions.length} 场有用量（共 ${T.sessions_total} 场），按输入量降序`;
    return table(
      [{ t: '时间' }, { t: '来源' }, { t: '项目' }, { t: '标题' }, { t: '你说', r: true }, { t: '工具', r: true },
       { t: '输入(含缓存)', r: true }, { t: '缓存', r: true }, { t: '输出', r: true }, { t: '命中率', r: true }],
      T.sessions.slice(0, 400).map(r => [
        `<span class="lnk" data-day="${r.day}">${esc(r.at)}</span>`,
        esc(r.src), `<span class="tag">${esc(r.project || '—')}</span>`,
        `<span class="tag">${esc(r.title || '(无标题)')}</span>`,
        String(r.turns), String(r.tools),
        fmt(r.input_total), fmt(r.cached), fmt(r.output), rate(r.hit)]));
  };

  const draw = () => {
    slot.innerHTML = mode === 'slice' ? bySlice() : bySession();
    enter('tbody tr', slot);
  };
  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-m]');
    if (!b) return;
    mode = b.dataset.m;
    host.querySelectorAll('[data-m]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.m === mode)));
    draw();
  });
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]');
    if (d) go('day', d.dataset.day);
  });
  draw();
  enter('.sec, .kv > div', host);
}
