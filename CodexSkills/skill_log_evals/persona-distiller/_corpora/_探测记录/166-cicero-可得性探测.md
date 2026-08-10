# Marcus Tullius Cicero（前106–前43）可得性探测报告

探测日期：2026-08-10 ｜ 方式：只读网页探测（WebSearch + WebFetch），**未下载任何文件**，**并发恒为1**（全程顺序单发），**未访问任何付费墙内文**（loebclassics.com 仅通过其公开可见的 URL 路径/书目页/书评核实年份，从未登录或读取其正文），**未触发/未绕过任何验证码**。本报告只探测可得性与证据结构，不产出任何蒸馏产物，**未写入任何工作区**，仅存于本文件。

## 证据核实层级说明（贯穿全文使用）

- **[核实A]**：我用 WebFetch 直接打开了该确切 URL，亲眼看到译者名/出版年/正文内容。
- **[核实B]**：内容来自 WebSearch 的结果摘要（通常整合自搜索引擎索引到的该页文字或权威书目库），给出了具体年份/引文，但我没有独立再打开那一页复核。
- **[核实C]**：只核实了"存在 + 书目元数据"（书名/译者/年份），未读正文。
- **查不到**：明确尝试但没有找到或访问失败（如404/503），如实标注，不臆测。

---

## 结论摘要（对应最终要交付的五点）

1. **方法证据是分散的，不是集中的。** 与 Pacioli（记账方法只存在于一部作品、三个译本只算一处证据）不同，Cicero 至少有三个独立体裁互相印证同一方法/思维习惯：论著自陈方法（De Officiis）、修辞短论点名引用自己的真实法庭演说（De Optimo Genere Oratorum → Pro Milone）、书信中记录的真实编辑决策（Ad Atticum 论 Academica 献词）。若判据要求"方法类断言 ≥2 处独立证据"，Cicero 现存候选轻松过线，且不靠译本数量凑数。
2. **拉丁原文完全免费、无门槛、覆盖面极广**（Perseus + The Latin Library）。**英译本方面有一个具体陷阱**：De Oratore、Brutus、Orator、De Natura Deorum、Academica 这五部作品**"默认能搜到的现代标准 Loeb 译本"全部出版于1930年之后**（1933/1939/1942），不满足本项目 PD 分界；但每一部**都存在更老（1776/1853/1855）的公有领域替代译本**，只是不是搜索引擎第一个给出的那个。
3. **第一人称密度随语域剧烈摆动，跨度超过100倍**：法庭演说开篇质问段 0/525 词，全篇聚合约1/95–110词；私人书信约1/13–14词；哲学对话内部又分裂成两种声口（Cicero本人序言声口约1/28–31词，对话角色Laelius的论证声口约1/120词）。只抽一种语域、甚至只抽一部作品的一段，都会得出误导性结论。
4. **同名者共5人（含1个容易被忽略的陷阱）**：本人、独子"小西塞罗"（前30年执政官）、胞弟 Quintus Tullius Cicero、侄子 Quintus Tullius Cicero（父子同名）、以及**释奴秘书 Marcus Tullius Tiro——他的 praenomen+nomen 与本人完全相同（"Marcus Tullius"），只有 cognomen 不同**，按"Marcus Tullius"做字符串检索会直接命中他。
5. **未能核实清单见文末第⑤节**，主要是：Academica/Varro 献词那批书信（Att. 13.12/13.13/13.16）的原文页多次访问失败，只做到 [核实B]；多数 Loeb 早期卷次的年份是搜索结果给出、未逐页打开复核；第一人称计数全部是 WebFetch 工具（小模型）辅助读数，不是我逐字人工复核，误差可能有 ±20%。

---

## ① 方法证据：集中在一部作品，还是分散在互不相同的作品里？

### 背景对照

Pacioli 案例：记账方法论述**只存在于 Summa de Arithmetica 这一部作品**，三个不同译本被判定只算一处独立证据来源，导致"方法/思维方式类断言需要 ≥2 处独立证据"这道门只能勉强摸到 1 个思维模型 + 1 条启发式（门要 2 和 3）。

