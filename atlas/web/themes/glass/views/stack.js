import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas , cssVar } from '../../../core/g3d.js';
import { sec, bento, orbit, drawer, table, warn, pill, rate, state } from '../kit.js';

export async function render(host) {
  const K = D.A().stack, T = D.tokens(), t = T.total;
  const llm = K.harness.filter(r => r.kind === 'llm');
  const tools = K.harness.filter(r => r.kind === 'tool');
  let mode = 'slice';

  host.innerHTML = `
${sec('技术栈与 Token', esc(K.note))}
${bento([
  { k: '输入（含缓存）', v: fmt(t.input_total), n: `其中缓存 ${fmt(t.cached)}`, w: 3, tone: 'acc' },
  { k: '缓存命中率', v: rate(t.hit_rate), n: `有用量数据 ${t.measured} / 无用量 ${t.unmeasured}`, w: 3, alt: true },
  { k: '输入（不含缓存）', v: fmt(t.input_excl), n: '真正重新读进去的' },
  { k: '输出', v: fmt(t.output), n: '模型写出来的' },
  { k: 'LLM 应用', v: String(llm.length), n: `另有 ${tools.length} 个只是工具` },
])}
${tools.length ? warn(`<b>这些不是 LLM，不产生 token</b> —— 单独列出，不混进上面的分母：<br>
  ${tools.map(r => `<b>${esc(r.label)}</b>（${r.sessions} 场）—— ${esc(r.note)}`).join('<br>')}`) : ''}

${sec('按应用', 'harness = 你操作的那个应用。')}
<canvas class="viz" id="rings" height="240" role="img" aria-label="各应用的缓存命中率对照图。逐项明细见下方表格。"></canvas>
${drawer('展开应用明细', table(
  [{ t: '应用' }, { t: '厂商' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true },
   { t: '输出', r: true }, { t: '命中率', r: true }, { t: '模型' }],
  llm.map(r => [`<b>${esc(r.label)}</b>`, esc(r.vendor), String(r.sessions), fmt(r.input_total),
    fmt(r.output), rate(r.hit_rate), r.models.map(m => pill(m)).join('')])))}

${sec('按厂商', 'provider = 谁在服务这个模型。')}
${orbit(K.provider.map(r => ({ k: r.provider, v: r.input_total,
  label: `${fmt(r.input_total)}　${rate(r.hit_rate)}`, c: 'var(--acc)' })))}

${sec('按模型', '一场会话换过模型的按模型数均分 —— 每个都记全量会把总量放大成模型个数倍。')}
${orbit(K.model.map(r => ({ k: r.model, v: r.input_total,
  label: `${fmt(r.input_total)}　${r.sessions.toFixed(1)} 场`, c: 'var(--acc2)' })))}
${drawer('厂商 × 模型', table([{ t: '厂商' }, { t: '模型' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '命中率', r: true }],
  K.provider_model.map(r => [esc(r.provider), esc(r.model), r.sessions.toFixed(1), fmt(r.input_total), rate(r.hit_rate)])))}

${sec('切片')}
<div class="ctl">
  <button data-m="slice" aria-pressed="true">按时间切片</button>
  <button data-m="session" aria-pressed="false">按会话切片</button>
  <span class="pill" id="cnt"></span>
</div>
<div id="slot"></div>`;

  const slot = host.querySelector('#slot'), cnt = host.querySelector('#cnt');
  const bySlice = () => {
    cnt.textContent = `${T.by_slice.length} 时段 · ${T.by_week.length} 周 · ${T.by_day.length} 天`;
    return `<p class="hint">悉尼时段</p>${orbit(T.by_slice.map(r => ({ k: r.slice, v: r.input_total,
      label: `${fmt(r.input_total)}　${rate(r.hit_rate)}`, c: 'var(--acc)' })))}
      <p class="hint" style="margin-top:26px">最近 14 周</p>
      ${orbit(T.by_week.slice(-14).reverse().map(r => ({ k: r.w, v: r.input_total,
        label: `${fmt(r.input_total)}　${rate(r.hit_rate)}`, c: 'var(--acc2)' })))}
      ${drawer('展开逐日（最近 45 天）', table(
        [{ t: '日期' }, { t: '会话', r: true }, { t: '输入(含缓存)', r: true }, { t: '缓存', r: true }, { t: '命中率', r: true }],
        T.by_day.slice(-45).reverse().map(r => [`<span class="lnk" data-day="${r.d}">${r.d}</span>`,
          String(r.sessions), fmt(r.input_total), fmt(r.cached), rate(r.hit_rate)])))}`;
  };
  const bySession = () => {
    cnt.textContent = `${T.sessions.length} 场有用量数据 / 共 ${T.sessions_total} 场`;
    return `<p class="hint">最烧的 30 场</p>${orbit(T.sessions.slice(0, 30).map(r => ({
      k: r.day, v: r.input_total, label: `${fmt(r.input_total)}　${rate(r.hit)}`,
      c: 'var(--acc)', attr: `data-day="${r.day}"` })))}
      ${drawer('展开全部会话', table([{ t: '时间' }, { t: '应用' }, { t: '模型' }, { t: '标题' },
        { t: '输入(含缓存)', r: true }, { t: '命中率', r: true }],
        T.sessions.slice(0, 300).map(r => [`<span class="lnk" data-day="${r.day}">${esc(r.at)}</span>`,
          esc(r.src), (r.models || []).map(m => pill(m)).join('') || pill('未记录'),
          esc((r.title || '(无标题)').slice(0, 34)), fmt(r.input_total), rate(r.hit)])))}`;
  };
  const draw = () => { slot.innerHTML = mode === 'slice' ? bySlice() : bySession(); enter('.orow', slot); };
  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-m]'); if (!b) return;
    mode = b.dataset.m;
    host.querySelectorAll('[data-m]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.m === mode)));
    draw();
  });
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });

  const css = k => cssVar(k);
  const drawRings = () => {
    const { ctx, w } = fitCanvas(host.querySelector('#rings'), 240);
    const h = 240, n = Math.max(1, llm.length), cellW = w / n, R = Math.max(14, Math.min(cellW / 2 - 16, 54));
    ctx.clearRect(0, 0, w, h);
    llm.forEach((r, i) => {
      const cx = cellW * (i + .5), cy = 98;
      ctx.lineWidth = 13; ctx.lineCap = 'round';
      ctx.strokeStyle = css('--track');
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.2832); ctx.stroke();
      if (r.hit_rate != null) {
        const g = ctx.createLinearGradient(cx - R, cy - R, cx + R, cy + R);
        g.addColorStop(0, css('--acc')); g.addColorStop(1, css('--acc2'));
        ctx.strokeStyle = g;
        ctx.beginPath(); ctx.arc(cx, cy, R, -Math.PI / 2, -Math.PI / 2 + r.hit_rate * 6.2832); ctx.stroke();
      }
      ctx.textAlign = 'center';
      ctx.fillStyle = r.hit_rate == null ? css('--warn') : css('--fg');
      ctx.font = '700 15px -apple-system, system-ui, sans-serif';
      ctx.fillText(r.hit_rate == null ? '说不准' : (r.hit_rate * 100).toFixed(1) + '%', cx, cy + 5);
      ctx.fillStyle = css('--dim'); ctx.font = '12px -apple-system, system-ui, sans-serif';
      ctx.fillText(r.label.slice(0, 13), cx, cy + R + 26);
      ctx.fillStyle = css('--dim2'); ctx.font = '11px -apple-system, system-ui, sans-serif';
      ctx.fillText(`${r.vendor} · ${fmt(r.input_total)}`, cx, cy + R + 42);
      ctx.textAlign = 'left';
    });
  };
  drawRings();
  const onR = () => drawRings();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.sec, .card, .orow', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
