# #107 Robert Koch —— 可续检查点（语料与账本已成，研究门测量中）

日期：2026-08-03　｜　蒸馏版本 `v0.0.0.37`　｜　德文写作，**有译文层**

---

## 一、已完成（全部实跑）

| 步 | 结果 |
|---|---|
| 同名门 | `resolution none / ready`；**实搜有消歧义页**，但同名者按年代／领域全可分（见 `NAMESAKE_HAZARD.md`） |
| 建工作区 | `workspaces/robert-koch`，`--profile deep --subject-origin historical --language de --time-scope 1843-1910` |
| 抓源 | **121 份 209 MB**（writings 55 / external 59 / biography 7） |
| `check_corpus_integrity` | **0 张错误页**；1 条软报（774 字节手写信，OCR 全废，已标不可用） |
| ingest | **121 成功 / 0 失败**，1 份 holdout |
| 六路 | external 58 / writings 41 / decisions 15 / expression 5 / conversations 1 / timeline 1 —— **六路齐** |

## 二、★★★ 本人物最要紧的一件：Koch–Pasteur 之争**双方语料都在本机**

抓源实取到 **Koch 批评 Pasteur 的三篇原文，都有卷页**：

| 篇 | 出处 |
|---|---|
| 《Zur Ätiologie des Milzbrandes》(1881) | GW Bd.I **S.174** |
| 《Ueber die Milzbrandimpfung. Eine Entgegnung auf den von Pasteur in Genf gehaltenen Vortrag》(1882) | GW Bd.I **S.207** |
| 《Über die Pasteurschen Milzbrandimpfungen》(DMW 1887 Nr.32) | GW Bd.I **S.271–273**——Koch 逐条质疑 Pasteur 报的 20 万只羊 1% 死亡率，并列 Kelbra／Klonie／Domäne Packisch 的德国对照数据 |

**Pasteur 一侧**：`b28124571`《La vaccination charbonneuse: réponse de M. Pasteur à un mémoire
de M. Koch》(Revue scientifique 1883-01-20)；日内瓦讲演在
`../wip-pasteur-106/raw/uvresdepasteur0006past.txt`（Œuvres t.VI p.391–411），
**且该卷编者注明确回指 Koch 那本小册子——两库互指闭环。**

> **这是本项目第一次出现「争论双方的语料都在本机」的情形。**
> Harvey #103 因编造对手立场而拒发；Pasteur #106 第 1 轮把 Pouchet 的主张挂到一本讲自发排卵的书上。
> **这一次没有借口：凡「Pasteur 主张 X」，指到页码，指不到就不写。**

另拿到 **Koch–Pettenkofer** 对质原件（BKW 1884 年卷收 1884 柏林霍乱会议逐字记录 S.478/498/509，
Koch 发言以「Koch:」引出；同卷 S.490 有 Virchow 反驳 Pettenkofer）。

## 三、必取件全部到手

- **《Gesammelte Werke》3 册全，且两套独立扫描**（Glasgow `b21463608_0001/2/3` +
  LSHTM `b21353207_*`），德文虚词率 10.3–11.0%，OCR 干净
- **1876 炭疽** —— 原刊 Cohns Beiträge Bd.II S.277 + GW Bd.I S.5
- **1882 结核（科赫法则首刊）** —— 原刊 BKW 1882 S.221 + 1884 全本 + GW Bd.I S.428/467
- **1881 纯培养法** —— 抽印 `b21303095` + 原刊 + GW Bd.I S.112

## 四、★ Fraktur OCR 报废 8 份（已识别，附德文虚词占比）

干净件 10–13%，报废件掉到 0–2.3%：

`ueberdiemilzbra00kochgoog` **0.5%**（1882 驳 Pasteur 单行本）、`b21365647` **0.1%**（1887 霍乱报告）
—— **这两份是 Koch 本人的，都已用 Gesammelte Werke 的干净版顶替**；
其余 6 份为对手方（Pettenkofer 1855、Virchow 1862、Gaffky 1899、Cohn ×2 等）。

**德文 Fraktur 的 OCR 判据（数虚词占比）本轮首次用上，应考虑落成判据。**

## 五、抓源阶段就被剔掉的（同名门在此处起了作用）

`diecholeraaufih00kochgoog` 扉页署 **Sanitätsrath Dr. A. Koch**——**不是 Robert Koch**，已删。
另删 `waswissenundknne00koch`（自然疗法论战，同名）、`micro_IA40243207_0245`（实为 1847 童话集）、
及 3 份无 Koch 内容的期刊卷。

## 六、★★ 待决：`primary_ratio` 的分母

抓源报 **一手 45.5% < deep 门 65%**，但**一手绝对量 55 份，远超「约 30 份」的锚**。
低的原因是分母：为满足「对手立场必须指到原文」这条硬约束，
二手集从预设的约 15 份涨到 66 份（Pettenkofer 9 + Cohn 7 + Virchow 4 + Hueppe 4 + Flügge 4 + Behring 4 + 期刊卷 11 …）。

抓源方提了一个 **CORE 子集（81 份，一手 67.9%）**，选它即可过门、不必删文件。

> **本轮先全量 ingest、让门自己报数，不预先优化。**
> 看到分数之后再去挑子集，与 Pasteur #106 那次「看到分数再改 profile」是同一件事——
> **那次我拒绝了，这次也不许自动就做。**
>
> 但两者有一处实质区别，必须写下来供判断：
> Pasteur 那次要动的是**尺子**（profile 定在测量之前）；
> 这次要动的是**语料的取舍**（本就是蒸馏前的策展决定）。
> **区别是否成立，须在看到门的实测数字之后、单独判定并记账，不许顺手带过。**

## 七、下一步

```bash
# 1. 读研究门实测的 primary_ratio（跑 209 MB 需 >2 分钟）
# 2. 按上面第六节判定分母口径，并把判定理由写进本文件
# 3. attribution_basis 四字段 + 55 条 P1 逐份点名
# 4. 六路正文；★ 04-external.md 必须逐条给 Koch–Pasteur 的卷页
# 5. 断言层：work-method 至少 3 条可复用（科赫法则本身就是判据，是最好的素材）
# 6. 出题：★★ 题面里每个数与每个口径先回语料核（Pasteur 用三轮换来的教训）
```
