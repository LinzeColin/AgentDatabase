import { S, esc, go, topicColor, local } from '../app.js';

export async function render(host) {
  const a = S.atlas;
  const byDay = new Map();
  for (const s of a.sessions) {
    if (!byDay.has(s.d)) byDay.set(s.d, []);
    byDay.get(s.d).push(s);
  }
  const days = a.days.slice().reverse();

  host.innerHTML = `
    <h2>时间轴</h2>
    <p class="sub">每一行是一天，横轴是当天 00:00→24:00（悉尼时间）。一竖＝一场会话，高度＝你说了几次。</p>
    <div class="flexbar">
      <label class="muted" style="font-size:12.5px"><input type="checkbox" id="mach"> 画上机器扇出</label>
      <select id="range">
        <option value="30">最近 30 天</option><option value="60">最近 60 天</option>
        <option value="90">最近 90 天</option><option value="0">全部 ${days.length} 天</option>
      </select>
    </div>
    <div class="panel" style="padding:10px 14px">
      <div style="display:flex;gap:8px;color:var(--dim2);font-size:11px;margin:0 0 6px 92px">
        ${[0, 3, 6, 9, 12, 15, 18, 21].map(h => `<span style="flex:1">${String(h).padStart(2, '0')}</span>`).join('')}
      </div>
      <div id="rows"></div>
    </div>`;

  const draw = () => {
    const n = +host.querySelector('#range').value;
    const showMach = host.querySelector('#mach').checked;
    const list = n ? days.slice(0, n) : days;
    host.querySelector('#rows').innerHTML = list.map(d => {
      const ss = (byDay.get(d.d) || []).filter(s => showMach || s.k === 'human');
      const marks = ss.map(s => {
        const lt = local(s.t);
        const x = (lt.getUTCHours() + lt.getUTCMinutes() / 60) / 24 * 100;
        const h = Math.min(18, 4 + Math.sqrt(Math.max(1, s.u)) * 3.2);
        const c = s.tp[0] ? topicColor(s.tp[0]) : '#3f4954';
        return `<i style="left:${x.toFixed(2)}%;height:${h}px;background:${c};opacity:${s.k === 'human' ? .95 : .32}"
          title="${esc(local(s.t).toISOString().slice(11, 16))} ${esc(s.n || '')}"></i>`;
      }).join('');
      return `<div class="tlrow"><button class="rowbtn tlday" data-day="${d.d}">${d.d.slice(5)}
        <span class="muted">${d.human}</span></button><div class="tlbar">${marks}</div></div>`;
    }).join('');
  };
  host.querySelector('#range').addEventListener('change', draw);
  host.querySelector('#mach').addEventListener('change', draw);
  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
  draw();

  const st = document.createElement('style');
  st.textContent = `
    .tlrow{display:flex;align-items:center;gap:8px;height:22px}
    .tlday{width:84px;font-size:12px;font-variant-numeric:tabular-nums;flex:none;text-align:left}
    .tlday .muted{font-size:11px;margin-left:4px}
    .tlbar{position:relative;flex:1;height:20px;border-bottom:1px solid #171d24}
    .tlbar i{position:absolute;bottom:1px;width:2.5px;border-radius:1px}`;
  host.appendChild(st);
}
