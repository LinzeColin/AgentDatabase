// core/select.js —— 纯数据选择器。**这一层不产出任何标记、不含任何样式。**
// 三套主题各自决定怎么把这些数字画出来；共享的只有「数字是什么」。

import { S } from './app.js';

export const A = () => S.atlas;

export const meta = () => A().meta;
export const slice = k => A().slices[String(k)];
export const SLICE_KEYS = ['3', '7', '15', '30', '45', '60', '90', '180', '0'];

/** 按会话数／主题／项目筛出一批会话。所有视图共用同一套筛法，口径才一致。 */
export function sessions({ kind = 'human', topic = '', project = '', source = '',
                           from = '', to = '', limit = 0 } = {}) {
  let out = A().sessions.filter(s =>
    (kind === 'all' || (kind === 'human' ? s.k === 'human' : s.k !== 'human')) &&
    (!topic || (topic === '__none' ? !s.tp.length : s.tp.includes(topic))) &&
    (!project || s.p === project) &&
    (!source || s.s === source) &&
    (!from || s.d >= from) && (!to || s.d <= to));
  if (limit) out = out.slice(0, limit);
  return out;
}

/** 会话切片：按「最近 N 场」而不是「最近 N 天」取，Owner 明确要求两种切法都要有。 */
export function lastNSessions(n, kind = 'human') {
  const all = A().sessions.filter(s => kind === 'all' || (kind === 'human' ? s.k === 'human' : s.k !== 'human'));
  return all.slice(-n);
}

export function aggregate(list) {
  const topics = new Map(), projects = new Map(), sources = new Map(), days = new Set();
  let turns = 0, tools = 0, ti = 0, to = 0, tc = 0;
  for (const s of list) {
    days.add(s.d);
    turns += s.u; tools += s.o; ti += s.ti; to += s.to; tc += s.tc;
    for (const t of s.tp) topics.set(t, (topics.get(t) || 0) + 1);
    if (s.p) projects.set(s.p, (projects.get(s.p) || 0) + 1);
    sources.set(s.s, (sources.get(s.s) || 0) + 1);
  }
  const rawIn = ti + tc;
  return {
    n: list.length, days: days.size, turns, tools,
    tok_in_excl: ti, cached: tc, output: to, input_total: rawIn,
    hit: rawIn ? tc / rawIn : null,
    topics: [...topics].sort((a, b) => b[1] - a[1]),
    projects: [...projects].sort((a, b) => b[1] - a[1]),
    sources: [...sources].sort((a, b) => b[1] - a[1]),
    unclassified: list.filter(s => !s.tp.length).length,
  };
}

export const days = () => A().days;
export const weeks = () => A().weeks;
export const projects = () => A().projects;
export const tokens = () => A().tokens;
export const economics = () => A().economics;
export const coupling = () => A().coupling;
export const lessons = () => A().lessons;
export const opportunities = () => A().opportunities;
export const insights = () => A().insights;
export const topicNames = () => A().topic_names;
export const ladder = () => A().ladder;

/** 主题在各周的占比序列，给堆叠图用。 */
export function topicSeries() {
  const W = A().trend.weeks.filter(w => w.human > 0);
  const names = topicNames().filter(t => W.some(w => (w.count[t] || 0) > 0));
  return { weeks: W, names };
}

/** 一个项目/主题在耦合网络里连到谁 —— 宇宙那一屏要靠这个显示「关联」。 */
export function neighbours(nodeId) {
  const c = coupling();
  const out = [];
  for (const e of c.edges) {
    if (e.a === nodeId) out.push({ id: e.b, w: e.w });
    else if (e.b === nodeId) out.push({ id: e.a, w: e.w });
  }
  return out.sort((x, y) => y.w - x.w);
}
