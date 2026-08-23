# Writings and systematic works

## Scope and assigned sources

| source_id | 题名 | 编年 | raw 路径 | 本道用途 |
|---|---|---|---|---|
| src-60a849fa8c49 | *A System of Logic, Ratiocinative and Inductive* | 1884 | raw/asystemlogicrat00millgoog.txt | 逻辑体系（主源） |
| src-7c6ec4577041 | *A System of Logic, Ratiocinative and Inductive* | 1868 | raw/asystemoflogic02milluoft.txt | 同书另一扫描 |
| src-4e339d410c73 | *On Liberty* | 1863 | raw/onliberty05millgoog.txt | 论自由（主源） |
| src-836de413b6b9 | *On Liberty* | 1859 | raw/onlibertyxero00milluoft.txt | 同书另一扫描（derived_from src-4e339d410c73） |
| src-ddd3c72adeb3 | *Utilitarianism* | 1863 | raw/dli.ernet.531701.txt | 功利主义 |
| src-8278ffce1ca4 | *Principles of Political Economy* | 1865 | raw/principlesofpoli00mill_3.txt | 政治经济学原理（主源） |
| src-563778bbaee5 | *Principles of Political Economy* | 1849 | raw/principlespolit03millgoog.txt | 同书另一扫描（derived_from src-8278ffce1ca4） |
| src-a5bb209570f4 | *Auguste Comte and Positivism* | 1907 | raw/augustecomteposi00mill_0.txt | 对 Comte 的评述 |
| src-7d6633fa5e16 | *Dissertations and Discussions* | 1865 | raw/dissertationsdis00milliala.txt | 文集（Bentham/Coleridge 等） |
| src-568eb932c905 | *Essays on Some Unsettled Questions of Political Economy* | 1844 | raw/essaysonsomeunse12004gut.txt | 政治经济学方法论 |

**本道只读上列 10 份 train 源；未列出的源一律未读、未引。**

**口径说明**
- 10 份按作品归并为 **7 部**：3 组为同书另一扫描——On Liberty（1859/1863）与 Principles（1849/1865）两组中 1859/1849 份在台账标记 `derived_from` 各自的 1863/1865 主源；System of Logic 的 1868/1884 为不同版次、台账各计一行。同书另一扫描不重复逐字引用，以主源引文为准。
- 引文一律照 OCR 形态逐字照录：行尾断词连字符/软连字符（¬）按原词合并（如「pro¬ portion」→「proportion」），OCR 讹字照录不修（如「TJiirxlly」=Thirdly、「peu|ie」=people、「WHAT,」=What,），双空格折叠为单空格；每条引文后以独立来源注释标注。
- 全部引文均已逐条回原文逐字回验（grep 命中）。

## 13 条实测发现

### ① 论自由：个人对自身的主权边界（第 IV 章开场设问）

> the rightful limit to the sovereignty of the individual over himself?

<!-- src-4e339d410c73 -->

⇒ 《论自由》第四章以设问开场：对「个人对自己」的主权，正当的边界何在、社会权威从何开始。这一章正是全书伤害原则的系统化表述所在。OCR 注：本扫描该句首词印作大写「WHAT,」，照录时取句中片段以避开大小写噪声。

### ② 论自由：自由三域——言论、趣味、结社

> No society in which these liberties are not, on the whole, respected, is free, whatever may be its form of government ;

<!-- src-836de413b6b9 -->

> for any purpose not involving harm to others : the persons combining being supposed to be of full age, and not forced or deceived.

<!-- src-836de413b6b9 -->

⇒ 1859 扫描（本道另一扫描）给出了同一段的清晰文本：三类自由（思想言论、趣味/生活方式、结社）缺一即非自由社会；结社自由以「不伤及他人」为界、参与者须成年且非受骗/被迫。OCR 注：本扫描双空格密集、讹字多（「TJiirxlly」=Thirdly、「peu|ie」=people、「unqu.ali-」=unqualified），已避开重灾区逐字引用。

