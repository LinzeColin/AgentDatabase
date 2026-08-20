import { S, esc } from '../app.js';

export async function render(host) {
  const m = S.atlas.meta;
  const rows = Object.entries(m.method).map(([k, v]) => `<tr><td style="width:120px"><b>${esc(k)}</b></td><td>${esc(v)}</td></tr>`).join('');
  host.innerHTML = `
    <h2>口径</h2>
    <p class="sub">每个数字是怎么来的。看不懂的地方就是我没写清楚，不是你的问题。</p>

    <div class="note"><b>四个状态词</b>：通 / 断了 / 没做 / 不确定。<br>
      算不出来的地方写「不确定」，不写「没问题」。<b>颜色只是辅助</b>，每个状态都带字。</div>

    <h2>数据从哪来</h2>
    <div class="panel"><table><thead><tr><th>来源</th><th class="num">会话</th></tr></thead><tbody>
      ${Object.entries(m.sources).sort((a, b) => b[1] - a[1])
        .map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${v}</td></tr>`).join('')}
    </tbody></table></div>

    <h2>查过但没有对话内容的</h2>
    <p class="sub">这些占着磁盘但入不了库。列出来是为了下次不用再挖一遍。</p>
    <div class="panel"><table><thead><tr><th>名字</th><th>位置</th><th class="num">体积</th><th>为什么不入库</th></tr></thead><tbody>
      ${Object.entries(m.skipped_sources).map(([k, v]) => `<tr><td>${esc(k)}</td>
        <td class="muted" style="font-size:12px">${esc(v.path)}</td>
        <td class="num">${v.size_mb ? v.size_mb + ' MB' : '—'}</td>
        <td class="muted">${esc(v.why)}</td></tr>`).join('')}
    </tbody></table></div>

    <h2>被剔掉的那部分</h2>
    <p class="sub">被丢掉的东西不参与任何总量校验，所以总量永远显得是对的。这里把丢掉的摆出来。</p>
    <div class="panel"><table><thead><tr><th>重复投喂的提示词</th><th class="num">场次</th></tr></thead><tbody>
      ${m.auto_batches.map(b => `<tr><td style="max-width:520px;overflow:hidden;text-overflow:ellipsis">${esc(b.prompt)}</td>
        <td class="num">${b.n}</td></tr>`).join('')}
    </tbody></table></div>
    <div class="panel"><table><thead><tr><th>agent 密集扇出</th></tr></thead><tbody>
      ${m.fanout_hours.map(f => `<tr><td>${esc(f.when)}</td></tr>`).join('') || '<tr><td class="muted">无</td></tr>'}
    </tbody></table></div>

    <h2>算法</h2>
    <div class="panel"><table><tbody>${rows}</tbody></table></div>

    <h2>主题归并</h2>
    <div class="panel"><table><tbody>${Object.entries(S.atlas.ladder).map(([k, v]) =>
      `<tr><td style="width:70px"><b>${esc(k)}</b></td><td>${v.map(t => `<span class="chip">${esc(t)}</span>`).join('')}</td></tr>`).join('')}
    </tbody></table></div>

    <h2>权重最高的关键词</h2>
    <p class="sub">越少见的词权重越高。出现在半数以上会话里的词权重直接归零 —— 否则「方案」「数据」这种到处都是的词会决定一切。</p>
    <div class="panel">${Object.entries(S.atlas.keyword_weights).slice(0, 40)
      .map(([k, v]) => `<span class="chip" title="权重 ${v}">${esc(k)}</span>`).join('')}</div>`;
}
