import { esc, fmt, go, local, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, table, kv, warn, rate } from '../kit.js';

export async function render(host, arg) {
  const q = new URLSearchParams((arg || '').replace(/^\?/, ''));
  let f = { kind: 'human', topic: q.get('t') || '', project: q.get('p') || '', source: q.get('s') || '',
            sort: 't', limit: 0 };
  const projs = [...new Set(D.A().sessions.map(s => s.p).filter(Boolean))].sort();
  const srcs = [...new Set(D.A().sessions.map(s => s.s))].sort();

  host.innerHTML = `
${sec('GRID', '全部会话铺开。每格一场，大小＝你说了几次，颜色＝主主题。')}
<div class="ctl">
  <select id="kind"><option value="human">只看你开口的</option><option value="all">全部（含机器）</option><option value="mach">只看机器</option></select>
  <select id="topic"><option value="">全部主题</option>${
    D.topicNames().map(t => `<option value="${esc(t)}" ${f.topic === t ? 'selected' : ''}>${esc(t)}</option>`).join('')}
    <option value="__none" ${f.topic === '__none' ? 'selected' : ''}>未分类</option></select>
  <select id="proj"><option value="">全部项目</option>${
    projs.map(p => `<option value="${esc(p)}" ${f.project === p ? 'selected' : ''}>${esc(p)}</option>`).join('')}</select>
  <select id="src"><option value="">全部来源</option>${
    srcs.map(s => `<option value="${esc(s)}" ${f.source === s ? 'selected' : ''}>${esc(s)}</option>`).join('')}</select>
  <select id="sort"><option value="t">按时间</option><option value="u">按你说话次数</option><option value="ti">按 token</option><option value="o">按工具数</option></select>
  <span class="tag" id="cnt"></span>
</div>
<div id="sum"></div>
<div id="cells"></div>
<div id="tbl"></div>`;

  const draw = () => {
    let list = D.sessions({ kind: f.kind, topic: f.topic, project: f.project, source: f.source });
    list = list.slice().sort(f.sort === 't' ? (a, b) => a.t < b.t ? 1 : -1 : (a, b) => (b[f.sort] || 0) - (a[f.sort] || 0));
    host.querySelector('#cnt').textContent = `${list.length} 场`;
    const agg = D.aggregate(list);
    host.querySelector('#sum').innerHTML = kv([
      ['会话', String(agg.n), 'acc'], ['覆盖天数', String(agg.days), ''],
      ['你说话次数', String(agg.turns), ''], ['工具调用', String(agg.tools), ''],
      ['token 输入(含缓存)', fmt(agg.input_total), ''], ['缓存命中率', rate(agg.hit), 'acc'],
      ['未分类', String(agg.unclassified), agg.unclassified ? 'warn' : ''],
      ['最常见主题', agg.topics.length ? `${esc(agg.topics[0][0])} ${agg.topics[0][1]}` : '—', ''],
    ]);
    const shown = list.slice(0, 2600);
    host.querySelector('#cells').innerHTML = `<div class="gwrap">${shown.map(s => {
      const sz = Math.min(24, 6 + Math.sqrt(Math.max(1, s.u)) * 2.8);
      return `<i data-day="${s.d}" style="width:${sz}px;height:${sz}px;background:${s.tp[0] ? topicColor(s.tp[0]) : 'var(--dim2)'};opacity:${s.k === 'human' ? .92 : .34}"
        title="${esc(s.d)} ${esc(s.n || '')} · ${esc(s.tp.join('、') || '未分类')}"></i>`;
    }).join('')}</div>${list.length > shown.length
      ? `<p class="hint">只画了前 ${shown.length} 格（共 ${list.length} 场）。剩下的没画出来，不是没有。</p>` : ''}`;

    host.querySelector('#tbl').innerHTML = table(
      [{ t: '时间' }, { t: '来源' }, { t: '项目' }, { t: '标题' }, { t: '主题' },
       { t: '你说', r: true }, { t: '工具', r: true }, { t: 'token 入', r: true }],
      list.slice(0, 120).map(s => [
        `<span class="lnk" data-day="${s.d}">${s.d.slice(5)} ${local(s.t).toISOString().slice(11, 16)}</span>`,
        esc(s.s), `<span class="tag">${esc(s.p || '—')}</span>`,
        `<span class="tag">${esc(s.n || '(无标题)')}</span>`,
        s.tp.map(t => `<span class="tag" style="color:${topicColor(t)}">${esc(t)}</span>`).join('') || '<span class="tag">未分类</span>',
        String(s.u), String(s.o), fmt(s.ti + s.tc)]));
    enter('tbody tr', host);
  };

  const bind = (id, key) => host.querySelector(id).addEventListener('change', e => { f[key] = e.target.value; draw(); });
  bind('#kind', 'kind'); bind('#topic', 'topic'); bind('#proj', 'project'); bind('#src', 'source'); bind('#sort', 'sort');
  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]');
    if (d) go('day', d.dataset.day);
  });
  const st = document.createElement('style');
  st.textContent = `.gwrap{display:flex;flex-wrap:wrap;gap:3px;align-items:flex-end;margin:10px 0}
    .gwrap i{cursor:pointer;display:block}
    .gwrap i:hover{outline:1px solid var(--fg)}`;
  host.appendChild(st);
  draw();
  enter('.sec, .kv > div', host);
}