### ③ 功利主义：最大幸福原则的经典定义

> The creed which accepts as the foundation of morals, Utility, or the Greatest Happiness Principle, holds that actions are right in proportion as they tend to promote happiness, wrong as they tend to produce the reverse of happiness.

<!-- src-ddd3c72adeb3 -->

⇒ 第二卷卷首对功利主义信条的正式定义：以效用（最大幸福）为道德基础，行为之正误按其「促进幸福／产生不幸」的倾向度量。OCR 注：「pro¬ portion」为行尾断词，照原词合并为「proportion」。

### ④ 功利主义：幸福论——质高于量

> pleasure and freedom from pain are the only things desirable as ends ;

<!-- src-ddd3c72adeb3 -->

> It is better to be a human being dissatisfied than a pig satisfied

<!-- src-ddd3c72adeb3 -->

⇒ 快乐与免于痛苦是唯一作为「目的」而被欲求的东西（其余皆为其手段）；随后给出质的区分——「做一个不满足的人，好过做一头满足的猪」。OCR 注：后一句在「pig satisfied」后印有「;!」与乱码（「^sa Be,」），引文止于「satisfied」前。

### ⑤ 政治经济学原理：生产规律 vs 分配规律——全书最著名的二分

> The laws and conditions of the production of wealth, partake of the character of physical truths. There is nothing optional, or arbitrary in them.

<!-- src-8278ffce1ca4 -->

> It is not so with the Distribution of Wealth. That is a matter of human institution solely. The things once there, mankind, individually or collectively, can do with them as they like.

<!-- src-8278ffce1ca4 -->

⇒ 第二卷开篇（"OF PROPERTY" 章）的核心区分：**生产规律**具物理真理性质、无选择余地；**分配规律**则是「人类制度」的纯粹产物，社会可以对既得财富任意处置——这是他对分配可改革性（乃至后来同情式讨论社会主义）的支点。

### ⑥ 政治经济学原理：落后国家为何少见大规模固定资本投入

> It is not in poor or backward countries that great and costly improvements in production are made.

<!-- src-8278ffce1ca4 -->

⇒ 论资本积累的条件：把资本沉入土地作长期回报、引入昂贵机械，需要产权相当安全、产业活力相当活跃、以及较高的「有效积累欲」——三者在落后国家罕见。这是他用「制度/激励」而非单纯「贫穷」解释发展差异的一例。

### ⑦ 逻辑体系：归纳逻辑的职责

> The business of Inductive Logic is to provide rules and models (such as the Syllogism and its rules are for ratiocination) to which if inductive arguments conform, those arguments are conclusive, and not otherwise.

<!-- src-60a849fa8c49 -->

⇒ 归纳也像三段论那样需要「规则与模型」：只要论证符合这些规则即结论成立、否则不成立——这正是他的归纳四法（契合法/差异法等）的定位。

### ⑧ 逻辑体系：经验主义认识论——关系观念亦来自经验

> And in truth it never does exist, except as the result of experience.

<!-- src-60a849fa8c49 -->

⇒ 讨论「人必有一死」这类命题：『人』与『有死』两观念之间的这种关系「从不独立存在，除非作为经验的结果」——直接反驳先天论者的一处表述。

### ⑨ Auguste Comte：对其「第二事业」的评述

> came forth transfigured as the High Priest of the Religion of Humanity.

<!-- src-a5bb209570f4 -->

⇒ 他把 Comte 的后期（1851 后的 Politique Positive 阶段）概括为「脱胎换骨为人道教的大祭司」——本卷整体基调：早期实证哲学有价值，后期制度化的人道教应予批评。

### ⑩ Auguste Comte：对知识权威设定的批评

> He does not imagine that he actually possesses all knowledge, but only that he is an infallible judge what knowledge is worth possessing.

<!-- src-a5bb209570f4 -->

⇒ 批评 Comte 不自认拥有一切知识，却自封「什么知识值得拥有」的绝对裁判——这是他对「精神权威制度化」的核心反对。

