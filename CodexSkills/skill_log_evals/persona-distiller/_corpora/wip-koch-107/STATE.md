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

---

# 判定 · 2026-08-03：分母不挑子集，如实记 0.4583

研究门实测：**`primary_ratio 0.4583`**（deep 门 0.65），另有
`authorship-unproven` 46、`source-unclaimed` 55、`attribution-basis` 2、`lane-completion` 1
——后四类是尚未写 `attribution_basis` 与六路正文，属正常进度，不是缺陷。

## 判定

**不采纳 CORE 81 份子集。** 全量 121 份留在账本里，比例就记 0.4583。

## 理由（三条，第三条是本轮真正的发现）

**一、时点不对。** 子集方案是在**看到 45.5% 之后**提出的。
Pasteur #106 那次我拒绝了「看到分数再改 profile」，理由是「定在测量之前的东西，测量之后不许动」。
策展与 profile 确实不是一回事，**但「看到数再挑」这个动作的形状是一样的**。
既然形状一样，就按同一条处理——**不是因为它一定错，是因为我此刻分不清它错不错。**

**二、挑掉的正是最该留的。** 那 66 份二手里的大头是对手方原文
（Pettenkofer 9、Cohn 7、Virchow 4、Hueppe 4、Flügge 4、Behring 4、期刊卷 11）。
而 `contrast` 是前四人合并里最差的一组（**−0.1281**），
Pasteur #106 第 1 轮的 `contrast −0.1500` 正是因为我把对手的立场挂错了书。
**为过比例门去砍对手方语料，等于用一个已知会失分的方式去换一个数字。**

**三、★ 这里有一条真实的判据冲突，本轮第一次撞上：**

> **「对手立场必须指到原文」（Harvey #103 拒发后立的纪律）
> 与 `min_primary_ratio`（比例门）直接冲突。**
>
> 前者要求把对手方收全——收得越全，分母越大、比例越低；
> 后者要求一手占比高——满足它的最省力办法就是**少收对手方**。
>
> 本人物是这条冲突第一次被量出来：**一手绝对量 55 份（deep 锚值约 30，超一倍），
> 而比例 0.4583 不过门。** 两条纪律都遵守的结果是**门不过**。

## 这条冲突该怎么解，我没有答案，也不在这里替它做主

可能的方向（**均未验证，不许当结论用**）：
- 比例门改为「一手绝对量 + 一手占比」双判据，任一满足即可？
  ——那等于给比例门开了一个后门，与 v0.0.0.24 那次整批免检同型，**危险**。
- 对手方语料单独计一类，不进比例分母？
  ——那需要先定义「对手方」，而定义权在我手上，**又是一个可以被我自己滥用的旋钮**。
- 或者比例门本来就该这样：**收全对手方的人物，本来就该走 standard 而不是 deep？**
  ——但 profile 定在测量之前，事后改档已被 Pasteur 那次判为不许。

**判定是：这个问题交由用户裁定，我不自行开口子。**
在有裁定之前，本人物按实测记账，继续把其余各门做完——
**看看除了比例之外还有没有别的问题，那才是有用的信息。**
