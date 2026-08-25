# Expression DNA and micro-behavior

## Scope and assigned sources

**本道分到 4 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-342fd9325225` | 1900 | P1 | The Evolution of Mercantile Business（American Academy of Political and Social Science 年会发言，JSTOR） |
| `src-161fd427387d` | 1909 | P1 | The John Wanamaker Commercial Institute — A Store School（The Annals） |
| `src-2f57e8856a02` | 1912 | P1 | Address on the occasion of the visit of President Taft at the dedication of the Wanamaker Store |
| `src-4e53b2952a15` | 1914 | P1 | Mr. Wanamaker's address to the aisle managers of the John Wanamaker store（口头发言记录） |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## 五条实测发现（逐份）

### ① 《The Evolution of Mercantile Business》（1900）——百货零售的"实证辩护学"声口

`src-342fd9325225` 是 Wanamaker 在"资本组合作为产业进步要素"年会上的发言（题名页 OCR 作 `Wanamakbr`=Wanamaker）。**论点先行、数据佐证、替行业辩护**是他的主导声口。核心命题是"百货店=服务公众=压低价格"：

> Public service is the sole basic condition of retail business growth. To give the best merchandise at the least cost is the modern retailer's ambition.
<!-- src-342fd9325225 -->

> His principle is the minimum of profit for the creation of the maximum of business.
<!-- src-342fd9325225 -->

- **对"百货=垄断"指控的直接反驳**（`com-petition` 折行连字归一）：

> so long as competition is not suppressed by law, monopolies cannot exist in storekeeping, and that the one quarter of the globe that cannot be captured by trusts is most assuredly that of the mercantile trading world.
<!-- src-342fd9325225 -->

- **"水流不能高过源头"的格言式推论**（句中横页眉，用 [版口] 分段各自命中）：

> It is an old axiom that the water of a stream cannot rise [版口：ia8 Annals of the American Academy.] beyond its level. Neither can any business rise or thrive except at the will of the people who are served by it.
<!-- src-342fd9325225 -->

- **量化辩护**（低价=全民储蓄、商店数=竞争未萎缩的证据）：

> It is an easily proven fact that the operation of the American retail system has reduced the prices of many classes of goods one-half in twenty years.
<!-- src-342fd9325225 -->

> I believe the new American system of storekeeping is the most powerful factor yet discovered to compel minimum prices.
<!-- src-342fd9325225 -->

> The keys of every public question are in the hands of the people, and it is the people alone who, by neglect and discouragement, slow up and stop the wheels of progress.
<!-- src-342fd9325225 -->

- **承认大店的代价、但用"公共福利"压平**（`Doubtless there must be some disadvantages arising from large single businesses of every kind` 为可核句；"既无教养的愚昧、又安于现状的小店主，都辩不倒大店影响小店铺这一事实"一句因语料 `well-\ndressed` 跨行折字无法逐字成句，改述，引文见 :188-202 段）。- **自评方法论**：他称自己的数字是"fair estimate from an experience of twenty-five years and more of careful study"，并自陈 `I desire to be a witness for the truth`（改述）——把生意经验当"证人证言"用。

⇒ 声口/论点：**行业辩护人 + 数据举证者**。面对"百货店挤死小店/垄断"的指控，他的策略是：①先承认确有代价，②再用"人民利益/最低价/竞争未萎缩"三件套翻盘，③最后落到"人民的钥匙在人民手里"。修辞上爱用"水流不高过源头"式谚语收束。

### ② 《The John Wanamaker Commercial Institute》（1909）——商店学校的"教育即雇佣"观

`src-161fd427387d` 自述创办"商店学校"的动机。**职业尊严论 + 学用相长论**：

> a business career is a profession as noble in its way as that of the lawyer or the engineer. Men and women must be trained for it. They must become specialists.
<!-- src-161fd427387d -->

> it is an organization inside the Wanamaker store in Philadelphia to enable those who are doing the day's work and earning a living to get a better education to earn a better living.
<!-- src-161fd427387d -->

> the two have marched along shoulder to shoulder, study assisting labor, and labor in turn illuminating and illustrating book knowledge. The two together daily increase his value to his employer and to himself.
<!-- src-161fd427387d -->

- **斥"纯机械雇佣观"**（工时换工资的契约不构成雇主-雇员关系的全部）：

> The payment of an agreed wage from one to the other, the taking in exchange specified hours of labor and the continuation of this mechanical system through weeks and months and years, define neither an employer's relation to his people nor the duty of the workers to one who happens to control their output of energy and brains.
<!-- src-161fd427387d -->

- **"从基层提拔"是成文的店策**：

> it is a great fixed policy of the house to build up from the ranks, and the boys and girls of to-day will be the chiefs of to-morrow.
<!-- src-161fd427387d -->

- **把学校砌进新楼的决策自白**（商业教育与建筑实体合一）：

> my confidence and firm belief in the value of the commercial institute and its relation and application to the laws of the business has led me to build it into the new Philadelphia store building in stone and iron and cement.
<!-- src-161fd427387d -->

- **"little and often"教学法**（OCR 引号为直引号，照录）：

> It is "little and often and continuous" that counts, as the horse said every time he put down a foot.
<!-- src-161fd427387d -->

⇒ 声口/论点：**雇主启蒙论**——把店员当"要培养成专门人才的人"，把教育当商店的固定开支与政策；"从基层提拔"是他反复使用的口号（与 Timeline 道的"店内学校"互证）。

### ③ 《Mr. Wanamaker's Address to the Aisle Managers》（1914）——口语化的"人性化劳资"声口

`src-4e53b2952a15` 是 1914-05-27 对通道经理（aisle managers）的口头发言记录，讨论"夏末周六休息"新政。**本卷 OCR 损伤极重**（词首字母大面积缺失、`meet;`/`n eet;` 等），引文一律取可核片段。

- **开场谦和、拉家常**（`con¬ference` 为软连字符，未逐字引，取可核前半）：

> I am very glad to be invited to meet you tonight for this little conference.
<!-- src-4e53b2952a15 -->

（引文以 `con¬ference` 的软连字符形态存在于语料，`¬` 在比对时按排印归一。）

- **把缩短工时当"教育公众"的运动**：

> I believe that the people can be educated to go along with us in the matter of shortening the hours of service
<!-- src-4e53b2952a15 -->

- **劳工观的格言（名句；OCR `ictivity`=activity、`hings`=things 讹形照录）**：

> I think the real genius of labor is ceaseless ictivity. It is not that somebody has a great, big brain that thinks out great hings, but the real thing is to keep at it all the time.
<!-- src-4e53b2952a15 -->

- **员工福利的"第一个"自述**（回忆 1876 开店初）：

> We were the first to prepare a place where we furnished cooking ranges to the people to cook anything they brought; we furnished, without cost, milk and sugar and some other little things
<!-- src-4e53b2952a15 -->

- **对"退货被滥用"的抱怨（OCR `habi c`=habit、`o .`=of 讹形，只引可核句）**：

> so many goods don't stay sold.
<!-- src-4e53b2952a15 -->

（续句大意"人们养成了拿回家半打衬衫/半打绸缎头再退掉任何想要退的"——语料 `the habi c`/`remnants o . silk` 损伤无法逐字成句，改述。）

- **"亲自上阵"的现场感**（语料 `he  main`=the main 缺 t）：

> I began by putting on he main aisle some few benches.
<!-- src-4e53b2952a15 -->

⇒ 声口/论点：**口语化、自嘲式、把雇员当"自己人"**。他先讲自己当学徒时的苦（`Many a time I left old Oak Hall at ten minutes to twelve`，改述），再讲"这是你们的商店/你们是船长"，把商业决定讲成"人性回应"（`a response to the human spirit that is in people who care for each other`，改述）。与 Evolution 的书面辩护声口互补。

### ④ 《Address at the Dedication of the Wanamaker Store》（1912）——庄严场合的"商业=文明"声口

`src-2f57e8856a02` 是 Taft 总统为 Wanamaker 新楼剪彩时的献词（本卷 OCR 损伤重，`d^free`=degree、`aU`=all、`chat`=that 等讹形照录）。

- **"诚实劳动胜过军舰"（名句）**：

> Mr. President, honest, hearty, fairly paid labor is better than fleets of war vessels to conserve the peace and happiness of any country.
<!-- src-2f57e8856a02 -->

- **商业的自我贬抑式辩护**（"若商业只是买卖就太渺小了"）：

> if mercantile business is only buying and selling it is a very small affair and narrowing to those engaged in it. The blacksmith and the engine builder, who produce sometlimg the world wants, are more worthy of honor.
<!-- src-2f57e8856a02 -->

（`sometlimg`=something 讹形照录。）

- **反托拉斯立场（与 Evolution 同调）**：

> A competitive and co-operative business is the antithesis of such trusts as are permitted to monopolize business.
<!-- src-2f57e8856a02 -->

- **为广告行业呼吁"说真话"（进步主义腔调）**：

> I appeal for the recall, for the recall of old-fashioned truth-telling in public print, editorially, locally and advertisingly, because the constant and almost unconscious filtration of poison into the body politic and physical is a blood poisoning that is at least devitalizing to life.
<!-- src-2f57e8856a02 -->

- **能力观（"越能者越能"）**：

> the more a man or a people can do the more it is possible for them to do.
<!-- src-2f57e8856a02 -->

- **"新商业"自我定位**（`New Kind of Business` 是他的自造标签，OCR 作 `New / Kind  of  Business`）：

> At the time the New Kind of Business was instituted here there was no other store in America organized upon the same basis.
<!-- src-2f57e8856a02 -->

⇒ 声口/论点：**庄重场合的"商业荣光"修辞**——把商店讲成"国家的学校/就业的守护者"，把诚实劳动、自由竞争捧为国家和平与繁荣之基；对托拉斯与"把财富当投机"持鲜明的对立面。此卷与 Evolution（1900）相距十二年，声口从"行业辩护"升格为"文明宣言"。

## Candidate Claims

- C-E1（fact）：百货=公共服务——"货最优、价最低"是现代零售商的志向，利润最小化以换取生意最大化（src-342fd9325225 `Public service is the sole basic condition of retail business growth`、`the minimum of profit for the creation of the maximum of business`）。
- C-E2（mental-model）：竞争是防垄断的天然机制，只要法律不压制竞争，零售不会被垄断（src-342fd9325225 "so long as competition is not suppressed by law, monopolies cannot exist in storekeeping"；src-2f57e8856a02 "A competitive and co-operative business is the antithesis of such trusts…"）。
- C-E3（value）：诚实劳动优于战争与投机（src-2f57e8856a02 "honest, hearty, fairly paid labor is better than fleets of war vessels"；"The blacksmith and the engine builder…are more worthy of honor"）。
- C-E4（mental-model）：雇佣=教育的对等关系，工资换工时不是全部契约（src-161fd427387d "define neither an employer's relation to his people nor the duty of the workers"）。
- C-E5（heuristic）：从基层提拔+持续小量教育（src-161fd427387d "build up from the ranks"、"little and often and continuous"）。
- C-E6（expression）：口语/书面双声口——格言收束（"水流不高过源头"）、拉家常开场、庄严颂词（src-342fd9325225；src-4e53b2952a15；src-2f57e8856a02）。

## Contradictions and alternative explanations

- **"利润最小化"是立场声明，不是会计事实**：Evolution 既说"最小利润/最大生意"，又承认大店确有代价（`Doubtless there must be some disadvantages arising from large single businesses of every kind`）、且小店主把失败都算在大店头上（`an unsuccessful effort was made to decry them as monopolies`）——他是在辩护文体内给出理想化模型，不是描述现实账本。
- **"退货"的双面声口**：1900 年把退货当"对消费者的恩惠"（`not as a favor but as a condition of the contract of sale`，"return of goods for"与"refund"间横页眉，改述），1914 年却抱怨"退货被滥用"（`so many goods don't stay sold`）——同一原则，从"营销卖点"到"经营痛点"，是立场随场景切换，不是逻辑矛盾。
- **"服务公众"与"促销话语"并存**：Evolution 是年会上的公共话语，Aisle Managers 是店内的执行话语；二者修辞不同（前者讲原则、后者讲销售），引用须按场景取用。

