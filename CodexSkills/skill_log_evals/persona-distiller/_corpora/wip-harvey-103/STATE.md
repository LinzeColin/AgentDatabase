# Harvey #103 —— 可续检查点（探源已交回，**灌库起步**）

**日期**：2026-08-02

## 已完成

| 步骤 | 状态 |
|---|---|
| 同名门 | **ready**（3 候选；风险以机构为主，另有其父 Thomas Harvey 落在他族） |
| 工作区 init | deep 档、`subject_origin: historical`、语言 la |
| 探源 | **交回**：54 件可取、`primary_ratio` **75.9%**、六路全覆盖、holdout 已定 |
| 归属依据门 | **✓ 通过**，`disputed_works` **4 条已填实** |

## ★ 探源自己先提出的诚实问题，必须由人裁定

> **54 件可取，但去重后只有约 32 部不同著作**——其中 15 件是《De Motu Cordis》
> 1639→1908 的不同版次与译本。**把 15 件算成 15 条源，正是拖垮前两位的语料注水。**

本工作区已裁定并写进 `meta.json:counting_convention`：
**版次算源**（各有自己的扉页、印工、译者，版次差异本身是证据），
**但任何断言都不得建立在「本语料含 N 个版次」之上**——那是账本事实，
按 `check_fact_density` v0.0.0.29 不计入密度。

## ★★ 探源交回 40 条带页码的人物事实——这是前两位失败之处

样本（每条都能回原件核）：

- **Hofmann 的指控原文**：说他把自然指为「a most clumsy and inefficient artificer」；
  哈维的回信是**拒绝为一个他从未提出的主张辩护**，并注明日期 **Nürnberg, 20 May 1636**。
- **纽伦堡当众演示后他放下解剖刀走人**——Slegel 1650 年的序独立佐证。
- **牛膀胱注水实验**：在一具绞刑犯尸体上、当着数位具名同行；判据是
  「不是一滴水或血从左室的切口漏出」，改扎肺动脉后「一股混着血的液体立刻从左室的穿孔涌出」。
- **芦管插动脉那条，他指控前人纸上谈兵**：「neither Vesalius nor Galen says that he had
  tried the experiment, which, however, I did.」
- **定量论证的全部数字**：左室容量、每搏排出比例、半小时逾千次搏动，
  推出十磅五盎司／二十磅十盎司／四十一磅八盎司／八十三磅四盎司四组；
  **论证不是任一数字为真，而是每一个都超过全身血量**。
  并有一条对照是他实测的：「a fact which I have myself ascertained in the case of the sheep」。
- **蒙哥马利子爵之子的开胸病例**：查理一世派他去核实；他伸进三指与拇指、
  以「一手按心、一手按腕」的时序判据认出那是心尖；**并把病人带到国王面前让他摸活人的心**。
- **托马斯·帕尔的尸检（1635）**：他把死因归给伦敦的煤烟与骤变的饮食，不归给年龄。
- **他承认自己从没看见过动静脉吻合**：「I have never found any visible anastomoses.」
- **他临终前六周拒绝重启研究**（致 Vlackveld, 1657-04-24）：「I now consider myself
  entitled to my discharge from duty.」
- **Aubrey 记的原话**：论培根「'He writes philosophy like a Lord Chancelor,' said he to me,
  speaking in derision; 'I have cured him.'」；1651 年对 Aubrey 说读书要
  「goe to the fountain head … and did call the neoteriques shitt-breeches」。
- **出版的职业代价**：书出之后「he fell mightily in his practize … 'twas beleeved by the
  vulgar that he was crack-brained」。
- **1642 年埃奇山**：受托看顾王子，「tooke out of his pockett a booke and read」，直到炮弹擦地才挪地方。

## ★ 归属分层里最要紧的一条

`Prelectiones`（1616 Lumleian 讲席笔记）**不得承载年份断言**：
1886 年印本自序**自己承认**删去了红笔批注，而同一篇序又断言这份笔记是他首次提出循环之处。
**用一份自承有删节的版本去支撑一个年份断言，这条链是断的。**

因此「他 1616 年已有循环说」**必须溯源到他 1628 年致 Argent 的献词**
（「nine years and more」，即约 1619 年起）。

另得一条用源规则：**Aubrey 论其为人一流，论其书目不可靠**
（他说 George Ent 代译拉丁文，Willis 按年代与 Ent 自己的献词驳倒了）。

## 缺口（下一次接着做）

1. **灌库未做**——探源表里 54 个 URL 全部实测 200，直接抓即可。
2. 六路研究、断言层、用例、答案、裸模型对照、两席判分、打包、登记——**全部未做**。
3. 断言层按 v0.0.0.29/31 口径：**账本事实一条不计入密度**；
   直接用上面那 40 条，**每条都带页码**。
4. holdout 已定：**Mitchell 1912《Some Recently Discovered Letters》中的 1636 年 8 月
   Feilding 书信**——1912 年才由 HMC 发现，Willis 1847 不可能含它；
   已 grep 全语料确认零泄漏；**且是全库唯一一批哈维本人未经翻译的英文散文**。
