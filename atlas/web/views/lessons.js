import { S, esc, go, topicColor } from '../app.js';

export async function render(host) {
  const a = S.atlas, L = a.lessons;
  if (!L) { host.innerHTML = '<div class="note"><b>状态：没做。</b>这一页的数据还没生成。</div>'; return; }

  host.innerHTML = `
    <h2>沉淀</h2>
    <p class="sub">全部从你自己的会话里数出来，没有一句是编的。${esc(L.note)}</p>

    <h2>同一件事，你问过几次</h2>
    <div class="note"><b>一个问题被反复问，说明上一次的答案没留下来。</b>
      这一栏就是「下一次该先固化什么」的清单 —— 不是批评，是省时间。</div>
    <div class="panel"><table><thead><tr><th class="num">次数</th><th class="num">横跨</th>
      <th>问的是什么</th><th>项目</th></tr></thead><tbody>
      ${L.repeats.map(r => `<tr>
        <td class="num"><b>${r.n}</b></td>
        <td class="num muted">${r.days} 天</td>
        <td style="max-width:520px">${esc(r.text)}
          <div class="muted" style="font-size:11.5px;margin-top:3px">
            <button class="rowbtn" data-day="${r.first}">${r.first}</button> →
            <button class="rowbtn" data-day="${r.last}">${r.last}</button></div></td>
        <td class="muted" style="font-size:12px">${r.projects.map(p => esc(p)).join('<br>')}</td></tr>`).join('')}
    </tbody></table></div>

    <h2>最耗你的项目</h2>
    <p class="sub">按「每场会话平均提到多少次报错」排。不是哪个项目 bug 多，是<b>哪个项目最消耗你</b>。</p>
    <div class="panel"><table><thead><tr><th>项目</th><th class="num">每场提报错</th>
      <th class="num">会话</th><th style="width:32%"></th></tr></thead><tbody>
      ${(() => { const mx = Math.max(1, ...L.pain.map(p => p.per));
        return L.pain.map(p => `<tr><td>${esc(p.name)}</td><td class="num">${p.per}</td>
          <td class="num muted">${p.sessions}</td>
          <td><span class="bar" style="width:${(p.per / mx * 100).toFixed(0)}%;background:var(--warn)"></span></td></tr>`).join(''); })()}
    </tbody></table></div>

    <h2>最长的十场</h2>
    <p class="sub">你说话次数最多的会话。一场里说了几百次，通常意味着那次没有一遍过。</p>
    <div class="panel"><table><thead><tr><th>日期</th><th class="num">你说</th>
      <th>标题</th><th>主题</th></tr></thead><tbody>
      ${L.longest.map(x => `<tr>
        <td><button class="rowbtn" data-day="${x.day}">${x.day}</button></td>
        <td class="num"><b>${x.turns}</b></td>
        <td style="max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(x.title || '(无标题)')}</td>
        <td>${x.topics.map(t => `<span class="chip" style="border-color:${topicColor(t)}">${esc(t)}</span>`).join('') || '<span class="muted">未分类</span>'}</td>
      </tr>`).join('')}
    </tbody></table></div>

    <h2>回去过的项目</h2>
    <div class="panel"><table><thead><tr><th>项目</th><th class="num">你开口</th>
      <th>起止</th><th>谈过上线</th></tr></thead><tbody>
      ${L.revisit.map(p => `<tr><td>${esc(p.name)}</td><td class="num">${p.human}</td>
        <td class="muted" style="font-size:12px">${p.first} → ${p.last}</td>
        <td><span class="state" data-s="${p.shipped ? '通' : '没做'}">${p.shipped ? '谈过' : '没谈过'}</span></td></tr>`).join('')}
    </tbody></table></div>`;

  host.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (b) go('day', b.dataset.day);
  });
}
