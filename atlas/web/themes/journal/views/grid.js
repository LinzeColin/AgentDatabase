import { esc, fmt, go, local, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, lede, p, n, big, figure, rank, table, rate } from '../kit.js';

export async function render(host, arg) {
  const q = new URLSearchParams((arg || '').replace(/^\?/, ''));
  const f = { kind: 'human', topic: q.get('t') || '', project: q.get('p') || '', source: q.get('s') || '', sort: 't' };
  const projs = [...new Set(D.A().sessions.map(s => s.p).filter(Boolean))].sort();
  const srcs = [...new Set(D.A().sessions.map(s => s.s))].sort();
  host.innerHTML = `
${sec('目录')}
${lede(`把所有会话按条件筛出来，逐条列开。这一页是索引，不是叙述。`)}
<div class="ctl">
  <select id="kind"><option value="human">只看你开口的</option><option value="all">全部</option><option value="mach">只看机器</option></select>
  <select id="topic"><option value="">全部主题</option>${D.topicNames().map(t=>`<option value="${esc(t)}" ${f.topic===t?'selected':''}>${esc(t)}</option>`).join('')}<option value="__none">未分类</option></select>
  <select id="proj"><option value="">全部项目</option>${projs.map(p=>`<option value="${esc(p)}" ${f.project===p?'selected':''}>${esc(p)}</option>`).join('')}</select>
  <select id="src"><option value="">全部来源</option>${srcs.map(s=>`<option value="${esc(s)}" ${f.source===s?'selected':''}>${esc(s)}</option>`).join('')}</select>
  <select id="sort"><option value="t">按时间</option><option value="u">按你说话次数</option><option value="ti">按 token</option></select>
</div>
<div id="sum"></div><div id="rest"></div>`;
  const draw = () => {
    let list = D.sessions(f);
    list = list.slice().sort(f.sort === 't' ? (a, b) => a.t < b.t ? 1 : -1 : (a, b) => (b[f.sort] || 0) - (a[f.sort] || 0));
    const agg = D.aggregate(list);
    host.querySelector('#sum').innerHTML = p(`筛出 ${big(agg.n)} 场，覆盖 ${n(agg.days)} 天。
      你说话 ${n(agg.turns)} 次，工具 ${n(agg.tools)} 次，token 输入 ${n(agg.input_total)}（含缓存），
      命中率 ${rate(agg.hit)}。最常见的主题是 ${agg.topics.length ? `<b>${esc(agg.topics[0][0])}</b>（${agg.topics[0][1]} 场）` : '—'}。`);
    host.querySelector('#rest').innerHTML =
      figure(rank(agg.topics.slice(0, 12).map(([t, v]) => ({ k: t, v, label: String(v) }))), '主题构成。')
      + figure(table([{ t: '时间' }, { t: '来源' }, { t: '项目' }, { t: '标题' }, { t: '你说', r: true }, { t: 'token 入', r: true }],
        list.slice(0, 150).map(s => [
          `<span class="lnk" data-day="${s.d}">${s.d.slice(5)} ${local(s.t).toISOString().slice(11, 16)}</span>`,
          esc(s.s), esc(s.p || '—'), esc((s.n || '(无标题)').slice(0, 40)), String(s.u), fmt(s.ti + s.tc)])),
        `前 150 行，共 ${list.length} 场。`);
    enter('figure, p.body', host);
  };
  ['#kind','#topic','#proj','#src','#sort'].forEach((id, i) => {
    const key = ['kind','topic','project','source','sort'][i];
    host.querySelector(id).onchange = e => { f[key] = e.target.value; draw(); };
  });
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  draw(); enter('.sec, p.body', host);
}
