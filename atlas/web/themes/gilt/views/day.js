import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

import { day as day_ } from '../../../core/app.js';

// 一天。第一页是这天的总账，后面每页 20 场。
export async function render(host, arg) {
  const ds = D.days();
  const dstr = arg || (ds.length ? ds[ds.length - 1].d : '');
  let j;
  try { j = await day_(dstr); }
  catch (e) { host.innerHTML = leaf({ title: dstr, lead: '', body: warn(`<b>那一天没有记录。</b>${esc(e.message || e)}`) }); return; }

  const rows = j.sessions || [];
  const hum = rows.filter(r => r.kind === 'human');
  const row = ds.find(d => d.d === dstr) || {};
  const PER = 20, chunks = [];
  for (let i = 0; i < rows.length; i += PER) chunks.push(rows.slice(i, i + PER));

  host.innerHTML =
    leaf({
      title: dstr,
      lead: `这一天共 ${rows.length} 场，其中你自己开口 ${hum.length} 场。`,
      body: plate({ k: '你开口的次数', v: String(hum.length), big: true,
        n: `另有 ${rows.length - hum.length} 场是机器在跑` })
        + plates([
          { k: '轮次', v: String(row.turns || 0) },
          { k: '工具调用', v: String(row.tools || 0) },
          { k: '工具失败', v: String(row.errors_tool || 0), n: '真实的 is_error，不是词频' },
          { k: 'token', v: fmt((row.tok_in || 0) + (row.tok_cache_r || 0)) },
        ]),
    })
    + chunks.map((c, i) => leaf({
        title: `${dstr} · 第 ${i + 1} 叠`,
        lead: `共 ${chunks.length} 叠，每叠 ${PER} 场。`,
        cols: false,
        body: rub([{ t: '开始' }, { t: '来源' }, { t: '项目' }, { t: '标题' }, { t: '轮', r: true }],
          c.map(s => [esc((s.start || '').slice(11, 16)), esc(s.source), esc(s.project || '—'),
            esc((s.title || '').slice(0, 56)), String(s.turns || 0)])),
      })).join('');
}
