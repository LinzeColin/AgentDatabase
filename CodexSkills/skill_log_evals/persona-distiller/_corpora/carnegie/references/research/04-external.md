# External views, criticism, and counterexamples

## Scope and assigned sources

**本道无独立 train 源**：台账里没有任何 `split == train` 的"外部批评/传记/评价"文献（`dimensions` 无 external 项）。语料 8 份全是 Carnegie 本人的著作/演讲/自传。

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。
★ 本道虽无独立源，但下列观察**全部间接取自其他道的 train 源**，逐条标出：`src-eabcbd209294`（League of Peace）、`src-5a457dfece71`（Edwin M. Stanton）、`src-4769b2a7c8a7`（The Negro in America）、`src-5512c8642a23`（Problems of To-day）、`src-f942339e1cea`（Autobiography）。

## Source-linked observations

### ① 道内无独立观察——如实说明

- 本道**没有独立的第三方批评/传记文献**（没有传记、没有当时评论家的评论文集、没有对立面著作）。
- 但**外部声音以"他转述/征用"的形式嵌在他的演讲与自传里**，可作"外部视角的间接材料"，逐条标注声口：

1. **Horace Greeley 的悼文（03 道 Stanton 演讲整段征用）**：Greeley 在《Tribune》称 "it is to Edwin M. Stanton, more than to any other individual, that these auspicious events are now due"（改述）——第三方溢美被 Carnegie 整段引用并亲口背书（"Nothing is exaggerated here"），此层可当"Carnegie 愿意采纳的外部评价"，不可当独立批评。
2. **Henry Holt 对 Stanton 的赞语（03 道）**：`loyalty to the Union cause was , a passion`（OCR 在 was 后多一逗号，照录；详见 03 道）——同为"他引用的他人评价"。
3. **Rev. Lyman Abbott 的评价（03 道 Negro 结尾）**：`never in the history of man has a race made such educational and material progress in forty years as the American negro`（照录见 03 道）——Carnegie 用第三方之口背书自己的乐观判断。
4. **《Problems of To-day》里"社会主义者"的声音（01 道）**：他反复引用 Snowden 的"社会主义者预算"（`the "Socialist's Budget," as presented by Mr. Snowden`，改述）并正面回应——**对手的纲领被他转述后逐条回应**，这是"外部批评如何进入他论证"的罕见样本。
5. **自传里"外界传言"的反驳（06 道）**：他驳斥欧洲上层流传的"格兰特靠任命中饱私囊"（"the impression was widespread among the highest officials there that there was something in the charge that General Grant had benefited pecuniarily by appointments"，改述）——展示他对"外部丑闻叙事"的态度：以自己的一手见闻反驳。

（第 1 条 Greeley、第 2 条 Holt、第 3 条 Abbott 的引文细节见 03 道；Holt 原句在语料中作 "loyalty to the Union cause was , a passion"（OCR 多一逗号），本道只转述不逐字引。）

⇒ 结论：本道只能提供"**被 Carnegie 征用的外部声音**"，且全部经由他的手转述/筛选；**没有任何独立于他的批评视角**（他从未在自己的 train 语料里全文转录攻击自己的文章）。

## Candidate Claims

- 本道**无独立候选断言**（无独立 train 源）。
- 可移交跨道的观察：①"他如何回应社会主义者预算"（01 道已承）；②"他如何征用第三方赞美/评价"（03 道已承）；③"他如何反驳外界传言"（06 道已承）——本道只提供"外部声音存在"的清单，不重复计。

## Contradictions and alternative explanations

- **"征用的赞美"≠"独立评价"**：Greeley/Abbott/Holt 的评价都是**他挑出来、由他确认"毫不夸张"**才进入文本的——这是"自选的外部背书"，不是第三方自发批评。下游引用时不得把它当成"史学界/评论界的独立判断"。
- **"转述对手再驳"的筛选性**：《Problems》转述 Snowden 预算后说"无一不使我赞同"（改述）——他转述对手时**只选自己认可的部分**，不呈现对手对其本人的攻击；因此语料里的"社会主义声音"是筛选过的。
- 若下游需要真正的"反 Carnegie 批评"（如当时对 Homestead 的舆论谴责、对《财富的福音》的批评），**本库 train 语料没有**——那是外部史实，须另案取证，不能用语料背书。

## Unknowns and source gaps

- **语料无任何完整的外部批评文本**：没有传记（自传外的他人传记）、没有当时报刊的批评文章合集、没有政敌（如对《财富的福音》持异议的教士/工会）的回应文本。
- **Homestead 罢工的外部舆论**只在自传里以"他/合伙人的辩护"出现（Phipps 信、他对工会"勒索"的指控，改述），**没有当时的报纸社论或工会一方文本**。
- 若下游需要"外部视角"场景（如"当时别人怎么看他"），须另补 PD 史料；本道现状下只能给"被他征用的外部声音"清单。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- 本道**不产 claims**（无独立源）。
- 向合成阶段移交两个"声口纪律"：①凡语料里的第三方声音（Greeley/Abbott/Holt/Snowden/传言）都必须标"由 Carnegie 转述/征用"；②凡需要"独立外部批评"的用例，本模型**没有一手依据**，须在 boundaries.md 写明"外部批评材料缺失"。

## 这一道给下游的东西

- 明确的**道空声明**：external 无 train 源。
- "被征用的外部声音"清单（Greeley/Abbott/Holt/Snowden/格兰特传言）——只在"他怎样使用外部声音"这个维度上有用，不能当独立批评证据。

## 未做完 / 未核

- 本道**全部未做**（无源可做），非"未完成"而是"不适用"。
- 未核：上述"被征用声音"是否完整（我按 01/03/06 道阅读印象列出，未逐字回溯确认没有遗漏更长的外部引文）。
