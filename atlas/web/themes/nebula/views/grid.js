import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 网格。星云版不铺网格 —— 按主题筛，把命中的会话变成射线。
export async function render(host, arg) {
  const topic = arg || '';
  const list = D.sessions({ kind: 'human', topic });
  const names = D.topicNames ? D.topicNames() : Object.keys(D.slice(0).topics || {});

  hud([{ k: topic ? '这个主题' : '全部', v: String(list.length) }]);

  host.innerHTML = stage({
    eyebrow: '结构 · 网格',
    title: topic || '按主题看',
    hint: topic ? `命中「${esc(topic)}」的每一场。点一条进那天。`
                : '选一个主题。<b>一次对话最多算三个主题</b>，所以各主题之和大于总数。',
    body: headline(topic ? '命中的场次' : '主题数', String(topic ? list.length : names.length),
      topic ? `占你全部开口的 ${pct(list.length / Math.max(1, D.meta().sessions_human))}` : '点一条进去')
      + (topic ? '' : beams(Object.entries(D.slice(0).topics).sort((a, b) => b[1] - a[1])
          .map(([t, n]) => ({ k: t, v: n, c: topicColor(t), attr: `data-topic="${esc(t)}"` }))))
      + (topic ? beams(list.slice(0, 60).map(s => ({
          k: (s.n || '（没有标题）').slice(0, 50), v: s.u || 1,
          sub: `${s.d} · ${s.p || '未标注'}`, label: `${s.u || 0} 轮`,
          c: topicColor(topic), attr: `data-day="${esc(s.d)}"`,
        }))) : '')
      + (topic ? `<p class="hint"><a href="#/grid" style="color:var(--acc)">← 回到全部主题</a></p>` : ''),
  });

  host.addEventListener('click', e => {
    const t = e.target.closest('[data-topic]'), d = e.target.closest('[data-day]');
    if (t) go('grid', t.dataset.topic);
    else if (d) go('day', d.dataset.day);
  });
  enter('.headline, .beam', host);
}
