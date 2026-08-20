import { esc, fmt, pct, go, enter, countUp, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { stage, headline, reads, beams, sheet, table, warn, pill, state, rate, hud } from '../kit.js';

// 耦合星图。这一屏本来就该是三维的 —— 所以中央只放判读，图在背景里。
export async function render(host) {
  const C = D.coupling() || {};
  const edges = (C.edges || []).slice(0, 40);
  const nodes = new Map((C.nodes || []).map(n => [n.id, n]));
  const label = id => (nodes.get(id) || {}).label || id.split(':').pop();

  hud([{ k: '节点', v: String((C.nodes || []).length) }, { k: '边', v: String((C.edges || []).length) }]);

  host.innerHTML = stage({
    eyebrow: '结构 · 耦合星图',
    title: '哪些事总是一起出现',
    hint: `边 = 同一场会话里共同出现的次数。<b>只统计你亲自开口的会话。</b>
           ${C.dropped_edges ? `另有 ${C.dropped_edges} 条边太弱没画。` : ''}`,
    body: headline('最强的一对', edges.length ? `${label(edges[0].a)} × ${label(edges[0].b)}` : '—',
      edges.length ? `同场出现 ${edges[0].w} 次` : '')
      + beams(edges.map(e => ({
          k: `${label(e.a)} × ${label(e.b)}`, v: e.w, label: `${e.w} 次`,
          c: e.a.startsWith('topic') && e.b.startsWith('topic') ? 'var(--acc2)' : 'var(--acc)',
        })))
      + (C.note ? warn(esc(C.note)) : '')
      + sheet('全部节点', table([{ t: '节点' }, { t: '类型' }, { t: '权重', r: true }],
          (C.nodes || []).slice().sort((a, b) => b.w - a.w).map(n =>
            [esc(n.label), esc(n.kind), String(n.w)]))),
  });
  enter('.headline, .beam', host);
}
