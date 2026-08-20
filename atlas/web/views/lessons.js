import { S, esc, go } from '../app.js';
export async function render(host) {
  host.innerHTML = `<h2>沉淀</h2><div class="note"><b>状态：没做。</b><br>
    这一页要放的是「同一个坑踩了几次」——从会话里数出重复出现的失败形状。
    还没做，所以这里如实写「没做」，而不是先放个空壳假装有。</div>`;
  host.addEventListener('click', e => { if (e.target.closest('[data-go]')) go(e.target.closest('[data-go]').dataset.go); });
}