## Unknowns and source gaps

- **Aisle Managers（1914）OCR 损伤最重**：词首字母大量丢失（`meet;`/`n eet;`/`neet;`、`adiust`、`tire` 等），长句几乎无法逐字成句，本道只取可核片段；"hot potato for lunch""Waldorf-Astoria 轮船"等轶事段未逐字重建。
- **Taft 献词（1912）OCR 同样损伤重**：`d^free`/`aU`/`chat`/`sometlimg`/`tr;insactions`/`tdl` 等讹形，长句仅部分可逐字；"Williamson 学校 vs 商店学校"对照段（:223-227）只取轮廓。
- **Evolution（1900）的统计数字未与外部核对**（1870 年 16,560 家店、1900 年 34,000+、降价一半、储蓄 1,000 万等）——只能当"其自称"，语料内无外部印证。
- **四卷都无"个人对话"记录**：Aisle Managers 虽是口头发言记录，仍属"对雇员讲话"而非一对一访谈——conversations 道的独立源不在此（见 02 道）。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- **服务公众主簇（C-E1 + C-E3）**：与 writings 道"serve the public"合流成 persona/work 核心理念。
- **竞争防垄断（C-E2）**：mental-model 主证，进 cognitive-os/boundaries——他反"托拉斯垄断"，不反"大店竞争"。
- **雇佣=教育（C-E4/C-E5）**：work-method 主证，进 work/decision-policy；与 06-timeline 的商店学校年表互证。
- **声口对照（C-E6）**：进 persona——正式场合庄重、店内场合拉家常、书面场合举证辩护。
- **OCR 词汇指纹**：`Wanamakbr`=Wanamaker、`sometlimg`=something、`chat`=that、`tr;insactions`=transactions、`tdl`=tell、`mutiplying`=multiplying、`helpfulnss`=helpfulness、`habi c`=habit、`o .`=of、`he`=the（Aisle）、`con¬ference`（软连字符）、`6c`=and（History 卷）；引文照录。

