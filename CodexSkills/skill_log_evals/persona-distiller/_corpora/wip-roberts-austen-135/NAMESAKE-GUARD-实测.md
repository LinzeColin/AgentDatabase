# Roberts-Austen #135 同名护栏实测

判据：`namesake-criteria.json`　候选册：`namesake-candidates.json`　闸门：`namesake-gate.json`
所有判定**都是跑出来的**，命令见文末。

---

## 零、这个人物的同名问题为什么特别

**他一生用过两个姓。** 1843 年出生名 `William Chandler Roberts`；1885 年依王室许可、
应舅父 Major Nathaniel Lawrence Austen 之请加姓 Austen，此后署 `Roberts-Austen`。

印本证据（照录自本轮落盘正文）：

| 年 | 载体 | 扉页／署名照录 |
|---|---|---|
| 1884 | Cantor Lectures on Alloys used for Coinage | `CANTOR LECTURES ON ALLOYS USED FOR COINAGE, BT W. CHANDLER ROBERTS, RR.S.` |
| 1888 | Phil. Trans. Roy. Soc. A 179 | `By W. Chandler Koberts- Austen, F.RS, Professor of Metallurgy in the Normal School of Science and Royal School of Mines, South Kensington, Chemist and Assay er of the Royal Mint.` |

**四年之隔，同一个人，两个姓。** 任何只认一个姓的判据都会漏掉他半生的东西。

而且他的复姓以**英语最常见姓氏之一** `Roberts` 打头——判据的排除正则
`(?<![A-Za-z])` + 记号按 `\s*` 连接**只有词首边界、没有词尾边界**，
于是「排除某个 Roberts」这件事本身就是雷区。

---

## 一、同名者：15 人（另 4 条禁区条目）

`namesake-candidates.json` 共 19 条，其中 1 条是目标本人、15 条是真实同名者、
3 条是**亲属**（父 George Roberts、外祖父 William Chandler、舅父 Nathaniel Lawrence Austen）、
1 条是**看着最该排除而绝不能排除**的同代人（Charles Frederick Chandler）。

**Roberts 一侧（8 人）**：Sir William Roberts（1830-1899 医生 FRS）、Isaac Roberts（1829-1904 天文 FRS）、
Richard Roberts（1789-1864 机床）、Charles Roberts（1836-1901 人体测量）、
Robert Davies Roberts（1851-1911 地质／推广教育，**DNB 补编里紧挨目标条目的前一条**）、
Alexander William Roberts（1857-1938 变星）、William C. Roberts（1932-2023 心脏病理，现代检索污染源）、
Charles Hubert Roberts。

**Austen 一侧（7 人）**：R. A. C. Godwin-Austen（1808-1884，**1854 年前署 `Robert A. C. Austen`**——
与目标同形状的一次改姓）、H. H. Godwin-Austen（1834-1923，1854 年前称 `Henry Haversham Austen`）、
Peter Townsend Austen（1852-1907 美国化学家）、Ernest Edward Austen（1867-1938 昆虫）、
Jane Austen（检索污染）、Austen Henry Layard 与 Austen Chamberlain（**`Austen` 作教名**）。

**★ 有一整类可以划掉**：DNB 1912 补编原文 `he had no issue`——**无子嗣**，
因此不存在「同姓后代」这一类同名者。

---

## 二、区分字段

| 字段 | 取值 | 为什么 |
|---|---|---|
| `surname`（贴近锚点） | **`oberts`** | 见下第三节——受损的恰是首字母 |
| `marker_window` | **45** | 见下第四节——实测 41 字 + 余量 |
| `any_of_markers` | 22 条：10 条姓氏形（含讹形）＋ 12 条机构／职衔（Royal Mint、Chemist of the Mint、Chemist and Assayer、Royal School of Mines、Royal College of Science、Normal School of Science、Professor of Metallurgy、Alloys Research、Assay Master、K.C.B.、Chandler Roberts…） | 机构与职衔是硬标识；题材词不是 |
| `excluded_names` | 29 条，**全部是完整消歧形式** | 见下第五节的禁区 |
| `bare_name_before_year` | `William Roberts` / 1868 | Royal Society《Catalogue of Scientific Papers》收他 74 篇，起讫 **1868-1900**（DNB 1912 补编原文） |

