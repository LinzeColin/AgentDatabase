import { esc, fmt, go, local, enter, topicColor } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { sec, bento, orbit, drawer, table, pill, rate } from '../kit.js';

export async function render(host, arg) {
  const q = new URLSearchParams((arg || '').replace(/^\?/, ''));
  const f = { kind: 'human', topic: q.get('t') || '', project: q.get('p') || '', source: q.get('s') || '', sort: 't' };
  const projs = [...new Set(D.A().sessions.map(s => s.p).filter(Boolean))].sort();
  const srcs = [...new Set(D.A().sessions.map(s => s.s))].sort();

  host.innerHTML = `
${sec('星群', '每一颗 = 一场会话。大小＝你说了几次，颜色＝主主题。')}
<div class="ctl">
  <select id="kind"><option value="human">只看你开口的</option><option value="all">全部（含机器）</option><option value="mach">只看机器</option></select>
  <select id="topic"><option value="">全部主题</option>${D.topicNames().map(t=>`<option value="${esc(t)}" ${f.topic===t?'selected':''}>${esc(t)}</option>`).join('')}<option value="__none" ${f.topic==='__none'?'selected':''}>未分类</option></select>
  <select id="proj"><option value="">全部项目</option>${projs.map(p=>`<option value="${esc(p)}" ${f.project===p?'selected':''}>${esc(p)}</option>`).join('')}</select>
  <select id="src"><option value="">全部来源</option>${srcs.map(s=>`<option value="${esc(s)}" ${f.source===s?'selected':''}>${esc(s)}</option>`).join('')}</select>
  <select id="sort"><option value="t">按时间</option><option value="u">按你说话次数</option><option value="ti">按 token</option><option value="o">按工具数</option></select>
</div>
<div id="sum"></div>
<div class="card w6"><div id="cells"></div></div>
<div id="rest"></div>`;

  const draw = () => {
    let list = D.sessions(f);
    list = list.slice().sort(f.sort === 't' ? (a, b) => a.t < b.t ? 1 : -1 : (a, b) => (b[f.sort] || 0) - (a[f.sort] || 0));
    const agg = D.aggregate(list);
    host.querySelector('#sum').innerHTML = bento([
      { k: '会话', v: String(agg.n), n: `覆盖 ${agg.days} 天`, w: 3, tone: 'acc' },
      { k: 'token 输入(含缓存)', v: fmt(agg.input_total), n: `命中率 ${rate(agg.hit)}`, w: 3, alt: true },
      { k: '你说话次数', v: String(agg.turns), n: `工具 ${agg.tools} 次` },
      { k: '未分类', v: String(agg.unclassified), n: '如实留空，不硬塞' },
      { k: '最常见主题', v: `<span style="font-size:22px">${agg.topics.length ? esc(agg.topics[0][0]) : '—'}</span>`,
        n: agg.topics.length ? `${agg.topics[0][1]} 场` : '' },
    ]);
    const shown = list.slice(0, 2600);
    host.querySelector('#cells').innerHTML = `<div class="gwrap">${shown.map(s => {
      const sz = Math.min(26, 7 + Math.sqrt(Math.max(1, s.u)) * 3);
      return `<i data-day="${s.d}" style="width:${sz}px;height:${sz}px;background:${s.tp[0] ? topicColor(s.tp[0]) : 'var(--dim2)'};opacity:${s.k === 'human' ? .9 : .3}"
        title="${esc(s.d)} ${esc(s.n || '')} · ${esc(s.tp.join('、') || '未分类')}"></i>`;
    }).join('')}</div>${list.length > shown.length ? `<p class="hint" style="margin-top:12px">只画了前 ${shown.length} 颗（共 ${list.length} 场）。剩下的没画出来，不是没有。</p>` : ''}`;
    host.querySelector('#rest').innerHTML = drawer(`展开明细表（前 120 行 / 共 ${list.length} 场）`, table(
      [{ t: '时间' }, { t: '来源' }, { t: '项目' }, { t: '标题' }, { t: '主题' }, { t: '你说', r: true }, { t: 'token 入', r: true }],
      list.slice(0, 120).map(s => [
        `<span class="lnk" data-day="${s.d}">${s.d.slice(5)} ${local(s.t).toISOString().slice(11, 16)}</span>`,
        esc(s.s), esc(s.p || '—'), esc(s.n || '(无标题)'),
        s.tp.map(t => `<span class="pill" style="color:${topicColor(t)}">${esc(t)}</span>`).join('') || pill('未分类'),
        String(s.u), fmt(s.ti + s.tc)])));
    enter('.card', host);
  };
  ['#kind','#topic','#proj','#src','#sort'].forEach((id, i) => {
    const key = ['kind','topic','project','source','sort'][i];
    host.querySelector(id).onchange = e => { f[key] = e.target.value; draw(); };
  });
  host.addEventListener('click', e => { const d = e.target.closest('[data-day]'); if (d) go('day', d.dataset.day); });
  const st = document.createElement('style');
  st.textContent = `.gwrap{display:flex;flex-wrap:wrap;gap:4px;align-items:flex-end}
    .gwrap i{border-radius:50%;cursor:pointer;display:block;transition:transform .3s cubic-bezier(.22,1,.36,1)}
    .gwrap i:hover{transform:scale(1.6);box-shadow:0 0 14px -2px currentColor}`;
  host.appendChild(st);
  draw(); enter('.sec, .card', host);
}
