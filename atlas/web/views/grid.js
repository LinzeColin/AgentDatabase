import { S, esc, go, topicColor, fmt, local } from '../app.js';

export async function render(host) {
  const a = S.atlas;
  const projects = [...new Set(a.sessions.map(s => s.p).filter(Boolean))].sort();

  host.innerHTML = `
    <h2>网格</h2>
    <p class="sub">全部会话铺开。每格一场，大小＝你说了几次，颜色＝主主题。筛完点任一格进那一天。</p>
    <div class="flexbar">
      <select id="kind"><option value="human">只看你开口的</option>
        <option value="all">全部（含机器）</option><option value="mach">只看机器</option></select>
      <select id="topic"><option value="">全部主题</option>
        ${a.topic_names.map(t => `<option value="${esc(t)}">${esc(t)}</option>`).join('')}
        <option value="__none">未分类</option></select>
      <select id="proj"><option value="">全部项目</option>
        ${projects.map(p => `<option value="${esc(p)}">${esc(p)}</option>`).join('')}</select>
      <select id="sort"><option value="t">按时间</option><option value="u">按你说话次数</option>
        <option value="ti">按 token</option></select>
      <span class="muted" id="cnt" style="font-size:12.5px"></span>
    </div>
    <div class="panel" id="wrap"></div>
    <div class="panel" id="tbl"></div>`;

  const $ = q => host.querySelector(q);
  const draw = () => {
    const k = $('#kind').value, t = $('#topic').value, p = $('#proj').value, so = $('#sort').value;
    let list = a.sessions.filter(s =>
      (k === 'all' || (k === 'human' ? s.k === 'human' : s.k !== 'human')) &&
      (!t || (t === '__none' ? s.tp.length === 0 : s.tp.includes(t))) &&
      (!p || s.p === p));
    list = list.slice().sort(so === 't' ? (x, y) => x.t < y.t ? 1 : -1 : (x, y) => (y[so] || 0) - (x[so] || 0));
    $('#cnt').textContent = `${list.length} 场`;
    $('#wrap').innerHTML = `<div class="gwrap">${list.slice(0, 3000).map(s => {
      const sz = Math.min(26, 7 + Math.sqrt(Math.max(1, s.u)) * 3);
      const c = s.tp[0] ? topicColor(s.tp[0]) : '#39434f';
      return `<i class="gcell" data-day="${s.d}" style="width:${sz}px;height:${sz}px;background:${c};opacity:${s.k === 'human' ? .9 : .35}"
        title="${esc(s.d)} ${esc(s.n || '')} · ${esc(s.tp.join('、') || '未分类')}"></i>`;
    }).join('')}</div>${list.length > 3000 ? `<div class="muted" style="font-size:12px;margin-top:8px">
      只画了前 3000 格（共 ${list.length} 场）。剩下的没画出来，不是没有。</div>` : ''}`;

    $('#tbl').innerHTML = `<table><thead><tr><th>时间</th><th>标题</th><th>项目</th>
      <th class="num">你说</th><th class="num">工具</th><th class="num">token 入</th></tr></thead><tbody>
      ${list.slice(0, 60).map(s => `<tr>
        <td><button class="rowbtn" data-day="${s.d}">${s.d.slice(5)} ${local(s.t).toISOString().slice(11, 16)}</button></td>
        <td style="max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(s.n || '(无标题)')}
          ${s.tp.map(x => `<span class="chip" style="border-color:${topicColor(x)}">${esc(x)}</span>`).join('')}</td>
        <td class="muted">${esc(s.p || '—')}</td><td class="num">${s.u}</td>
        <td class="num muted">${s.o}</td><td class="num muted">${fmt(s.ti)}</td></tr>`).join('')}
    </tbody></table>${list.length > 60 ? `<div class="muted" style="font-size:12px;margin-top:8px">表格只列前 60 行。</div>` : ''}`;
  };
  ['#kind', '#topic', '#proj', '#sort'].forEach(q => $(q).addEventListener('change', draw));
  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
  draw();

  const st = document.createElement('style');
  st.textContent = `.gwrap{display:flex;flex-wrap:wrap;gap:3px;align-items:flex-end}
    .gcell{border-radius:3px;cursor:pointer;display:block}
    .gcell:hover{outline:1.5px solid #fff}`;
  host.appendChild(st);
}
