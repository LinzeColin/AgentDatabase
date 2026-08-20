import { esc, fmt, pct, go, enter } from '../../../core/app.js';
import * as D from '../../../core/select.js';
import { hero, sec, grid, orbit, slab, drawer, table, warn, pill, state } from '../kit.js';

// 沉淀 → 转化。
// 这一屏不是又一块 KPI 仪表盘：Owner 打开它应该先拿到一个**决定**，而不是更多数字。
// 所以顺序是固定的：先「这周最值得做的一件事」，再「做了很多但还没变成结果」，
// 最后才是漏斗和价值路径。
export async function render(host) {
  const C = D.A().compounding;
  if (!C) {
    host.innerHTML = hero('转化', '这一块还没生成', '')
      + warn('<b>没做。</b>这一版的数据里还没有成果复利投影。');
    enter('.hero', host); return;
  }
  const S = C.stage_labels || {};

  // ── A. 这周最值得转化的一件事 ──
  const champ = C.champion ? `
${grid([
  { k: '现在这一步', v: `${esc(S[C.champion.stage] || C.champion.stage)}`, size: 'sm',
    n: '漏斗六档里的第 ' + (1 + (C.stages || []).indexOf(C.champion.stage)) + ' 档', w: 3, tone: 'acc' },
  { k: '为什么是现在', v: `${esc((C.champion.why_now || '—').slice(0, 40))}`, size: 'sm', w: 3 },
])}
${slab(`
  <div class="ck">这是什么</div>
  <div class="stitle">${esc(C.champion.problem || '—')}</div>
  <div class="cn">${esc(C.champion.why_now || '')}</div>`)}
${grid([
  { k: '7 天要做的', v: `${esc(C.champion.next_7d || '（事件里没写）')}`, size: 'sm', w: 3 },
  { k: '30 天要看到的', v: `${esc(C.champion.target_30d || '（事件里没写）')}`, size: 'sm', w: 3 },
])}
${C.champion.experiment ? `<p class="hint"><b>最小实验：</b>${esc(C.champion.experiment)}</p>` : ''}
${(C.champion.success || []).length ? `<p class="hint"><b>怎么算成了：</b>${
  (C.champion.success || []).map(x => pill(x)).join('')}</p>` : ''}
${(C.champion.stop || []).length ? warn(`<b>什么情况下停手：</b>${
  (C.champion.stop || []).map(esc).join('；')}`) : ''}
${(C.champion.evidence || []).length ? `<p class="hint"><b>依据：</b>${
  (C.champion.evidence || []).map(x => pill(x)).join('')}</p>` : ''}`
  : warn(`<b>这周没有推荐。</b>${esc(C.champion_note)}`);

  // ── B. 做了很多，但还没变成结果 ──
  const debt = (C.debt || []).length ? (C.debt || []).map(d => slab(`
  <div class="ck">${state('看这里')}　${esc(d.kind_label)}　·　${esc(d.size_label)}</div>
  <div class="stitle">${esc(d.title)}</div>
  <div class="cn" style="line-height:1.7">${esc(d.why)}</div>
  <div style="margin-top:10px">${(d.evidence || []).map(x => pill(x)).join('')}</div>
  <p class="hint" style="margin:10px 0 0"><b>下一步：</b>${esc(d.next)}</p>`)).join('')
    : warn('目前没有派生出债务信号。这可能是好事，也可能是数据还不够 —— 别当成结论。');

  // ── C. 漏斗：强调「变化」而不是累计 ──
  const stages = C.stages || [];
  const total = stages.reduce((a, s) => a + (C.funnel[s] || 0), 0);
  const funnel = orbit(stages.map(s => ({
    k: `${S[s] || s}`, v: C.funnel[s] || 0,
    label: `${C.funnel[s] || 0}　${s}`,   // 中文在前：这一屏给人看，schema 名是给 agent 写事件用的
  })));

  host.innerHTML = `
${hero('转化', '这周最值得转化的一件事',
  `沉淀是原料，不是资产。这一屏只回答一个问题：<b>已经花掉的时间，
   哪一块最接近变成可复用的东西或真实收益？</b>　当前状态：${state(C.state)}`)}
${C.state !== '通' ? warn(esc(C.why)) : ''}
${champ}

${sec('做了很多，但还没变成结果', esc(C.debt_note))}
${debt}

${sec('转化漏斗', `一共 ${total} 条候选在链上。旁路：暂停 ${C.funnel_side.HOLD || 0} · 淘汰 ${C.funnel_side.REJECT || 0}。
  允许「这周不晋级」—— 逼着每周造一个新 Skill 是把这套东西做坏的方式。`)}
${funnel}
${(C.funnel_moves || []).length ? `${sec('最近的状态变化')}
${table([{ t: '候选' }, { t: '从' }, { t: '到' }, { t: '什么时候' }],
  (C.funnel_moves || []).map(m => [esc(m.candidate),
    `${esc(S[m.from] || m.from)}`, `<b>${esc(S[m.to] || m.to)}</b>`,
    esc((m.at || '').slice(0, 10))]))}`
  : '<p class="hint">还没有任何状态变化 —— 漏斗强调的是「动了没有」，不是累计数量。</p>'}

${sec('价值实现', esc(C.economic.note))}
${(C.economic.paths || []).length
  ? orbit((C.economic.paths || []).map(p => ({
      k: p.label, v: p.n,
      label: `${p.n} 条　${Object.entries(p.status).map(([k, v]) => `${k} ${v}`).join(' · ')}`,
    })))
  : warn('还没有任何一条候选带经济路径。<b>这里显示的是「未测」，不是 0</b> —— '
       + '自动填 0 等于断言「没赚到」，而真实状态是「没有可核的金额入口」。')}

${(C.clamps || []).length ? `${sec('被压回去的', esc(C.clamp_note))}
${table([{ t: '候选' }, { t: '事件里声称' }, { t: '证据只支撑到' }, { t: '为什么' }],
  (C.clamps || []).map(c => [esc(c.candidate), `<b style="color:var(--warn)">${esc(c.claimed)}</b>`,
    esc(c.allowed), esc(c.why)]))}` : ''}

${sec('最近的归档变化', '只放新教训、别再犯、未了事项 —— 不放完整聊天，那不是资产。')}
${(C.closeout.lessons || []).length || (C.closeout.unresolved || []).length
  ? `${(C.closeout.lessons || []).map(l => slab(`
      <div class="ck">${esc(l.scope)}</div>
      <div class="cn" style="font-size:14px;color:var(--fg);line-height:1.7">${esc(l.lesson)}</div>
      ${l.do_not_repeat ? `<p class="hint" style="margin:8px 0 0"><b>别再犯：</b>${esc(l.do_not_repeat)}</p>` : ''}`)).join('')}
     ${(C.closeout.unresolved || []).length ? drawer(`未了事项 ${C.closeout.unresolved.length} 条`,
        table([{ t: '项目' }, { t: '还欠着什么' }],
          C.closeout.unresolved.map(u => [esc(u.project), esc(u.what)]))) : ''}`
  : '<p class="hint">还没有收到任何收尾事件（closeout）。Claude Code 与 Codex 已挂 SessionEnd/PreCompact 钩子，'
    + 'Kimi Code 与 DSH 没有钩子机制，需要手动跑一次归档。</p>'}

${sec('失败有没有变成防复发资产', esc(C.failure_bridge.note))}
${grid([
  { k: '收到的失败输入', v: String(C.failure_bridge.total), n: '条', w: 3 },
  { k: '根因已证实', v: String(C.failure_bridge.proven), n: '条', w: 3 },
  { k: '已形成守卫', v: String(C.failure_bridge.guarded), n: '条 —— 只有这些算复利', w: 3, tone: 'acc' },
])}

${drawer(`候选全表（${(C.candidates || []).length} 条）`, (C.candidates || []).length
  ? table([{ t: '这一步' }, { t: '类型' }, { t: '问题' }, { t: '证据', r: true }, { t: '最近出现' }],
      (C.candidates || []).map(c => [`${esc(S[c.stage] || c.stage)}`,
        esc(c.type), esc(c.problem), String((c.evidence || []).length), esc((c.last_seen || '').slice(0, 10))]))
  : '<p class="hint">还没有候选。</p>')}

${drawer('读到了什么、拒了什么', `
  <p class="hint">收到事件 ${C.sources.events} 条${
    Object.keys(C.sources.producers || {}).length
      ? '（来自 ' + Object.entries(C.sources.producers).map(([k, v]) => `${k} ${v}`).join('、') + '）' : ''}。
  ${(C.sources.rejected || []).length
    ? '下面这些形状不对，<b>没有静默跳过</b>：' : '没有被拒收的文件。'}</p>
  ${(C.sources.rejected || []).length
    ? table([{ t: '文件' }, { t: '为什么拒' }],
        (C.sources.rejected || []).map(r => [esc(r.file), esc(r.why)])) : ''}
  <p class="hint">${esc(C.note)}</p>`)}

${sec('做不到的', '逐条列出来。不写成「后续迭代」糊过去。')}
${drawer('摊开', table([{ t: '缺什么' }, { t: '为什么现在给不出来' }],
  (C.not_measured || []).map(x => [`<b>${esc(x.item)}</b>`, esc(x.why)])))}`;

  host.addEventListener('click', e => {
    const d = e.target.closest('[data-day]');
    if (d) go('day', d.dataset.day);
  });
  enter('.hero, .sec, .cell, .slab, .orow', host);
}