### ⑪ Dissertations：Bentham 与 Coleridge——英国两大「种子心智」

> These men are Jeremy Bentham and Samuel Taylor Coleridge,— the two great seminal minds of England in their age.

<!-- src-7d6633fa5e16 -->

> Bentham was a Progressive philosopher ; Coleridge, a Conservative one.

<!-- src-7d6633fa5e16 -->

⇒ 《Bentham》开篇（原刊 Westminster Review 1838）：把 Bentham 与 Coleridge 并列为「英国思想的两大种子心智」，几乎所有受过教育者都先向他们之一学思考；并划分类别——Bentham 属进步派、Coleridge 属保守派。OCR 注：「Cole- ridge」为行尾断词，合并为「Coleridge」。

### ⑫ Unsettled Questions：Ricardo 使政治经济学获得科学性格

> Of the truths with which political economy has been enriched by Mr. Ricardo, none has contributed more to give to that branch of knowledge the comparatively precise and scientific character which it at present bears, than the more accurate analysis which he performed of the nature of the advantage which nations derive from a mutual interchange of their productions.

<!-- src-568eb932c905 -->

⇒ 第一卷开篇（论国家间交换法则）对 Ricardo 的评价：在 Ricardo 对政治经济学的诸贡献中，没有比他对「国家互通有无之利」的精确分析更能赋予该学科当下这种「相对精确与科学的性格」。

### ⑬ Unsettled Questions：贸易利得的定义

> He shewed, that the advantage of an interchange of commodities between nations consists simply and solely in this, that it enables each to obtain, with a given amount of labour and capital, a greater quantity of all commodities taken together.

<!-- src-568eb932c905 -->

⇒ 贸易利得被定义为：用等量劳动与资本换取更大的商品总量；随后即推导出比较成本原理。OCR 注：本扫描该段落前后印有排印强调标记（`_absolute_`/`_comparative_`），本道避开了逐字带标记的句子。

## 这一道给下游的东西

- **可直接引用的立场锚点（均出自上列 7 部作品原文）**：
  - 伤害原则 / 个人主权边界（On Liberty，src-4e339d410c73 / src-836de413b6b9）；
  - 最大幸福原则定义 + 快乐质的区分（Utilitarianism，src-ddd3c72adeb3）；
  - 生产规律（物理真理）与分配规律（人类制度）之分（Principles，src-8278ffce1ca4）；
  - 归纳需要形式规则（四法）（System of Logic，src-60a849fa8c49）；
  - 比较成本 / 贸易利得（Unsettled Questions，src-568eb932c905）；
  - 对 Comte：早期哲学可取、后期人道教当批（Auguste Comte，src-a5bb209570f4）；
  - Bentham 进步 / Coleridge 保守 的划类（Dissertations，src-7d6633fa5e16）。
- **思想指纹**：把「经验是一切关系观念的来源」当作认识论底色；把「分配可由社会制度重排」当作改革空间；对体系化的思想权威（Comte 后期）保持清醒的批评。
- **表达指纹**：论证多为「先给出最大幸福/效用这类标准，再逐层检验其推论」；对对手先复述其论点再拆标准（与 conversations 道对 Thornton 的做法同源）。

## 未做完 / 未核

- **台账缺口（需上游处理）**：`raw/considerationson05669gut.txt`（*Considerations on Representative Government*，P1 一手）在 raw/ 目录存在，但**未出现在 evidence/source-ledger.jsonl**（台账现 16 行，缺此 1 行）——本道未引该源；需台账补录（含其 train 或预留归属与 source_id）后再评估是否纳入 writings 道。
- 同书另一扫描未逐字重引：System of Logic 1868 版（src-7c6ec4577041）未精读，只以 1884 版引文为准；On Liberty 1859 版（src-836de413b6b9）与 Principles 1849 版（src-563778bbaee5）仅引与主源一致的片段。
- 各源 OCR 讹字见各发现注（「¬」软连字符、大写噪声、乱码段均已避开或加注）。