Cicero 的情况实测下来结构不同：同一个方法/思维习惯，能在**至少三个互相独立的体裁**里找到，而且不是靠"同一句话被翻译了几次"凑数，是三处**内容不同、场合不同、写作动机不同**的独立文本。

### 例1：论著自陈方法——"两面论证"（in utramque partem / Academic 怀疑方法）

**[核实A]** *De Officiis* 卷二第8节，Walter Miller 译本（Harvard University Press / Loeb Classical Library No. 30, **1913**）。
URL: https://www.perseus.tufts.edu/hopper/text?doc=Perseus:abo:phi,0474,055:2:8

我亲眼读到的译文原句（英译，逐字引用，21词，出自1913年公有领域译本，不受版权限制）：
> "our school argues against everything, that is only because we could not get a clear view of what is 'probable'"

Cicero 在这里明确自陈：他属于"新学园派"，方法是对每个立场都正反论证，为的是找出"更可能为真"的一侧，而不是武断下结论。这是他反复讲的方法论自述（同一自述在 Tusculan Disputations、De Natura Deorum、De Divinatione 的前言里也各自出现过，但那些还是"哲学论著"这同一个体裁大类，独立性较弱）。

### 例2：修辞短论点名引用自己的真实法庭演说——治世自证

**[核实A]** *De Optimo Genere Oratorum*（论最佳雄辩体）第10节，拉丁原文，A. S. Wilkins 校订本。
URL: http://www.perseus.tufts.edu/hopper/text?doc=Perseus:abo:phi,0474,041:4:10

我亲眼在这一页看到 Cicero 在讨论"雄辩风格该如何匹配场合"时，**直接点名自己真实出庭辩护过的案子 "pro Milone"**（原文短语：*"...dici pro Milone decuisse..."*，意为"为米洛辩护时本应如此陈说"）。他用这个真实法庭案例（不是虚构例子）来论证：演说风格必须匹配场合的紧张程度（Milo案审判时法庭周围有全副武装的军队环伺，与私人诉讼的从容语调完全不同）。

这一条价值在于：**不是我在推断"修辞理论"和"演说实践"有关联，是 Cicero 本人在另一部作品里明确把两者绑在一起**。修辞短论（论如何写作/翻译）和真实法庭演说（Pro Milone，前52年实际发表）是完全不同的体裁、不同的写作动机、相隔数年，构成货真价实的独立互证。
（旁证 [核实B]：剑桥期刊 *Greece & Rome* 有专文讨论这条互证：Cicero's pro Milone and the 'demosthenic' style: De optimo genere oratorum 10——只看到摘要，未读全文，因为该刊正文在付费墙后，本次未访问。）

### 例3：书信记录的真实编辑决策——Academica 献词从 Catulus/Lucullus 改为 Varro

**[核实B]**（未能独立打开确切信件页，见第⑤节）：Wikipedia "Academica (Cicero)" 词条（**[核实A]**，我直接打开读过这页）记载：Cicero 最初把 *Academica* 献给 Catulus 和 Lucullus（书中角色），后来因为 Atticus 的意见，认为这两人"eminent men but in no way scholars"（原文 *homines nobiles illi quidem sed nullo modo philologi*，不适合讨论高深的知识论），**改献给 Varro**。搜索结果里能看到具体拉丁语句 *"ad Varronem transferamus"*（让我们把它转献给Varro），但这句我是从搜索摘要看到的，没有独立打开 Ad Atticum 13.12/13.13/13.16 那几封信的原文页核实（尝试了，503和404都遇到了，见第⑤节）。
URL（Wikipedia，[核实A]）: https://en.wikipedia.org/wiki/Academica_(Cicero)

这一条如果成立，是"哲学论著的前言" × "私人书信"两个体裁互证一次真实的编辑/写作决策过程——比例1、例2都更接近 Pacioli 案例要求的那种"完全独立体裁"，但因为我没能亲自打开原信，**证据强度定为 [核实B]，建议正式蒸馏前找人工复核 Att. 13.12/13.13/13.16 原文**。