**不许单独使用的三条**（已写进判据）：
`F.R.S.`（目标、Sir William Roberts、Isaac Roberts、两位 Godwin-Austen **全是 FRS**）、
首字母 `W.`（`A. W. Roberts` 与 `W. Roberts` 同形）、
题材词 `austenite`（**相变名里就嵌着他的姓**，那是关于他不是他写的）。

---

## 三、★★★ `surname` 锚点从 `Roberts` 改成 `oberts`——实测逼出来的

判据拿 `surname` 做**纯子串**贴近检验，没有模糊匹配。跑全部 26 份落盘正文，
姓氏的印本 OCR 形态**实测 14 种**（逐形计数，不是记的）：

```
108  Roberts-Austen        69  Roberts- Austen        6  Eoberts-Austen
  5  Boberts-Austen         5  Roberts -Austen        4  Koberts- Austen
  2  Eoberts- Austen        2  Koberts-Austen         1  Roberts Austen
  1  Roberts-Aicsten        1  Roberts-AuBten         1  Eoberts-Aiisten
  1  Roberts- A listen      1  Roberts- Ansten
```

- 写 `Roberts-Austen` → `Koberts- Austen`／`Boberts-Austen`／`Roberts- A listen` 这些**目标本人的署名**全部贴不上。
- 写 `Roberts` → 仍然漏：**`philtrans08066202`（Proc. Roy. Soc. 71, 1902）全篇 0 处 `Roberts`**，每一处都被打成 `Eoberts`。
- 受损的恰是**首字母**（R→K／B／E）。去掉首字母的 `oberts` 在 26 份里**一次也没被打坏**。

**把锚点挪到没被损坏的那一段**——这是实测结论，不是取巧。

---

## 四、`marker_window = 45`

- **逼出这个数的那一行**（Phil. Trans. A 187, 1896 Bakerian 扉页照录）：
  `By W. C. Roberts- Austen, C.B., F.R.S., Professor of Metallurgy, Royal College of Science ; Chemist of the Mint.`
  从 `oberts` 词尾到 `Royal College of Science` 词首**实测 41 字**——英式职衔串把姓氏与机构名撑开。窗口 40 判不到。
- **为什么不取更大**（跑了 45／60／120 三档）：

  | 检验 | W=45 | W=60 | W=120 |
  |---|---|---|---|
  | 反例串 `Mr. Thomas Roberts, of the Sheffield file works, was afterwards shown over the Royal Mint.`（实测距离 **61 字**） | unknown ✓ | unknown ✓ | **目标本人 ✗** |
  | 真语料 26 份判为「目标本人」 | 26/26 | — | 26/26 |

  **放宽零收益，却把反例放进来。** 取能容纳英式职衔串的最小整值。

---

## 五、★★★ 排除名单的禁区——**逐条实测过，不是推理**

体检办法：把每个候选字面单独放进 `excluded_names`（清空 markers），
对 **15 条真实印本字串**（1885 前后两个姓、家世段、改姓段、扉页、版口、著录卡）各跑一次，
看它把多少条判成「他人」。判成他人 ＝ **会删掉目标自己的材料**。

| 候选字面 | 命中目标本人 | 会删掉什么 |
|---|---|---|
| `Roberts` | **10/15** | 1885 年前的全部署名 + 复姓前一半 |
| `Austen` | **11/15** | 复姓后一半的每一次出现 |
| `Chandler` | **6/15** | 他的中名——`W. Chandler Roberts` 全部署名 |
| `W. C. Roberts` | **4/15** | 全语料 `W.`+`C.`+`[RKBE]oberts` 实测 **29 处**，两个方向同时错 |
| `William Chandler` | **3/15** | **外祖父的全名 = 他全名的前两段** |
| `George Roberts`（父） | 2/15 | 每一篇写家世的传记 |
| `Nathaniel Lawrence Austen`（舅父） | 1/15 | 解释 1885 年改姓的全部材料 |
| `Professor Roberts` | 1/15 | `BY PROFESSOR ROBERTS-AUSTEN`（Canada's Metals 扉页） |

