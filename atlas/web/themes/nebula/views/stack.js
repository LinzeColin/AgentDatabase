import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { fitCanvas, cssVar } from '../../../core/g3d.js';
import { hero, sec, grid, orbit, drawer, table, warn, pill, rate, state } from '../kit.js';

// 三个维度分开算：供应商（谁在服务）、模型（哪个脑子）、应用（你手里那个壳）。
// 不是 LLM 的工具单独列，绝不混进 token 的分母。
export async function render(host) {
  const K = D.A().stack, T = D.tokens(), t = T.total;
  const llm = K.harness.filter(r => r.kind === 'llm');
  const tools = K.harness.filter(r => r.kind === 'tool');
  let mode = 'slice';

  host.innerHTML = `
${hero('家当', '你手上到底有几套东西', esc(K.note))}
${grid([
  { k: '读进去的（含缓存）', v: fmt(t.input_total), n: `其中重复读的缓存 ${fmt(t.cached)}`, w: 3, tone: 'acc' },
  { k: '缓存命中率', v: rate(t.hit_rate), n: `有用量记录 ${t.measured} 场 / 没记录 ${t.unmeasured} 场`, w: 3, alt: true },
  { k: '真正新读的', v: fmt(t.input_excl), n: '把缓存刨掉之后' },
  { k: '它写出来的', v: fmt(t.output), n: '输出 token' },
  { k: '真的是 LLM 的', v: String(llm.length), n: `另外 ${tools.length} 个只是工具` },
])}
${tools.length ? warn(`<b>下面这些不是 LLM，本身不产生 token</b> —— 单独列，绝不混进上面的分母：<br>
  ${tools.map(r => `<b>${esc(r.label)}</b>（${r.sessions} 场）—— ${esc(r.note)}`).join('<br>')}`) : ''}

${sec('按应用分', '应用＝你手里操作的那个壳。环上填的是缓存命中率。')}
<div class="slab" style="padding:12px 12px 8px"><canvas class="viz" id="rings" style="border:0;background:none"></canvas></div>
${drawer('摊开应用明细', table(
  [{ t: '应用' }, { t: '厂商' }, { t: '会话', r: true }, { t: '读进(含缓存)', r: true },
   { t: '写出', r: true }, { t: '命中率', r: true }, { t: '用了哪些模型' }],
  llm.map(r => [`<b>${esc(r.label)}</b>`, esc(r.vendor), String(r.sessions), fmt(r.input_total),
    fmt(r.output), rate(r.hit_rate), r.models.map(m => pill(m)).join('')])))}

${sec('按供应商分', '供应商＝谁在服务这个模型。同一个模型在不同家跑，算不同供应商。')}
${orbit(K.provider.map(r => ({ k: r.provider, v: r.input_total,
  label: `${fmt(r.input_total)}　命中 ${rate(r.hit_rate)}` })))}

${sec('按模型分', '一场会话中途换过模型的，按模型个数均分 —— 每个都记全量会把总数放大成模型个数倍。')}
${orbit(K.model.map(r => ({ k: r.model, v: r.input_total,
  label: `${fmt(r.input_total)}　${r.sessions.toFixed(1)} 场`, c: 'var(--acc2)' })))}
${drawer('供应商 × 模型 对照', table(
  [{ t: '供应商' }, { t: '模型' }, { t: '会话', r: true }, { t: '读进(含缓存)', r: true }, { t: '命中率', r: true }],
  K.provider_model.map(r => [esc(r.provider), esc(r.model), r.sessions.toFixed(1),
    fmt(r.input_total), rate(r.hit_rate)])))}

${sec('换个切法看')}
<div class="ctl">
  <button data-m="slice" aria-pressed="true">按时间切</button>
  <button data-m="session" aria-pressed="false">按单场切</button>
  <span class="pill" id="cnt"></span>
</div>
<div id="slot"></div>`;

  const slot = host.querySelector('#slot'), cnt = host.querySelector('#cnt');
  const bySlice = () => {
    cnt.textContent = `${T.by_slice.length} 个时段 · ${T.by_week.length} 周 · ${T.by_day.length} 天`;
    return `<p class="hint">按悉尼时间的时段</p>
      ${orbit(T.by_slice.map(r => ({ k: r.slice, v: r.input_total,
        label: `${fmt(r.input_total)}　命中 ${rate(r.hit_rate)}` })))}
      <p class="hint" style="margin-top:26px">最近 14 周</p>
      ${orbit(T.by_week.slice(-14).reverse().map(r => ({ k: r.w, v: r.input_total,
        label: `${fmt(r.input_total)}　命中 ${rate(r.hit_rate)}`, c: 'var(--acc2)' })))}
      ${drawer('摊开逐日（最近 45 天）', table(
        [{ t: '日期' }, { t: '会话', r: true }, { t: '读进(含缓存)', r: true },
         { t: '其中缓存', r: true }, { t: '命中率', r: true }],
        T.by_day.slice(-45).reverse().map(r => [`<span class="lnk" data-day="${r.d}">${r.d}</span>`,
          String(r.sessions), fmt(r.input_total), fmt(r.cached), rate(r.hit_rate)])))}`;
  };
  const bySession = () => {
    cnt.textContent = `${T.sessions.length} 场有用量记录 / 一共 ${T.sessions_total} 场`;
    return `<p class="hint">最烧的 30 场</p>
      ${orbit(T.sessions.slice(0, 30).map(r => ({ k: r.day, v: r.input_total,
        label: `${fmt(r.input_total)}　命中 ${rate(r.hit)}`, attr: `data-day="${r.day}"` })))}
      ${drawer('摊开全部会话', table(
        [{ t: '时间' }, { t: '应用' }, { t: '模型' }, { t: '标题' },
         { t: '读进(含缓存)', r: true }, { t: '命中率', r: true }],
        T.sessions.slice(0, 300).map(r => [`<span class="lnk" data-day="${r.day}">${esc(r.at)}</span>`,
          esc(r.src), (r.models || []).map(m => pill(m)).join('') || pill('没记下来'),
          esc((r.title || '(没有标题)').slice(0, 34)), fmt(r.input_total), rate(r.hit)])))}`;
  };
  const draw = () => { slot.innerHTML = mode === 'slice' ? bySlice() : bySession(); enter('.orow', slot); };

  host.querySelector('.ctl').addEventListener('click', e => {
    const b = e.target.closest('[data-m]'); if (!b) return;
    mode = b.dataset.m;
    host.querySelectorAll('[data-m]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.m === mode)));
    draw();
  });
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day);
  });

  const drawRings = () => {
    const H = 250, { ctx, w } = fitCanvas(host.querySelector('#rings'), H);
    const n = Math.max(1, llm.length), cellW = w / n;
    const R = Math.max(15, Math.min(cellW / 2 - 18, 56));
    ctx.clearRect(0, 0, w, H);
    llm.forEach((r, i) => {
      const cx = cellW * (i + .5), cy = 102;
      ctx.lineWidth = 12; ctx.lineCap = 'round';
      ctx.strokeStyle = cssVar('--track');
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.2832); ctx.stroke();
      if (r.hit_rate != null) {
        const g = ctx.createLinearGradient(cx - R, cy - R, cx + R, cy + R);
        g.addColorStop(0, cssVar('--acc')); g.addColorStop(1, cssVar('--acc2'));
        ctx.strokeStyle = g; ctx.shadowBlur = 16; ctx.shadowColor = cssVar('--acc');
        ctx.beginPath();
        ctx.arc(cx, cy, R, -Math.PI / 2, -Math.PI / 2 + r.hit_rate * 6.2832); ctx.stroke();
        ctx.shadowBlur = 0;
      }
      ctx.textAlign = 'center';
      ctx.fillStyle = r.hit_rate == null ? cssVar('--warn') : cssVar('--fg');
      ctx.font = '700 15px -apple-system, system-ui, sans-serif';
      ctx.fillText(r.hit_rate == null ? '说不准' : (r.hit_rate * 100).toFixed(1) + '%', cx, cy + 5);
      ctx.fillStyle = cssVar('--dim'); ctx.font = '12px -apple-system, system-ui, sans-serif';
      ctx.fillText(r.label.slice(0, 13), cx, cy + R + 26);
      ctx.fillStyle = cssVar('--dim2'); ctx.font = '11px -apple-system, system-ui, sans-serif';
      ctx.fillText(`${r.vendor} · ${fmt(r.input_total)}`, cx, cy + R + 42);
      ctx.textAlign = 'left';
    });
  };
  drawRings();
  const onR = () => drawRings();
  addEventListener('resize', onR); addEventListener('atlas:theme', onR);
  draw(); enter('.hero, .sec, .cell, .orow, .slab', host);
  return { dispose() { removeEventListener('resize', onR); removeEventListener('atlas:theme', onR); } };
}
