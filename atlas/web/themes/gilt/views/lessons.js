import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

export async function render(host) {
  const L = D.lessons();
  const R = L.repeats || [], B = L.batches || [], PC = L.pointer_coverage || {};
  host.innerHTML =
    leaf({
      title: '同一件事你问过几次',
      lead: `一个问题被反复问，说明上一次的答案没沉淀下来。
             <b>跨天复发</b>和<b>单日批量</b>是两种病：前者该写进 AGENTS.md，后者该做成脚本。`,
      body: plate({ k: '隔天又问过的组数', v: String(R.length), big: true,
        n: PC.rate != null ? `其中 ${PC.with_pointer} 组指得回具体产物（${pct(PC.rate)}）` : '' })
        + (PC.why_low ? warn(`<b>指针覆盖率没达标，如实报低。</b>${esc(PC.why_low)}`) : '')
        + carve(R.map(r => ({
            k: (r.text || '').slice(0, 40), v: r.n,
            label: `${r.n} 次　${r.days} 天　${r.state === '有指针' ? '有产物' : '没有产物'}`,
          }))),
    })
    + leaf({
      title: '上次落在哪', lead: '只给指针，不写摘要 —— 压缩改写会牺牲「精确复述当时的东西」。',
      cols: false,
      body: rub([{ t: '问题' }, { t: '文件' }, { t: '命令' }],
        R.map(r => [esc((r.text || '').slice(0, 34)),
          (r.files || []).map(f => `<code style="font-size:11px">${esc(f)}</code>`).join('<br>') || '—',
          (r.cmds || []).map(c => `<code style="font-size:11px">${esc(c)}</code>`).join('<br>') || '—'])),
    })
    + leaf({
      title: '本该做成脚本的', lead: `同一段提示词在一天之内被投喂多次，共 ${B.length} 条。`,
      cols: false,
      body: rub([{ t: '提示词' }, { t: '次数', r: true }, { t: '天', r: true }],
          B.map(b => [esc((b.text || '').slice(0, 56)), String(b.n), String(b.days)]))
        + h2('工具失败最密集的项目')
        + rub([{ t: '项目' }, { t: '工具失败', r: true }, { t: '每场', r: true }, { t: '你提到报错', r: true }],
            (L.pain || []).map(p => [esc(p.name), String(p.tool ?? '—'), String(p.per_tool ?? '—'), String(p.errors)]))
        + (L.pain_note ? marginal(esc(L.pain_note)) : ''),
    });
}
