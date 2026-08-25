# Timeline, stages, and drift

## Scope and assigned sources

**本道分到 1 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-f652ed07aa15` | 1911 | P1 | The Abraham Lincoln chair : [advertising brochure]（John Wanamaker, New York，金婚纪念宣传册） |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。本道 train 源仅此一份宣传册；更长的商店年表在 writings 道 `src-eabfd2f57aac`（《History of the founding of Philadelphia》1910 的 Chronology 段），本道作为**间接提取**引用并标注其 source_id。

## Source-linked observations

### ① 宣传册给的时间锚：林肯就任总统之年 = Wanamaker 生意诞生之年（1861/1911）

`src-f652ed07aa15` 是 1911 年"金婚（Golden Jubilee）"纪念宣传册——**宣传册声口**，把林肯就任与商店创立绑在同一年，再以 1911 年五十周年为卖点：

> Fifty years ago Abraham Lincoln became President of these United States. Fifty years ago the John Wanamaker Business was born.
<!-- src-f652ed07aa15 -->

> To commemorate the Golden Jubilee we have reproduced the Lincoln Chair and three companion chairs to make a complete set; and our manufacturer, in honor of the occasion, has waived his usual profit which enables us to offer these chairs of historical interest for about the usual wholesale price.
<!-- src-f652ed07aa15 -->

（据此，本库对 Wanamaker 商店创立年的时间锚是 **1861**，与人物背景"1861 合开男装店"吻合；宣传册末页还印有售价表，如边椅/摇椅 $10-16.50 分档，OCR 将 `$10.00` 扫作 `$1  0.00`，改述不逐字引。）

- **林肯椅的物证时间线**（宣传册叙述，二手）：椅为林肯夫妇 1844-1861 年 Springfield 家中用物——`The chair, the picture of which appears on the first page of this folder, was used by Mr. and Mrs. Lincoln in their home at Springfield, 111., from 1844 to 1861`（`111.`=Ill. 的 OCR 讹形照录）；1883 年 R. L. Oldroyd 迁入林肯故居开设纪念收藏、Coleman 赠椅；后移入华盛顿 516 Tenth Street（Peterson 宅），林肯遇刺后被抬入该宅：

> It was in this house that Lincoln was carried after being shot by the assassin John Wilkes Booth in a box at Ford's Theatre.
<!-- src-f652ed07aa15 -->

- **纪念=商店宣传的合一**（宣传册收束句）：

> The Abraham Lincoln Chairs and The Lincoln Chair sets will recall, many generations hence, tender memories of not only Abraham Lincoln, the beloved President, for whose memory and fame they were inspired, but also of The John Wanamaker Golden Jubilee, which celebration made them possible.
<!-- src-f652ed07aa15 -->

⇒ 声口/论点：**商业宣传声口**——历史纪念是营销素材，林肯椅是"服务公众"叙事的物质道具；时间线上的"1861 年诞生"由商店自己定义。

### ② 间接提取：商店年表（writings 道 `src-eabfd2f57aac` 1910 Chronology 段）

- 1862 年宣布缩短工时（`1862 — The Wanamaker Store declared for shorter hours.`）；1876-03-12 现店开业（`1876, March 12 — The present Wanamaker Store opened.`）；1878 年成为世界第一家电灯照明的商店（`December 26 — The Wanamaker Store the first in the world to be lit by electricity.`，年份 1878 在上一行条目）；1880 年引入现金输送管（`1880 — Cash carriers introduced in the Wanamaker Store — in this a pioneer.`）；1886-07-04 开始周六半休（`1886, July 4 — The Store starts the Saturday half-holiday.`）；1899-04-15 进军钢琴业（`April 15 — The Wanamaker Store enters the piano trade, and revolutionizes it.`，年份 1899 在上一行条目）；1904-07-11 与 1909-02-08 由 John Wanamaker 亲手立下新楼首根钢柱（`1904, July 11 — First steel pillar of the new Store planted by Mr. John Wanamaker.`；`1909, February 8 — First pillar of the south wing of the new store planted by John Wanamaker.`）——逐条照录自 src-eabfd2f57aac，改述拼合。

### ③ 间接提取：经营阶段的自述（expression 道）

- **1876 年的创业期记忆**（1914 年对通道经理讲话，src-4e53b2952a15）：`I remember the first weeks of the business in 1876, when we had nothing like the car-traveling facilities that we have at the present`（改述衔接；同段回忆早期"自带午餐、商店提供炉灶"）。
- **商店学校约始于 1897**（src-161fd427387d，1909 年文称"已有 12 年"）：`an educational system that, for as many as twelve years, has been in active operation in a very quiet way under the title of "The John Wanamaker Commercial Institute"`（改述）。
- **"四十年旧制度→新制度"的行业阶段论**（src-342fd9325225，1900）：`As late as forty years ago, or before the war, the transaction of business in producing and distributing merchandise required many agencies: the manufacturer, importer, commission men, bankers, jobbers, commercial travelers, and retailers.`（改述拼合；另段 `Until twenty years ago trade rules limited the sales of manufacturers to commission men` 同属阶段划分，改述）。

## Candidate Claims

- C-T1（fact）：Wanamaker 生意的诞生年被商店自己定义为 1861（林肯就任之年），1911 年庆祝五十周年金婚（src-f652ed07aa15 `Fifty years ago Abraham Lincoln became President of these United States. Fifty years ago the John Wanamaker Business was born.`）。
- C-T2（fact）：商店年表 1862-1910（缩短工时/开店/电灯/现金输送管/周六半休/钢琴业/新楼钢柱），出自商店自家出版物（src-eabfd2f57aac；src-f652ed07aa15）——**宣传声口，数字与"第一"未独立印证**。
- C-T3（fact）：商店学校在 1909 年前已运行约 12 年（≈1897 始），被纳入新楼建筑（src-161fd427387d）。
- C-T4（lineage）：本道 train 源仅 1 份（Lincoln Chair 宣传册），时间线主体靠 writings/expression 道间接提取。

## Contradictions and alternative explanations

- **商店创立年 1861 vs 1876**：宣传册（1911）说 1861 年"生意诞生"（指与 Bennett 合开的男装店），而 1914 年讲话与 1910 年 Chronology 说"1876 年现店开业"、1900 年 Evolution 说"四十年前旧制度"——两者是"创业起点"与"百货店起点"之别，不是矛盾；引用须带口径（1861 男装店 / 1876 百货店）。
- **"第一"清单全是自述**：电灯第一、现金输送管第一、钢琴革命等均出自商店自家出版物，无外部印证；下游不得当独立史实。
- **宣传册的"物证叙事"不可独立核验**：林肯椅的流传链（Coleman→Oldroyd→Peterson 宅）为宣传册单方叙述，语料内无第二来源。

## Unknowns and source gaps

- 本道仅 1 份 train 源（4KB 宣传册）；**无自传、无年谱、无报纸报道**。人物全部生平日期（1838 生、1861 开店、1889-1893 邮政部长、1922 卒）均不在本语料 train 内——只有"1861 诞生""1876 现店开业"等商店叙事与"五十年"的 1911 锚点。
- 宣传册内"1911 金婚"是时间下沿；上沿信息（1844-1861 林肯椅）属林肯生平，非 Wanamaker。
- Chronology 段的商店条目年份（1862/1876/1878/1880/1886/1899/1904/1909）为逐条年号，未与任何外部资料交叉验证。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- C-T1/C-T2 进 facts：时间锚（1861 诞生/1911 金婚）与商店年表（1862-1910），全部标注"商店自述/宣传声口"。
- C-T3 与 expression 道"商店学校"互证，供 work/facts 使用。
- **声口纪律**：Lincoln Chair 宣传册的一切"第一/纪念"表述按宣传声口折减；1861 vs 1876 两个起点口径须在 facts/divergence-map 注明。

## 这一道给下游的东西

- **时间锚清单**：1861 生意诞生（宣传册）；1876-03-12 现店开业；1862 缩短工时；1878 电灯；1880 现金输送管；1886-07-04 周六半休；1899-04-15 钢琴业；1902-02-22 新楼破土；1904/1909 亲手立钢柱；1905 全天候电话；1910 费城卷出版（以上均自 src-eabfd2f57aac）；1911 金婚（src-f652ed07aa15）；1912 Taft 献词；1914 夏末周六休息实验（src-4e53b2952a15）。
- **宣传册声口样例**：`waived his usual profit`、`tender memories of not only Abraham Lincoln … but also of The John Wanamaker Golden Jubilee`——下游建模"广告/纪念"类场景的直接素材。

## 未做完 / 未核

- Lincoln Chair 宣传册 4KB 已整本读毕；但其中"Oldroyd 收藏史/彼得森宅"段未与其他林肯文献比对。
- 1910 Chronology 段只取了商店条目，城市条目未核。
- "1861 男装店"与"1876 百货店"两口径的关系在本语料内只有宣传册单方表述，未与外部史料核对。