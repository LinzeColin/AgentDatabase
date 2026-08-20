import { esc, fmt, pct, go, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { leaf, h2, plate, plates, carve, marginal, warn, rub, fold, chip, seal, rate } from '../kit.js';

export async function render(host) {
  const C = D.coupling() || {};
  const edges = (C.edges || []).slice(0, 50);
  const nodes = new Map((C.nodes || []).map(n => [n.id, n]));
  const label = id => (nodes.get(id) || {}).label || id.split(':').pop();

  host.innerHTML =
    leaf({
      title: '哪些事总是一起出现',
      lead: `边 = 同一场会话里共同出现的次数。只统计你亲自开口的会话。
             ${C.dropped_edges ? `另有 ${C.dropped_edges} 条边太弱没画。` : ''}`,
      body: plate({ k: '最强的一对', big: true, size: 'sm',
        v: edges.length ? `${esc(label(edges[0].a))} × ${esc(label(edges[0].b))}` : '—',
        n: edges.length ? `同场出现 ${edges[0].w} 次` : '' })
        + carve(edges.slice(0, 20).map(e => ({
            k: `${label(e.a)} × ${label(e.b)}`, v: e.w, label: `${e.w} 次`,
          })))
        + (C.note ? marginal(esc(C.note)) : ''),
    })
    + leaf({
      title: '全部节点', lead: '按权重排。', cols: false,
      body: rub([{ t: '节点' }, { t: '类型' }, { t: '权重', r: true }],
        (C.nodes || []).slice().sort((a, b) => b.w - a.w).map(n => [esc(n.label), esc(n.kind), String(n.w)])),
    });
}
