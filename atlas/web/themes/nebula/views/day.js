import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 一天。这一屏的镜头由视图接管 —— 必须 hold，否则滚动那条线会把镜头拽回最新那天。
import { day as day_ } from '../../../core/app.js';
import { holdCamera, scene } from '../shell.js';

export async function render(host, arg) {
  const ds = D.days();
  const day = arg || (ds.length ? ds[ds.length - 1].d : '');
  let j;
  try { j = await day_(day); }
  catch (e) { host.innerHTML = warn(`<b>那一天没有记录。</b>${esc(e.message || e)}`); return; }

  const rows = j.sessions || [];
  const hum = rows.filter(r => r.kind === 'human');
  const row = ds.find(d => d.d === day) || {};

  holdCamera(true);
  try { scene()?.flyToDay(day); } catch { /* 天幕没点起来就算了 */ }

  hud([{ k: '这一天', v: esc(day) }, { k: '你开口', v: String(hum.length) }]);

  host.innerHTML = stage({
    eyebrow: '时间 · 一天',
    title: day,
    hint: `这一天的每一场。<b>镜头已经飞到这一天</b> —— 离开本屏会交还给滚动。`,
    body: headline('你开口的次数', String(hum.length),
      `另有 ${rows.length - hum.length} 场是机器在跑`)
      + reads([
        { k: '轮次', v: String(row.turns || 0) },
        { k: '工具调用', v: String(row.tools || 0) },
        { k: '工具失败', v: String(row.errors_tool || 0), tone: (row.errors_tool || 0) > 40 ? 'warn' : '' },
        { k: 'token', v: fmt((row.tok_in || 0) + (row.tok_cache_r || 0)) },
      ])
      + beams(hum.slice(0, 40).map(s => ({
          k: (s.title || '（没有标题）').slice(0, 54), v: s.turns || 1,
          sub: `${(s.project || '未标注')} · ${s.source}`,
          label: `${s.turns || 0} 轮`, c: topicColor((s.topics || [])[0]),
        })))
      + sheet(`全部 ${rows.length} 场`, table(
          [{ t: '开始' }, { t: '来源' }, { t: '项目' }, { t: '标题' }, { t: '轮', r: true }],
          rows.map(s => [esc((s.start || '').slice(11, 16)), esc(s.source), esc(s.project || '—'),
            esc((s.title || '').slice(0, 60)), String(s.turns || 0)]))),
  });

  enter('.headline, .read, .beam', host);
  return { dispose() { holdCamera(false); } };
}
