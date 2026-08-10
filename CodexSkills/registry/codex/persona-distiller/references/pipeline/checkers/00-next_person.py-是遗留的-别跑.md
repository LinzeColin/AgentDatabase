# ★★★★ `checkers/next_person.py` 是 **2026-08-10 的遗留副本，别跑它**

## 活的那份在哪

**`references/pipeline/next_person.py`**（上一级目录，11,075 字节）——
`HANDOFF.md` §3 让接手方跑的就是它，今天（2026-08-11）改的也是它。

本目录这份 **37,141 字节**，docstring 与活的那份**逐字相同**，但**多 3 个顶层定义**，
是 8-10 那一版（`git log`：`a5b20601` vs 活份的 `b02bc46b`，晚一天）。

## ★★ 它不是「跑不起来」，是**跑出错的结果还照常给结论**

```
WARN: team-index.json not found at .../persona-distiller/persona-distiller-group/team-index.json
{
 "名册已入库人数": 0,        ← 真值 102
 "队列中已入库的": 19,
```

**路径少了一级**（`persona-distiller/persona-distiller-group/`），找不到名册，
**「名册已入库人数」记 0**，只在 stderr 上 `WARN` 一句，然后**照常输出 JSON**。

★ 这正是 HANDOFF 里记着的那次事故的坏法：
「`registry_products` 记成 0（真值 101），**20 个已入库的人被当成没做**，NEXT 指向了错的人」。
活的那份已经修好（从 `__file__` 推仓内路径，并打印「★ 实际用的路径」）。

## 为什么不删

- **仓内引用它的地方：0 处**（已 grep 全仓 `.py`/`.md`/`.json`）；
- 但**删文件不可逆**，而它可能是某个未纳入检索的流程的一环；
- 放一张字条比删掉更稳妥——**任何人打开这个目录都会先看见它**。

★ 若确认无用，删除是安全的（0 引用）；那是清理决定，不是 bug 修复。