## 这一道给下游的东西

- **"百货=服务=低价=竞争"的四连环**（Evolution 全文）：可作 claims 的 mental-model 主干。
- **"诚实劳动胜过军舰/托拉斯"**（Taft 献词）：可作 persona 的价值观与 boundary（反投机）。
- **"商店学校/从基层提拔/劳动是持续行动"**（Commercial Institute + Aisle Managers）：可作 work 文档的可复用做法。
- **双声口素材**：拉家常（"I am very glad to be invited…"）、格言收束（"水流不高过源头"）、庄严颂词（"诚实劳动胜过战争舰队"，语料作 `honest, hearty, fairly paid labor is better than fleets of war vessels`，见 ④）——分别对应店内/书面/庆典三种场合。

## 未做完 / 未核

- Aisle Managers（1914）与 Taft 献词（1912）的 OCR 损伤段落未逐字重建，只取可核片段；两卷的长轶事（1876 开店初的"热土豆午餐"、纽约轮渡上的黑人清洁工对话、轮船尺寸轶事）只记轮廓。
- Evolution 的统计表（1870/1900 商店数、降价幅度、$246,239.27/$697,428.23 福利数）未与任何外部数据交叉验证。
- Commercial Institute 卷内"军事营/乐队/夏令营"等组织细节未核（与商业声口关系弱，略过）。
- 本道未读未引：本道只引上述四份 train 源；其余来源一律未读。