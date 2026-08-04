# 我裁定「按作品计数」——**而流水线只会数文件**，并且会**吞掉第二个作品的道**

日期：2026-08-04　撞出人物：#125 Gregor Mendel　方法：临时工作区端到端实跑

---

## 一、我做了一个实现不了的裁定

Mendel 那 9 篇气象论文逐年独立投稿、各有署名行与「Vorgelegt in der Sitzung vom …」日期，
在原刊目次里是 9 个条目。**我据此裁定「按作品拆分计数」**，理由与门无关，那个理由**仍然成立**。

但它在流水线里**表示不出来**。

## 二、实跑（不是读代码，是真跑）

同一个文件，用两条不同元数据 `ingest` 两次：

```
第 1 次（--dimension writings）    退出码 0   status=['normalized']
第 2 次（--dimension conversations）退出码 0   status=['duplicate-skipped']

→ 账本 **1** 条：src-35b7952d115d　dimensions=['writings']
```

机理在 `ingest.py`：

```python
checksum  = sha256_bytes(raw_data)
source_id = f'src-{checksum[:12]}'      # ★ id 由**内容**决定
prior = by_checksum.get(checksum)
if prior:
    results.append({... 'status': 'duplicate-skipped'}); continue
```

**`source_id` 由内容决定，逐位相同的第二次直接跳过。**

## 三、两个后果，第二个更要紧

### ① 门数的是文件，不是作品

Mendel 的 27 个作品分布在约 21 个 carrier 里（确切映射待抓源方给出）。
**门看到的是 carrier 数。** 所以：

- 我裁定的 27 份**进不了账本**
- 若强行按作品写 27 行，**其中约 6 行会被静默跳过**，
  而 `raw/_ids.txt` 仍写着 27 —— **正是今天 `check_staged_but_not_ingested` 抓的那一类账物不符**

### ② ★★ **第二个作品的「道」被吞掉**

上面那次实跑里，第二次是 `--dimension conversations`，
而账本里那条只有 `dimensions=['writings']`。

**两个作品若分属不同的道、又共用一个 carrier，第二条道就没了。**
而 `min_lanes` 是硬门（deep/standard 都要 6 道）。

**这是一个会让人物无声掉道的缺陷**，不只是计数口径问题。
Mendel 这次侥幸没踩到（他的 conversations 两件各自独占 carrier），
**但那是运气，不是设计。**

### ★ 全库回溯：**没有人踩到过**（已实测，不是推测）

比对每个工作区的「抓源台账里出现过的道」与「工作区账本 `dimensions` 覆盖的道」：

```
barton／blackwell／fleming／nightingale   台账 6 道，账本 6 道   —
jenner／koch／lister／pasteur             台账 2–3 道，账本 6 道  —
semmelweis                               台账 2 道，账本 2 道    —
**丢道的：0 人**
```

★ 那几个「台账道数」偏小的，是**老一代台账不以可解析的方式记道**
（`FINDING_ledger-has-three-generations.md`），**不是丢道**。

**所以这条是「补上一个还没伤到人的洞」，不是「发现了既有损失」。** 两件事要分清。

## 四、我错在哪

**我在裁定计数单位时，没有先确认那个单位落得了地。**
裁定本身（按作品）在书目学上是对的；
**错在把一个「表示不出来的口径」当成了可执行的决定，还据此给抓源方派了活。**

★ 与今天另一处同形：我把档位阈值凭记忆写进 RUNBOOK（standard 道 ≥3，真值 6）。
**两次都是「先定了，再发现真源里不是这么写的」。**

## 五、这不是「改流水线」的理由（至少现在不是）

`ingest` 按内容去重是**对的**：它挡的是同一份材料重复入账把 `primary_ratio` 灌水。
**要支持「一个 carrier 多个作品」，需要的是「作品」这一层实体**，
而那是产物结构的改动，**波及所有已入库人物的账本**。

**现在只记账，不动。** 待裁定项已有 11 条，这是第 12 条候选，
但我不自行开这个口子——**它会改变所有既有人物的份数口径。**

## 六、Mendel 眼下按文件口径是什么

待抓源方给出 carrier 映射后才有确数。**在那之前我不报数**
（今天已经因为「核了 A 套到 B」错过一次，见 `eval-artifacts-have-five-schemas`）。

可以先说的是：**quick（8 份 / 3 道 / 占比 0.40）在两种口径下都富余**，
**standard 的份数门 24 在文件口径下更难过**——作品 27 → 文件约 21。

参见 `check_staged_but_not_ingested.py`（账物不符那一类）、
`FINDING_ratio-gate-can-be-set-upstream-without-a-trace.md`（分母的另一半问题）。
