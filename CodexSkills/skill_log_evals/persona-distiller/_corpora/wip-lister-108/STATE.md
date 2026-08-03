# #108 Joseph Lister —— 可续检查点

日期：2026-08-03　｜　蒸馏版本 `v0.0.0.37`　｜　**英文原著，无译文层**

---

## 一、已完成（全部实跑）

| 步 | 结果 |
|---|---|
| 同名门 | `resolution none / ready`；**实搜出一号风险是他父亲**，见 `NAMESAKE_HAZARD.md` |
| 建工作区 | `workspaces/joseph-lister`，`--profile deep --subject-origin historical --language en --time-scope 1827-1912` |
| 抓源 | **61 份 24.78 MB**（writings 44 / external 13 / biography 4） |
| **一手占比** | **72.1%（44/61）—— 过 deep 门 65%** |
| `check_corpus_integrity` | **62 份全是真文档，0 张错误页** |
| ingest | **61 成功 / 0 失败**，1 份 holdout |
| 六路 | writings 29 / external 11 / decisions 10 / expression 8 / conversations 2 / timeline 1 —— **六路齐** |

## 二、★★★ 第一次在抓源阶段就控住比例

Koch #107 收了 121 份、对手方 66 份，`primary_ratio` 只有 45.8%，**因此拒发**。
这一次我在派活时就写死：**一手先收足（≥30），对手方按需收、不求全**。
结果一手 44 份、占比 **72.1%**——**不是先收全再筛出来的，是按配比抓出来的。**

## 三、★★ 全集的性质与 Koch 相反，且有一手依据

《The Collected Papers of Joseph, Baron Lister》(Oxford, 1909, 2 卷)，
**出版于其生前**（他 1912 年卒）。序言逐字：

> "the Committee which has prepared these volumes for the press has had the inestimable
> advantage of **his guidance and advice**. The two volumes contain all the papers and
> addresses which **he himself considers** to possess permanent interest and importance"

**选目权在他本人，且他在世。** 这与 Koch 全集（1912 年身后编成、编者文字混入）性质相反。

**但仍有编者层，位置已定**：卷 I 的 PREFACE 与 Cameron 所撰 INTRODUCTION。
**这两处不得记为他本人之言。**

## 四、★ 同名排除是机器可复核的（抓源方给了三条判法）

1. **creator 字段**：archive.org 对父作 `Lister, Joseph Jackson`，对子作 `Lister, Joseph`
2. **年份**：子生于 1827、1853 才首发；**凡 1850 年前之作必非子**
3. **题材**：显微镜光学、水螅与海鞘解剖属父，子无此类著作

据此**主动不取父的 4 条**（含 1830 年那篇消色差物镜）与博物学家那位的 6 条。
反向确证：`philtrans09346010` 扉页署
"Joseph Lister, Esq., F.R.C.S., **Assistant Surgeon to the Royal Infirmary, Edinburgh**"
——身份、职务、年份三重锁定。

**★ 一处需要留意的**：全集卷 II 里有 16 处 "Joseph Jackson Lister"，
查下来是**他本人写的悼父文**《Obituary Notice of the late Joseph Jackson Lister, F.R.S.》
以及他引用父亲 1830 年那篇。**是子写父，不是父的作品**，记 writings——
而且它正好是「儿子能看见微生物靠的是父亲的镜子」这条线索的一手材料。

## 五、核心文献全部到手

- **《Collected Papers》两卷，各两个独立扫本（共 4 份）**
- **1867 Lancet《On a New Method of Treating Compound Fracture, Abscess, etc.》五篇原刊全到**
  （Iss. 2272 / 2273 / 2274 / 2278 / 2291）
- **1867 BMJ《On the Antiseptic Principle in the Practice of Surgery》**（另有 Lancet 版 Iss. 2299）
- 1869 结扎术、1870 医院卫生度（2 版本）、1858《On the Early Stages of Inflammation》（3 扫本 + Phil. Trans. 原刊）

**OCR 全部干净**：61 份英文虚词占比 0.178–0.274（干净区间 0.20–0.25）；
最低那份是 Lawson Tait 的死亡率统计专著，表格稀释虚词，抽读确认字迹清晰，**判为不报废**。

## 六、抓不到的（真实缺口）

- **1874 年 Lister 致 Pasteur 的信**与 1886 年书信——IA 有扫描但只是图像，OCR 出不来文字。
  **要文本得另找誊录本。**
- 《On the Lactic Fermentation》(1878)、《On the Flow of the Lacteal Fluid...》(1857)
  无单行本，**但全文都在《Collected Papers》卷 I 内**（已 grep 确认），不算实质缺口。

## 七、下一步

```bash
# 1. 读研究门实测（后台跑中，25 MB 语料约需 2 分钟）
# 2. attribution_basis 四字段 + 44 条 P1 逐份点名
#    ★ authority 要写「选目权在他本人且他在世」，并列明编者层的两处位置
# 3. 六路正文；★ 04-external 的对手立场必须指到对方的书
# 4. 断言层：work-method ≥3 条可复用（石炭酸规程与前后死亡率是最好的素材）
# 5. 出题：★ 题面每个数与口径先回语料核
# 6. ★★ 每轮记候选与基线的**绝对分**，不只记 delta
#    （Koch 三轮：delta 升而候选绝对分跌 0.215）
```

## 八、本人物的两个结构性优势（要用足）

1. **英文原著，无译文层**——与 Jenner #104 同；Pasteur（法文）、Koch（德文）栽的那一层不存在。
2. **全集生前出版且选目权在他**——Koch 那种「身后编者混入」的问题不存在。

**所以这一位若还是不过，原因不会在语料层，只会在断言与答案层。**
