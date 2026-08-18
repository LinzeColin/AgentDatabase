# ★★★ 订正两处 + 真机制：`marginal_select` **重罚同族**，把软件题选成「每族各一人」（2026-08-18）

## 先撤回我自己写错的两句（都已发表）

| 我写过 | 实测 |
|---|---|
| 「本测试调的是 **A 层旧路由** `route_team.py`」 | **错的。** `scripts/route_team.py` 全文 **6 行**：`from route_team_moe import main` —— **两者是同一个路由**。合同里那句「A 保持旧类别…只用于兼容」说的是**策略层 A/B/C**，不是这个文件名。 |
| 「MoE 把 Willison 排 **第 9**、size=14 ⇒ **会入选**」 | **也是错的。** 那是我按 `base_score` 排的名次，而**选人不是取前 N** —— 中间隔着 `marginal_select()`。 |

**两次都是同一个毛病：拿一个中间量（base_score 排名）去推终局（谁被选中），中间那一层我没看。**
[[measure-a-change-at-the-layer-it-acts-on]]｜[[stopping-at-the-first-answer-that-holds-together]]

★ 我是怎么发现的：正要给「两个路由的差」建判据，先去读 `route_team.py --help` ——
  发现它的 usage 与 `route_team_moe.py` **一模一样**，觉得不对，`wc -l` 得 **6 行**。
  **建判据之前先读被判对象**，这一步救了一件错判据。

## 真机制：`route_team_moe.marginal_select()`（第 290 行）

同一道英文软件工程评审题，size=14，产物自报的 `base_score` vs `marginal_score`：

| 名次 | 人 | 族 | base | **marginal** |
|---:|---|---|---:|---:|
| 1 | Kent Beck | 软件开发师 | 0.3616 | **0.3548** |
| 2 | Harry Bhadeshia | 材料建工师 | 0.3076 | 0.2738 |
| 3 | Martin Fischer | 建造采购师 | 0.2428 | 0.2645 |
| 4 | Nancy Leveson | 财务合规师 | 0.2875 | 0.2584 |
| **5** | **Joel Salatin** | **农林牧渔师** | 0.2299 | **0.2470** |
| 6 | David Packard | 创业经营师 | 0.2183 | 0.2236 |
| 7 | Ray Dalio | 投资资本师 | 0.1678 | 0.2012 |
| 8 | Theodore V. Wells Jr. | 政治法律师 | 0.1781 | 0.1997 |
| 9 | John Maeda | 艺术设计师 | 0.1717 | 0.1915 |
| **10** | **Chip Huyen** | **软件开发师** | **0.3549** ← 全场第 2 高 | **0.1872** |
| 12 | Shreya Shankar | 软件开发师 | 0.3461 | 0.1519 |

**第 2–9 名是每族各一人；第 10 名才回到第二个软件开发师。**

⇒ **一道软件工程评审题，14 人里只有 3 个软件开发师，第 5 位是农场主。**
  Simon Willison（软件开发师，base 排第 9）进不来 —— **软件席位早被占满**。

★ **这不是「路由坏了」**：多样性选择本身是正当设计（避免一队人重复覆盖同一片）。
  问题是**权重**：`Chip Huyen` base 0.3549 → marginal 0.1872（**掉 47%**），
  而 `Joel Salatin` base 0.2299 → marginal 0.2470（**涨 7%**，因为他是唯一的农林牧渔师）。
  **多样性压过了对口度。**

## 这条与 #129 的关系：**两件事，不是一件**

回头核 Mulcahy 那道（size=8）：选出的 8 人里**创业经营师只有 1 个**（郭士纳），
而投资资本师有 2 个（Fisher 第 2、李录 第 8 —— 李录 base 0.3520 被压到 marginal 0.2173，掉到最后）。
⇒ Mulcahy 作为**第二个创业经营师**同样要吃同族惩罚。

**但对她而言那是第二重，不是第一重**：她 `base_score` 就排 **38 / 70**
（`task_similarity` 0.0000，卡片纯英文对中文题面），**在这个位次上多样性权重再怎么调也进不了 8 人**。
⇒ **#129 那条（卡片语言）对 Mulcahy 仍然成立且是主因**；本条是**另一件**，主要打软件那道。
★ 我先前写「差的只有卡片语言」——**对 base_score 的比较成立，对「谁被选中」不完整**。此处补齐。

## 要 Owner 定的（本轮一个字不改）

- **调多样性权重**（让对口度压过同族惩罚）⇒ 改路由，撞「门、席位一概不动」。
- **改测试断言**（承认软件题只坐得下 3 个软件人）⇒ 等于宣布现状即预期。
- **两条都不做** ⇒ 这两道测试继续红，但**失败信息现在会自己说清真因**（已落地）。

## 可复算

```bash
cd CodexSkills/registry/codex/persona-distiller-group
wc -l scripts/route_team.py            # **6** 行
head -4 scripts/route_team.py          # from route_team_moe import main
grep -n "def marginal_select" scripts/route_team_moe.py   # 第 290 行

T='Design a software engineering review covering TDD, refactoring, evolutionary architecture, Python SQLite CLI, coding-agent prompt injection, AI/ML evaluation monitoring feedback loops, distributed systems API type design and technical teaching'
python3 scripts/route_team.py --task "$T" --size 14 | python3 -c "
import json,sys
for i,r in enumerate([x for x in json.load(sys.stdin)['selected_roles'] if x['role_type']=='persona-solver'],1):
    print(i, r['canonical_name'], r['registration_category'], r['base_score'], r['marginal_score'])"
```

[[measure-a-change-at-the-layer-it-acts-on]]｜[[stopping-at-the-first-answer-that-holds-together]]｜[[two-errors-stacked-so-either-stop-flips-the-verdict]]｜[[a-verdict-whose-scope-exceeds-its-inputs]]