### ★ 我第一版把 `William Roberts` 的理由写错了，被实测打回

**第一版写的理由**：「它会命中 `William Chandler Roberts-Austen`」。
**跑出来不会**——判据把名字编成记号间只许空白的正则 `William\s*Roberts`，中名 `Chandler` 横在中间，匹配不上。
初测结果是 **0/15**，看起来这条可以安全排除。

**真正的理由是去语料里找出来的**：全 26 份扫描 `William` 紧挨 `Roberts` 的写法，
**只有 2 处，两处都是目标本人**，逐字照录：

> `Sir Andrew Noble. Sir William Crookes. Sir William Roberts- Austen. The Right Hon. R. B. (now Lord) Haldane.`
> `BIBLIOGRAPHY. PAPERS AND ADDRESSES BY THE LATE SIR WILLIAM ROBERTS- AUSTEN RELATING TO THE METALLURGY OF IRON AND STEEL.`

两处都在 1914 年 Smith 编《Roberts-Austen: A Record of His Work》里，
**第二处正是他本人著作目录的标题行**。把 `William Roberts` 或 `Sir William Roberts` 写进排除名单，
这两处判「他人」——**整部 1.24 MB 的书被删掉**（实测 2/2）。

> **教训**：没跑过的理由不许写进判据。第一版那句话读起来完全合理，是错的。
> 而且两版的**结论相同**（这条不许排除）、**理由完全不同**——
> 结论对而理由错正是最难发现的一种（Sorby #133 的 `Clifton` 同形）。

### 那位真同名的医生怎么办

Sir William Roberts（1830-1899）是本人物最高危的同名者，而 `William Roberts` 不能排除。
改用**带学位后缀的完整消歧形**：`William Roberts, M.D.` 与 `W. Roberts, M.D.`
（目标持 D.C.L. 1897／D.Sc. 1901，**没有 M.D.**）。实测：对 15 条目标真串**零命中**，
对医生的两条真串**双双判为他人**。

### 全表体检

29 条 `excluded_names` × 15 条目标真串 = **435 次**逐条跑过，
**目标本人零命中**。

---

## 六、正例／反例总表（跑出来的）

| 组 | 内容 | 结果 |
|---|---|---|
| ① | 目标本人 15 条真实印本字串（含 1884 旧姓扉页、1888/1896 新姓扉页、`A listen` 讹形版口、`Eoberts` 讹形版口、著录卡、1914 传略首行） | **15/15 判「目标本人」** |
| ② | 他真实的同名者 15 条 | **15/15 判「他人」** |
| ③ | 反例：只有题材词 `austenite`、无署名 | unknown ✓（**不是目标本人**） |
| ④ | 反例：另一个 Roberts 与 `Royal Mint` 隔 61 字同现 | W=45 unknown ✓／W=120 误判 ✗ |
| ⑤ | 判据自带 self-test（Sorby 的七组对照） | **✓ 自测全过** |
| ⑥ | 排除名单逐条反向体检 435 次 | **目标本人零命中** |
| ⑦ | 对**真实台账** 26 份 | 目标本人 26　他人 0　**unknown 0** |

★ 第 ① 组里的**家世段**与**改姓段**单看会判 unknown（那两句只提到父／外祖父／舅父，
不提目标本人的任何区分符）——这是**对的**：unknown 是「没核」不是「不是他」。
它们在真实台账里落在整份 DNB 条目内，全篇有区分符，因此第 ⑦ 组判为目标本人。

---

## 复核用命令

```bash
WS=…/_corpora/wip-roberts-austen-135
TGT=$WS/workspaces/william-chandler-roberts-austen

python3 scripts/check_namesake_criteria.py --self-test     # → ✓ 自测全过
python3 scripts/check_namesake_criteria.py "$TGT"          # → 目标本人 26　他人 0　unknown 0
```

姓氏讹形计数、435 次反向体检、窗口三档对照的脚本见 FETCH-REPORT.md 文末。
