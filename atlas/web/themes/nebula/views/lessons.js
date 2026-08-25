import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 沉淀。头条是「隔天又问过同一件事的组数」——
// 它不降，说明答案没留在任何 agent 找得到的地方。
export async function render(host) {
  const L = D.lessons();
  const R = L.repeats || [], B = L.batches || [], PC = L.pointer_coverage || {};

  hud([{ k: '跨天复发', v: String(R.length) }, { k: '批量重放', v: String(B.length) }]);

  host.innerHTML = stage({
    eyebrow: '档案 · 沉淀',
    title: '同一件事你问过几次',
    hint: `一个问题被反复问，说明上一次的答案没沉淀下来。
           <b>跨天复发</b>和<b>单日批量</b>是两种病：前者该写进 AGENTS.md，后者该做成脚本。`,
    body: headline('隔天又问过的组数', String(R.length),
      PC.rate != null ? `其中 ${PC.with_pointer} 组指得回具体产物（${pct(PC.rate)}）` : '')
      + (PC.why_low ? warn(`<b>指针覆盖率没达标，如实报低。</b>${esc(PC.why_low)}`) : '')
      + beams(R.map(r => ({
          k: (r.text || '').slice(0, 46), v: r.n,
          sub: `${r.first} → ${r.last}　${r.days} 天　${r.state === '有指针' ? '有产物' : '没有产物'}`,
          label: `${r.n} 次`, c: r.state === '有指针' ? 'var(--acc3)' : 'var(--warn)',
        })))
      + sheet('上次落在哪（指针）', table(
          [{ t: '问题' }, { t: '文件' }, { t: '命令' }],
          R.map(r => [esc((r.text || '').slice(0, 40)),
            (r.files || []).map(f => `<code style="font-size:11px">${esc(f)}</code>`).join('<br>') || '—',
            (r.cmds || []).map(c => `<code style="font-size:11px">${esc(c)}</code>`).join('<br>') || '—'])))
      + sheet(`一天之内被投喂多次的（${B.length} 条）`, table(
          [{ t: '提示词' }, { t: '次数', r: true }, { t: '天', r: true }],
          B.map(b => [esc((b.text || '').slice(0, 60)), String(b.n), String(b.days)])))
      + sheet('工具失败最密集的项目', table(
          [{ t: '项目' }, { t: '工具失败', r: true }, { t: '每场', r: true }, { t: '你提到报错', r: true }],
          (L.pain || []).map(p => [esc(p.name), String(p.tool ?? '—'), String(p.per_tool ?? '—'), String(p.errors)])))
      + (L.pain_note ? warn(esc(L.pain_note)) : ''),
  });
  enter('.headline, .beam, .warnbox', host);
}
