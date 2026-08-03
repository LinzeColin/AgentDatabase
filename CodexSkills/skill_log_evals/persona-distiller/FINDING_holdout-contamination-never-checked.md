# 一件自称硬门的判据，从来没有跑过

日期：2026-08-04　发现方式：全量健康核查里的一行 `diff -rq`

---

## 一、怎么发现的

做完一天的提交后跑一次全量健康核查：

```
$ diff -rq scripts references/pipeline/checkers
Only in references/pipeline/checkers: check_anchor_coherence.py
Only in references/pipeline/checkers: check_holdout_overlap.py
Only in references/pipeline/checkers: check_material_split.py
Only in references/pipeline/checkers: check_verbatim_quotes.py

$ python3 scripts/check_contract_drift.py
✓ 无合同漂移
```

**两个结果同时为真。** 看合同漂移门的代码：

```python
for mirror in mirrors:
    twin = root / "scripts" / mirror.name
    if not twin.is_file():
        continue          # ← 只存在于一侧的文件，静默跳过
```

而这一段注释的上面就写着：

> 这是第二十二种的又一形态：**同一件东西两份拷贝，改一处另一处继续活着。**

**它没写第三种**：「只存在一处」，而**把门的恰好是没有它的那一处**。

## 二、四件判据，四件自测全绿

| 判据 | 自测 | 全仓被代码调用 |
|---|---|---|
| `check_anchor_coherence` | ✓ | **0 处** |
| **`check_holdout_overlap`** | ✓ | **0 处**——**它自己的文件头写着「硬门」** |
| `check_material_split` | ✓ | **0 处** |
| `check_verbatim_quotes` | ✓ | **0 处** |

这四个名字**只出现在注释与文档字符串里**（`quality_check.py` 的散文、
`check_authorship.py` 的「它与我的分工」说明、一条测试的注释）。
**没有一处 `import` 或 `spec_from_file_location`。**

反方向也有两件缺件：`check_contract_drift`（它自己）与
`check_distillation_freshness` 只在 `scripts/` 里，**装出去的包会少这两件**。

## 三、★ 它为什么连「跑不通」都没被发现

`check_holdout_overlap` 原本这样定位正文：

```python
def locate(r):
    return files.get((r.get("locator") or "").rsplit("/", 1)[-1])
```

按 `locator` 的最后一段当文件名。**而本流水线的 locator 是「篇名｜出处｜URL」**，
`rsplit("/")[-1]` 切出来是 URL 的尾巴。

Nightingale #112 实测：**117 条一条也定位不到**，判据只会打印
「找不到正文的源 117 条 —— 无法判定，**不算通过**」。

**它连自己跑不通都说得很清楚——只是没有人在跑它。**

改用 `local_path`（与其余判据一致）之后立刻出结果。

## 四、接进门第一次跑，就在五个人身上抓到硬失败

**全量扫描已跑完**（10 个可扫工作区；Galen / Harvey / Vesalius / Livermore
是旧布局或语料在 D 档，跑不了）：

| 工作区 | 硬失败 | |
|---|---:|---|
| **Nightingale #112** | **3** | 另 2 处待人工核 |
| **Jenner #104** | **1** | |
| **Koch #107** | **1** | |
| **Osler #110** | **1** | |
| **Semmelweis #105** | **1** | |
| Fleming #111 | 0 | ✓ |
| Lister #108 | 0 | ✓ |
| Pasteur #106 | 0 | ✓ |
| Godin | 0 | ✓ |
| Steinhardt #98 | 0 | 1 处待人工核 |

**十个人里五个有 holdout 污染。**

Nightingale 那三处最重：

```
✗ notes-on-nursing-1906.txt　与 train 里的 1908 版覆盖 **53.1%**
✗ notes-on-nursing-1888.txt　与 1883 版覆盖 **32.6%**
✗ surgical-operations-stats-1863.txt
```

### Nightingale 那三处的成因是同一个

**我把《Notes on Nursing》同一本书的不同版次，一半放 train、一半放 holdout。**
它们本来就是同一段文字的不同印次——覆盖率高是必然的。

**后果**：`known` 套组那两道题的保留集**不测泛化**，
产物拿高分可能只是「它见过这段文字」。

## 五、这件事的分量

- **不改变 Nightingale 的拒发结论**：boundary 与 fact 都没过，与 holdout 无关。
- **但它改变了五个人的 `known` 数字的可信度**：
  Nightingale、Jenner、Koch、Osler、Semmelweis。
  **十个里五个**——这不是个别失误，是**没有判据在管这件事**的必然结果。
- **已入库 100 人的 holdout 从未按这条扫过。** 判据接进门时设为**只报不拦**，
  否则会追溯性地拦住已发布的东西。

## 六、已做与未做

**已做**：
- 合同漂移门改成**两个方向都报**「只存在于一侧」，并配自测。
- 四件复制进 `scripts/`，两件补进镜像；两侧现在逐字节一致。
- `check_holdout_overlap` 改用 `local_path` 定位，接进 `synthesis` / `release`。
- 检查器 33 → **37**。

**未做**：
- **没有回头改任何人的 holdout**——那等于重划已判完分的评测集。
  正确做法是在**重蒸**（任务 #29）时重划，规则是：
  **同一著作的不同版次不能拆到 train / holdout 两侧。**

## 七、这条与既有记录的关系

`gate-green-but-pointed-at-wrong-artifact`（记忆）记着「判据绿了但指错了文件」
已发生八次。**这一次是第九种形态，而且是最彻底的一种**：

> **判据存在、自测全绿、文档里被反复引用——而它从来没有被任何代码调用过。**

前八种都是「跑了但没跑对」。这一种是**根本没跑**。