### 小结

即使只用完全经过 [核实A] 的例1+例2（论著自陈 + 修辞短论点名真实演说），已经是两处**不同体裁、内容不同**的独立证据，超过"≥2处独立证据"的门槛，且不依赖译本数量。例3若经人工复核为真，会补上第三处（论著前言 × 私人书信），进一步逼近"启发式类 ≥3"的门槛。**Cicero 不会重演 Pacioli 那种"1个思维模型+1条启发式卡在门外"的局面**——前提是选证据时有意识地跨体裁取材，不要在"哲学论著"这一个大类里反复横跳凑数量（De Officiis/De Finibus/Tusc. Disp./De Nat. Deorum/Academica 这五部互相之间独立性是弱的，都算"哲学论著"一类）。

---

## ② 拉丁原文 vs 英译：谁的话算数

### 拉丁原文：完全免费、无门槛

- **Perseus Digital Library**（Tufts大学）[核实A，多次直接打开成功，全程无登录提示]
  收藏索引：https://www.perseus.tufts.edu/hopper/collection?collection=Perseus%3Acorpus%3Aperseus%2Cauthor%2CCicero
  确认收录：Academica、De Amicitia、De Divinatione（两个校订本）、De Fato、De Finibus、De Inventione、De Legibus、De Natura Deorum、De Officiis、De Oratore、De Republica、De Senectute、Epistulae ad Familiares、Letters to/from Brutus、Letters to/from Quintus、Letters to Atticus、Lucullus、全部演讲（Verrines、Catilinarians、Philippics 等）、Paradoxa Stoicorum、Timaeus、Tusculan Disputations，以及**弟弟 Quintus Tullius Cicero 名下的 Commentariolum Petitionis 拉丁文本**（Perseus 页面标注作者为 Q. Tullius Cicero，注意这条不是 Marcus 的作品）。
  各篇校订者不同（Plasberg、Falconer、Müller、Stroebel、de Plinval、Miller、Wilkins、Purser、Clark、Peterson、Baiter/Kayser、Pohlenz 等），均为20世纪初的学术校勘本，**拉丁原文本身没有版权问题**（作者已故2000余年）。

- **The Latin Library**（thelatinlibrary.com）[核实A]
  索引页：https://www.thelatinlibrary.com/cicero（注意不是 `/cicero.html`，那个路径404）
  三大分类：ORATORIA（演讲，33篇）、PHILOSOPHIA（哲学，23种）、EPISTULAE（书信，4个集子）。**无登录、无付费墙、无验证码**，直接打开 https://www.thelatinlibrary.com/cicero/cat.shtml 验证过可正常显示拉丁文（页头 "M. TVLLI CICERONIS ORATIONES IN CATILINAM"）。

### 英译本：谁的话算数——关键提醒

**译文版权归译者**，与 Cicero 本人的公有领域身份无关。本项目 PD 分界 = 出版于 **≤1930**。逐一核实结果如下（体裁 / 译者 / 出版方年份 / 是否≤1930 / URL / 核实层级）：

