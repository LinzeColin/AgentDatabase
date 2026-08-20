import { esc, fmt, pct, go, enter, S } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas } from '../../../core/g3d.js';
import { sec, bento, orbit, drawer, table, warn, pill, rate, state } from '../kit.js';

export async function render(host) {
  const T = D.tokens(), t = T.total;
  let mode = 'slice';

  host.innerHTML = `
${sec('Token 与缓存', `口径：${esc(T.metric)}　时区 ${esc(T.timezone)}`)}
${bento([
  { k: '输入（含缓存）', v: fmt(t.input_total), n: `其中缓存命中 ${fmt(t.cached)}`, w: 3, tone: 'acc' },
  { k: '缓存命中率', v: rate(t.hit_rate), n: `有用量 ${t.measured} 场 / 无用量 ${t.unmeasured} 场`, w: 3, alt: true },
  { k: '输入（不含缓存）', v: fmt(t.input_excl), n: '真正重新读进去的' },
  { k: '缓存写入', v: fmt(t.cache_write), n: '建缓存的成本' },
  { k: '输出', v: fmt(t.output), n: '模型写出来的' },
])}
${warn(`<b>三家的命中率差别很大，不能只看总数。</b>总数被 claude-code 的体量压住了 ——
  它几乎全部走缓存，codex 在 96% 上下。下面按来源的环形图才是可比的。<br>
  另有 <b>${T.no_usage}</b> 场会话根本没有用量记录，它们的命中率写<b>不确定</b>，不是 0。`)}

${sec('按来源', '每个环 = 一个来源的缓存命中率。空心的表示没有用量数据。')}
<canvas class="viz" id="rings" height="230"></canvas>
${drawer('展开来源明细表', table(
  [{ t: '来源' }, { t: '会话', r: true }, { t: '有用量', r: true }, { t: '输入(含缓存)', r: true },
   { t: '缓存', r: true }, { t: '输出', r: true }, { t: '命中率', r: true }],
  T.by_source.map(r => [esc(r.s), String(r.sessions), String(r.measured), fmt(r.input_total),
    fmt(r.cached), fmt(r.output), rate(r.hit_rate)])))}

${sec('按类型', '你开口的 vs 机器跑的，谁更烧 token。')}
${orbit(T.by_kind.map(r => ({
  k: ({ human: '你开口的', auto: '批处理/单轮', fanout: 'agent 扇出' })[r.k] || r.k,
  v: r.input_total, label: `${fmt(r.input_total)} · ${rate(r.hit_rate)}`,
  c: r.k === 'human' ? 'var(--acc)' : 'var(--dim2)',
})))}

${sec('切片', 'Owner 要的两种切法：按时间，或按会话。')}
<div class="ctl">
  <button data-m="slice" aria-pressed="true">按时间切片</button>
  <button data-m="session" aria-pressed="false">按会话切片</button>
  <span class="pill" id="cnt"></span>
</div>
<div id="slot"></div>`;

  const slot = host.querySelector('#slot'), cnt = host.querySelector('#cnt');

  const bySlice = () => {
    cnt.textContent = `${T.by_slice.length} 个时段 · ${T.by_week.length} 周 · ${T.by_day.length} 天`;
    return `
<p class="hint">悉尼时段</p>
${orbit(T.by_slice.map(r => ({ k: r.slice, v: r.input_total,
  label: `${fmt(r.input_total)} · ${rate(r.hit_rate)}`, c: 'var(--acc)' })))}
<p class="hint" style="margin-top:26px">按周（输入量，含缓存）</p>
${orbit(T.by_week.slice(-14).reverse().map(r => ({ k: r.w, v: r.input_total,
  label: `${fmt(r.input_total)} · ${rate(r.hit_rate)}`, c: 'var(--acc2)' })))}
${drawer('展开逐日明细（最近 45 天）', table(
  [{ t: '日期' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '缓存', r: true },
   { t: '输出', r: true }, { t: '命中率', r: true }],
  T.by_day.slice(-45).reverse().map(r => [
    `<span class="lnk" data-day="${r.d}">${r.d}</span>`, String(r.sessions),
    fmt(r.input_total), fmt(r.cached), fmt(r.output), rate(r.hit_rate)])))}`;
  };

  const bySession = () => {
    cnt.textContent = `${T.sessions.length} 场有用量（共 ${T.sessions_total} 场）`;
    return `
<p class="hint">最烧的 30 场</p>
${orbit(T.sessions.slice(0, 30).map(r => ({
  k: r.day, v: r.input_total, label: `${fmt(r.input_total)} · ${rate(r.hit)}`,
  c: r.kind === 'human' ? 'var(--acc)' : 'var(--dim2)', attr: `data-day="${r.day}"`,
})))}
${drawer('展开全部会话明细', table(
  [{ t: '时间' }, { t: '来源' }, { t: '项目' }, { t: '标题' }, { t: '你说', r: true },
   { t: '输入(含缓存)', r: true }, { t: '缓存', r: true }, { t: '输出', r: true }, { t: '命中率', r: true }],
  T.sessions.slice(0, 300).map(r => [
    `<span class="lnk" data-day="${r.day}">${esc(r.at)}</span>`, esc(r.src),
    esc(r.project || '—'), esc(r.title || '(无标题)'), String(r.turns),
    fmt(r.input_total), fmt(r.cached), fmt(r.output), rate(r.hit)])))}`;
  };

  const drawSlot = () => { slot.innerHTML = mode === 'slice' ? bySlice() : bySession(); enter('.orow', slot); };
  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-m]');
    if (!b) return;
    mode = b.dataset.m;
    host.querySelectorAll('[data-m]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.m === mode)));
    drawSlot();
  });
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]');
    if (d) go('day', d.dataset.day);
  });

  const cv = host.querySelector('#rings');
  const drawRings = () => {
    const { ctx, w } = fitCanvas(cv, 230);
    const h = 230;
    ctx.clearRect(0, 0, w, h);
    const rows = T.by_source;
    const n = rows.length;
    const cellW = w / Math.max(1, n), R = Math.max(14, Math.min(cellW / 2 - 14, 52));
    const css = k => getComputedStyle(document.body).getPropertyValue(k).trim();
    rows.forEach((r, i) => {
      const cx = cellW * (i + 0.5), cy = 96;
      ctx.lineWidth = 12; ctx.lineCap = 'round';
      ctx.strokeStyle = css('--track');
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.2832); ctx.stroke();
      if (r.hit_rate != null) {
        ctx.strokeStyle = css('--acc');
        ctx.beginPath();
        ctx.arc(cx, cy, R, -Math.PI / 2, -Math.PI / 2 + r.hit_rate * 6.2832);
        ctx.stroke();
      }
      ctx.textAlign = 'center';
      ctx.fillStyle = r.hit_rate == null ? css('--warn') : css('--fg');
      ctx.font = '700 15px -apple-system, system-ui, sans-serif';
      ctx.fillText(r.hit_rate == null ? '不确定' : (r.hit_rate * 100).toFixed(1) + '%', cx, cy + 5);
      ctx.fillStyle = css('--dim'); ctx.font = '12px -apple-system, system-ui, sans-serif';
      ctx.fillText(r.s.slice(0, 14), cx, cy + R + 26);
      ctx.fillStyle = css('--dim2'); ctx.font = '11px -apple-system, system-ui, sans-serif';
      ctx.fillText(fmt(r.input_total), cx, cy + R + 42);
      ctx.textAlign = 'left';
    });
  };
  drawRings();
  const onR = () => drawRings();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  drawSlot();
  enter('.sec, .card, .orow', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