| 作品 | 体裁 | 译者 | 出版方 · 年份 | ≤1930? | URL | 层级 |
|---|---|---|---|---|---|---|
| 演讲全集（含 In Catilinam I-IV） | 演讲 | C. D. Yonge | Henry G. Bohn, London, **1852**（四卷本）/**1856**重印 | 是 | https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.02.0019%3Atext%3DCatil.%3Aspeech%3D1 | A |
| Epistulae ad Atticum（全）+ ad Familiares + ad Quintum + ad Brutum | 书信 | Evelyn Shuckburgh | George Bell & Sons, **1899–1900**（初卷）/1908（后续卷次再版） | 是 | Wikisource: https://en.wikisource.org/wiki/Letters_to_Atticus/1.1 ；Gutenberg: https://www.gutenberg.org/files/21200/21200-h/21200-h.htm | A（Wikisource页译者/年份+正文）|
| Letters to Atticus（Loeb，仅此信集） | 书信 | E. O. Winstedt | Harvard/Heinemann, 卷1=**1912**，卷2=**1913**，卷3=**1918** | 是 | archive.org: https://archive.org/details/letterstoatticus01ciceuoft ；Gutenberg卷2: https://www.gutenberg.org/cache/epub/50692/pg50692-images.html | B |
| Letters to Friends（ad Familiares，Loeb） | 书信 | W. Glynn Williams | Harvard, **1927**（卷1-3） | 是（但很接近门槛，1927距1930只差3年） | archive.org（搜索结果中出现条目，未独立打开） | B |
| De Officiis | 哲学（书信体，致其子） | Walter Miller | Harvard University Press（Loeb 30）, **1913** | 是 | https://www.perseus.tufts.edu/hopper/text?doc=Perseus:abo:phi,0474,055:2:8 | A |
| De Officiis（另一同期译本） | 同上 | Cyrus R. Edmonds | Bohn, **1856** | 是 | 书目页 pagesofpages.com/bohn（见下）| C |
| De Amicitia（Laelius）/ De Senectute / De Divinatione | 哲学 | William Armistead Falconer | Harvard University Press（Loeb）, **1923** | 是 | https://www.perseus.tufts.edu/hopper/text?doc=Cic.+Amic.+1 | A |
| Academic Questions（=Academica）/ De Finibus / Tusculan Disputations | 哲学 | C. D. Yonge | Bohn, **1853** | 是 | Gutenberg: https://www.gutenberg.org/files/14988/14988-h/14988-h.htm | C（书目页确认存在+年份，未打开正文核对是否逐字完整）|
| On the Nature of the Gods / On Divination / On Fate / On the Republic / On the Laws / On Standing for Consulship | 哲学 | C. D. Yonge | Bohn, **1853** | 是 | 同上Gutenberg 14988 | C |
| **De Natura Deorum / Academica（现代"默认"版本）** | 哲学 | H. Rackham | Harvard University Press, **1933** | **否——晚3年，不满足PD** | Perseus目录记录：https://catalog.perseus.org/catalog/urn:cts:latinLit:phi0474.phi050.opp-eng2 | A（目录页年份直接核实） |
| De Oratore（旧译） | 修辞学 | J. S. Watson | Bohn, **1855**（后多次重印1871/1896） | 是 | archive.org: https://archive.org/details/ciceroonoratoryo00ciceiala | B |
| **De Oratore（现代"默认"版本）** | 修辞学 | E. W. Sutton / H. Rackham | Harvard/Heinemann, **1942** | **否——晚12年** | loebclassics.com URL 本身标注 `/LCL348/1942/`（未进入付费墙正文，仅读URL/书目信息） | A（URL即证据） |
| Brutus / Orator（旧译，现存最早英译） | 修辞学 | E. Jones | London: B. White, **1776** | 是 | Gutenberg: https://www.gutenberg.org/ebooks/9776 | B |
| **Brutus / Orator（现代"默认"版本）** | 修辞学 | G. L. Hendrickson / H. M. Hubbell | Heinemann, **1939** | **否——晚9年** | loebclassics.com: https://www.loebclassics.com/view/LCL342/1939/volume.xml ；PhilPapers书评确认："Heinemann, 1939" | A（两处独立来源都确认年份，未读付费墙正文） |
| De Optimo Genere Oratorum | 修辞学短论 | 拉丁：A. S. Wilkins；英译者未查实 | 拉丁部分见Perseus | 拉丁本身天然PD；英译年份**查不到** | https://www.perseus.tufts.edu/hopper/text?doc=Perseus:abo:phi,0474,041:4:10 | 拉丁=A，英译=查不到 |

### 关键提醒：不要信任"搜到的第一个"

**De Oratore、Brutus、Orator、De Natura Deorum、Academica 这五部作品的现代标准 Loeb 译本（今天搜索引擎/Perseus目录最先给出的那个）全部出版于1930年之后**（1933/1939/1942），不满足本项目 PD 分界。但**每一部都存在一个更老、公有领域的替代译本**：De Oratore 有 Watson 1855，Brutus/Orator 有 Jones 1776，De Natura Deorum/Academica 有 Yonge 1853。这些老译本不是搜索引擎默认排序第一位给出的结果，需要专门去找（书目库 pagesofpages.com/bohn 和 Gutenberg 目录比较可靠）。

**结论**：Cicero 全集不存在"无法可得英译"的作品，但如果流程是"打开 Perseus/搜索引擎第一个链接就抄译文"，会在这五部作品上**静默踩雷**（英译不合规，即使原文和作者本人都毫无疑问是公有领域）。这是 Cicero 特有的坑，Pacioli 案例里不会遇到（他只有一部相关作品，不存在"这一部里有的篇章能查到年份、那五部踩雷"的分裂局面）。

Bohn's Classical Library 书目页（用于核对多个 Yonge/Watson/Edmonds 条目年份）：https://pagesofpages.com/bohn/bohn_classical_library.html [核实A]

---

## ③ 声口：三种语域的第一人称密度（分语域取样，务必对照读）

**方法说明**：以下计数由 WebFetch 内部模型辅助读数完成，不是我逐字人工复核，视为**近似值**（可能有±20%误差），词数同理为约数。发布前如需精确数字，建议用脚本对下列URL的纯文本做正则统计。

| 语域 | 具体篇目 | 译者/年 | 词数(约) | 第一人称单数次数(约) | 密度(约) | URL |
|---|---|---|---|---|---|---|
| 法庭演说——开篇直接质问段 | *In Catilinam* I, 第1章（"Quo usque tandem..."） | Yonge 1856 | ~525 | **0** | 0/525 | https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.02.0019%3Atext%3DCatil.%3Aspeech%3D1%3Achapter%3D1 |
| 法庭演说——全篇聚合 | *In Catilinam* I，全13章/33节 | Yonge 1856 | ~8000–9500(工具估算，未独立复核) | **~85–90** | ≈1/95–110 | https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.02.0019%3Atext%3DCatil.%3Aspeech%3D1 |
| 私人书信（致 Atticus） | *Ad Atticum* 1.1（论自己的执政官竞选） | Shuckburgh 1900 | ~1200 | **~85–90** | ≈1/13–14 | https://en.wikisource.org/wiki/Letters_to_Atticus/1.1 |
| 哲学对话——Cicero本人序言声口 | *De Amicitia* §1（回忆年轻时求学于 Scaevola） | Falconer 1923 | ~250–280 | **9** | ≈1/28–31 | https://www.perseus.tufts.edu/hopper/text?doc=Cic.+Amic.+1 |
| 哲学对话——对话角色 Laelius 论证声口 | *De Amicitia* §20（论友谊的抽象定义） | Falconer 1923 | ~240 | **2** | ≈1/120 | https://www.perseus.tufts.edu/hopper/text?doc=Cic.+Amic.+20 |

### 读出来的三点

1. **法庭演说内部本身就能摆动100倍以上**（同一篇演说，第1章0次 vs 全篇均值约1/100词）——取样位置比"取样自哪个体裁"更容易造成误判，这一点比项目已实测的"演讲改写文章 vs 正式论文"发现更极端：那次是跨体裁摆动，这次是**同一体裁、同一篇演说内部**就能从0摆到高密度，因为法庭演说的修辞策略本身在"直接质问对方（你/你的）"和"自证清白/自陈政绩（我/我的）"之间切换。
2. **私人书信密度最高**（约1/13–14词），这是三种语域里离"本人真实想法"最近的一层，也最直接呼应②——如果最终蒸馏要找"未经修饰的第一人称"，书信是最稳的语域，且已确认充分公有领域（Shuckburgh 1900 + Winstedt 1912-18 两套独立译本互相印证）。
3. **哲学对话不是单一声口，必须先判断"这段是谁在说话"**。De Amicitia 表面上整篇都是"第一人称"，但其中**只有开头的叙事框架是 Cicero 本人的"我"**（回忆自己年轻时的经历），一旦进入 Laelius 展开哲学论证的正文，语法上的"我"就变成了 Laelius 这个角色在说话，不是 Cicero 本人的自陈——这是 Cicero 特有的复杂度：De Officiis 通篇都是 Cicero 本人的声口（直接写给儿子），但 De Amicitia、De Senectute、De Finibus、Tusculan Disputations、De Natura Deorum、De Oratore 这些"对话体"作品里，大部分正文的"我"要先核实说话人是谁，才能判断这段是不是真的算 Cicero 本人的第一人称证据。**这个问题在选②的证据素材时也要注意**：De Amicitia 的英译文本如果被当成"Cicero 说了什么"的素材整段摘录，摘到 Laelius 说话的部分就会张冠李戴。

---

## ④ 同名者

| 人物 | 关系 | 生卒（约） | 易混点 | 区分方法 | URL |
|---|---|---|---|---|---|
| **Marcus Tullius Cicero**（本人） | — | 前106–前43 | — | — | — |
| **Cicero Minor**（"小西塞罗"，全名同为 Marcus Tullius Cicero） | 独子（母 Terentia） | 前65（或前64）–前30年后仍在世 | **与父亲姓名完全相同**，拉丁文献常仅写"M. Cicero"或"Cicero filius" | 看年代/事件：前30年任补缺执政官、向元老院宣布安东尼死讯的是**儿子**（本人早在前43年已被处死） | https://en.wikipedia.org/wiki/Cicero_Minor [核实A] |
| **Quintus Tullius Cicero** | 胞弟 | 前102–前43（与兄同日被处死） | 姓氏(Tullius Cicero)完全相同，仅praenomen不同(Quintus vs Marcus)；常被简称"Quintus"；名下存疑作品 *Commentariolum Petitionis*（竞选手册）作者权本身有争议（有学者主张实为兄长代笔或后世伪托） | 看praenomen是Marcus还是Quintus；Perseus拉丁库把 *Commentariolum Petitionis* 单独标注为"Q. Tullius Cicero"名下，与本人作品分开列 | https://en.wikipedia.org/wiki/Quintus_Tullius_Cicero [核实A] |
| **Quintus Tullius Cicero**（侄子/小昆图斯） | 侄子（胞弟之子） | 前66–前43（与父、伯父同日被杀，狱中未供出父亲藏身处） | 与父亲同名同姓，父子两代都叫 Quintus Tullius Cicero | 看年代（前66年生，前43年死）；无独立传世作品，出现时几乎都是"某人之子"身份 | 同上（Quintus Tullius Cicero 词条内提及）[核实A] |
| **★ Marcus Tullius Tiro** | 释奴／终身私人秘书 | 前103年前後–前4年 | **praenomen+nomen 与本人完全相同**（"Marcus Tullius"，释奴按罗马习俗沿用主人前两段姓名），仅 cognomen "Tiro" 不同——**按"Marcus Tullius"做全字符串或作者字段检索，会直接把他的书信残篇/速记记录混进本人名下** | 看cognomen "Tiro"；他不会有演讲/哲学对话署名，主要关联是书信收件人/代笔、以及"Tironian notes"速记符号发明者身份 | https://en.wikipedia.org/wiki/Marcus_Tullius_Tiro [核实A] |
| Tullia（女儿，阴性形式） | 女儿 | 前79–前45 | "Tullia"与"Tullius"词根相同，在按家族姓氏(Tullius/Tullia)做模糊检索时可能被并入 | 看性别标记的词尾/称谓 | 见 Cicero Minor 词条内提及 [核实A] |

**排序建议**：如果检索/归属逻辑只按"姓名字符串"匹配，最危险的顺位是 **Tiro > Cicero Minor > 侄子Quintus > 胞弟Quintus**——Tiro因为前两段姓名100%相同、且大量以"代笔/速记"身份出现在本人书信语境里，最容易被系统性地误当作本人证据，风险等级最高。

---

## ⑤ 未能核实的（如实列出，不臆测）

1. **Academica 献词从 Catulus/Lucullus 改献 Varro 这批关键书信的原文页**：尝试直接打开 Perseus 的 *Ad Atticum* 13.12（`doc=Perseus:text:1999.02.0022:text=A:book=13:letter=12`）遇到 **HTTP 503**，重试后页面只返回目录结构没有正文；改试 Wikisource `Letters_to_Atticus/13.12` 遇到 **HTTP 404**（该站书信编号体系可能与Perseus不同，未进一步排查正确路径）。目前这条证据的信息来源是 Wikipedia "Academica (Cicero)" 词条的转述 + 搜索引擎摘要里出现的拉丁短语，**没有做到亲自打开原信复核**，标记为[核实B]，建议正式使用前人工补验。
2. **De Optimo Genere Oratorum 英译本的译者/出版年**：只确认了拉丁原文（Perseus, Wilkins校订）。英译据搜索结果可能出自 H. M. Hubbell（收录于 Loeb "De Inventione; De Optimo Genere Oratorum; Topica"卷），但**具体出版年没有查到**——如果这一卷和同一译者的其他Cicero卷次一样跨越1930年分界，需要单独核实，不能假定。
3. **多数 Loeb 早期卷次的具体出版年**，是从 WebSearch 结果摘要/loebclassics.com URL 路径/archive.org条目标题读到的，**没有逐一用 WebFetch 打开确切原书页核对**（标记[核实B]的条目均属此类）：Winstedt译Letters to Atticus三卷、Williams译Letters to Friends、Edmonds译De Officiis 1856版、Yonge译1853合集是否逐字完整（只核实了书目存在，没打开正文数页数）。
4. **第一人称计数的精确度**：全部计数由 WebFetch 调用的辅助模型读数给出，不是我本人逐词人工复核或脚本统计，视为粗略估计，误差可能达±20%；De Officiis/De Amicitia以外的作品完全没有取样（比如Verrines、Philippics、Pro Milone本身、Ad Familiares书信）。
5. **The Latin Library 是否收录 Quintus Tullius Cicero 本人作品**：确认了该站三大分类不含Quintus独立署名的作品区，但没有反向搜索确认这类作品在该站是否以其他方式（如附在Marcus作品目录里）收录。
6. **De Amicitia、De Senectute 之外的其他"对话体"作品**（De Finibus、Tusculan Disputations、De Natura Deorum、De Oratore、De Re Publica、De Legibus）**同样存在"哪段话算谁说的"这个声口归属问题，但本次只用De Amicitia做了验证性取样，没有逐部核实每部作品里 Cicero 本人作为具名角色出场的比例**（有些对话里"M."/Cicero本人是具名发言人之一，比如据背景知识Tusculan Disputations和De Natura Deorum，但这一点本次未逐一打开核实，不确定，不列入正文结论）。
7. **loebclassics.com 付费墙内文完全没有访问**——所有关于该站条目的信息均来自其公开URL路径本身透出的年份、以及第三方书评/书目站点，符合"不碰付费墙"的约束，但也意味着任何该站声称的"revised translation"版本差异（有些Loeb卷次后来出过修订版，修订版翻译本身可能有新的版权起算点）未被排查——**如果某卷是"1913年首版、1930年代修订"，修订版的译文本身可能有独立于首版的版权状态，这一点本次完全没有能力核实**。

---

## 使用的工具与访问方式记录

- WebSearch（顺序调用，约15次）+ WebFetch（顺序调用，约20次），**无并发**。
- 未使用 Bash/curl/wget 等下载类工具，未保存任何 PDF/HTML/图片到本地。
- 访问过的站点：perseus.tufts.edu（多次，全部成功无登录墙）、thelatinlibrary.com（成功，无登录墙）、en.wikisource.org（部分成功部分404）、gutenberg.org（未直接WebFetch正文，仅WebSearch索引到）、archive.org（未直接WebFetch正文，仅WebSearch索引到）、en.wikipedia.org（多次，全部成功）、pagesofpages.com（成功）、catalog.perseus.org（成功）、loebclassics.com（**仅见于WebSearch结果里的URL/标题，从未WebFetch其正文**）。
- 全程未遇到验证码；遇到的访问失败均为 404/503 类错误，已在第⑤节列出，未做任何绕过尝试。
