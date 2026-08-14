# 抓源 → 研究阶段的**十件**工具（2026-08-12 新建，第 1 批 10 人跑通）

**这九件不是判据**（判据在 `registry/codex/persona-distiller/scripts/`，91 件，本轮一件没动）。
它们是把「一个人名」变成「判据能吃的四个数」的流水线。

## 一条命令跑完一个人

```bash
cd CodexSkills/skill_log_evals/persona-distiller/_corpora
PL=../_ledgers/_pipeline
WS=wip-<name>-<n>/workspaces/<slug>      # ★ 布局：语料在 $WS/raw（存量 42 个工作区就是这个）
W=$WS/raw

python3 $PL/probe_ia.py   --query 'creator:"<姓, 名>"' --rows 200 --out wip-<name>-<n>/04-探源.tsv
python3 $PL/curate_ia.py  --tsv wip-<name>-<n>/04-探源.tsv --person <key> --out $W/_ids.txt --cap 70
python3 $PL/fetch_ia.py   --ids-file $W/_ids.txt --out $W
python3 $PL/classify_primary.py --raw $W --surname <姓> [--surname 别拼法]
python3 $PL/dedup_corpus.py     --raw $W
python3 $PL/assign_lanes.py     --raw $W

# ★ 改过 classify_primary / assign_lanes 之后**必须跑这一件**（默认只查不改）
python3 $PL/check_measurements_fresh.py          # 有不一致就 rc=1 并逐项列出
python3 $PL/check_measurements_fresh.py --apply  # 确认之后再重出
python3 $PL/scan_copyright.py   --raw $W          # ★ PD 最后一道，**逐条读命中**
python3 $PL/measure_voice.py    --raw $W --samples 8
python3 $PL/emit_source_ledger.py --raw $W --workspace $WS
python3 $PL/assign_holdout.py    --workspace $WS --raw $W        # 先不加 --apply 看方案
python3 $PL/pull_quotes.py --raw $W --ledger $WS/evidence/source-ledger.jsonl \
        --lane writings --exclude-third-party --first-person     # ★ 取回来要**逐条人判说话人**
python3 ../../../registry/codex/persona-distiller/scripts/emit_lane_scope.py \
        wip-<name>-<n>/workspaces/<slug>          # Scope 节由台账现算，**别手打**
```

然后把四个数喂给**项目自己的判据**（★ 档位由它判，不要自己算）：

```bash
# 台账已生成时**用 --ledger**（口径与门完全一致，不用自己传数）：
python3 ../../../registry/codex/persona-distiller/scripts/check_corpus_ceiling.py \
  --ledger wip-<name>-<n>/workspaces/<slug>/evidence/source-ledger.jsonl --profile deep
```

`--profile` 依次试 `deep → standard → quick`，**第一个 rc=0 的就是这个人能到的档**。

---

## 每件在做什么、以及它是被哪次事故逼出来的

| 工具 | 做什么 | 硬保证（都是实测换来的） |
|---|---|---|
| `probe_ia.py` | 只检索不下载 | **必印 `numFound`**（只看前 N 条会把「窗口太小」读成「就这么多」）；**零命中当错处理**（rc=4） |
| `curate_ia.py` | 探源结果 → 抓取清单 | 五道筛**逐道报丢了多少**；**上限按馆轮转**（否则 30 卷同一批 bsb，min_lanes 是虚的）；**词元匹配姓名**（`Friedrich Fröbel` 名在前也要命中） |
| `fetch_ia.py` | 唯一的下载入口 | `access-restricted-item` **硬跳过**（不绕访问控制）；并发 4，**遇 429/403 降 1 且不再抬回**；**合并 manifest 不覆盖**；`ia_date` 是原作年**不是版次年**，PD 看 `titlepage_years` |
| `classify_primary.py` | 一手／二手 | **`需人判` 不默认成一手**，只能由 `_primary-decisions.json` 显式裁掉；`(?<!auto)biograph`；`former owner` = 藏书主不是作者 |
| `dedup_corpus.py` | 文件数 → 独立文献数 | 用 token shingle 的 min-hash，**不用 `difflib`**；**只报簇不替人判**「同卷多扫描」还是「同书不同卷」 |
| `assign_lanes.py` | 分六条研究道 | 道语义**取自 35 个存量 `source-ledger.jsonl` 实测**，不按字面猜 |
| `check_measurements_fresh.py` | **量测产物是不是这版工具出的** | ★ **改了上面两件之后必须跑**——2026-08-13 实测 4 个工作区的产物是旧版留下的（Kant 道 6→3），而工具的注释里早就写着那个修正。**修好判据不等于修好数据。** |
| `scan_copyright.py` | **PD 的最后一道，唯一读正文的一道** | 元数据挡不住在版权期内的重印／译本——**实测 6 份混进来**；决定性信号只有 ISBN 与「© 年份 >1930」，`All rights reserved` 是老书的套话不算 |
| `emit_source_ledger.py` | → `evidence/source-ledger.jsonl` | `derived_from` 由查重簇填；`title` 用真题名；`split` 全 train，**holdout 由人另指**；出处从 `source_url` 现推（不再写死 archive.org）。★★ **它是纯重生成**：重跑会把 `split`／`attribution`／`extraction_status`／`tier`／`rights` 全部推回规则值 —— 已有台账时**默认拒跑 rc=3**并逐条列出会丢什么；剔源重出用 `--preserve` 接续，`--force` 才是真丢 |
| `pull_quotes.py` | 取**可复算定位**的逐字引文 | `norm_offset` 自带 `text[off:off+len]==quote` 断言；四道筛（悼词署名行/目录行/词中起头/题名页）；★ **它判不了说话人** |
| `assign_holdout.py` | 分盲判密封面 | 用**判据自己那把尺子**量重合；**已引用过的不密封**；**不抽空任何一道**；★ k 词片**按哈希值抽不按位置抽** |
| `flag_borrowed_voice.py` | **标记「这句的第一人称可能不是本人」** | 四种机制①传记转录他人书信②小说角色对白③校勘者/编者序言④权利声明；★ **只给理由和原文证据，说话人由人定**；正 7 例负 12 例**全取真语料**，另做逐条拆规则的变异测试 |
| `measure_voice.py` | 声口密度 | **先修 OCR 折行断字**（一份文件里 77.8% 的命中是断字）；**先打印命中原句再报率**；主语脱落语另看动词 |

---

## ★★ 七个最容易踩的坑（第 1 批全踩过一遍）

### ① 「我跑了判据」不等于结论可靠

同一个问题我得出过**四个不同答案**，②③④ 都是跑 `check_corpus_ceiling.py` 得出的：

    ① 份数+占比手算            → 9 人 deep    ← 漏了 min_lanes
    ② 加 lanes、按字面定义      → 9 人 quick   ← 道义定窄了
    ③ 道义按存量实测 + 定向抓   → 4 人 deep    ← 二手年表归错道 + 同名门被绕过
    ④ 修完                     → **6 deep / 3 quick / 1 够不着**

**判据只验算术，不问「你这个 lane 分得对不对」。**
凡是我自己定义的分类字段（lane／tier／一手二手），**先去仓里找已有实例**。

### ② 同名门是挂在**检索式**上的，不是挂在人物上的

主检索式带 `creator:` 时同名门有效；补 `external`／`timeline` 道要够到第三方材料，
换成 `title:"<姓>"` —— **护栏静默失效**，一次抓进缅因州一个叫 Jefferson 的镇、
Jefferson Davis、Thomas Jefferson Lamar、Thomas Paine 的传记、
以及众议员 Rousseau O. Crump。
⇒ **每加一条新检索路径，重问一次「这条路上同名门还在吗」。**
   第三方材料这一档**必须逐条人读题名**。

### ③ 道数（`min_lanes`）才是真卡点，而它最容易被定窄

`quick` 要 3 道、`standard`／`deep` 要 **6 道**。份数和占比很容易过，道数不容易。
道的实际语义（**从存量实测出来的，不是字面**）：

- `decisions` = **他做判断的记录**：技术报告、专利、官方报告 —— **不只是判决书**
- `timeline` = **生平年表类，可以是第三方**：大学校史、ADB／DNB 条目、讣告、自传
- `expression` = **对外的短篇表达**：期刊短文、讲词
- `timeline` 与 `external` 都可第三方，区别是
  **前者答「何时发生何事」，后者答「别人怎么看他」**

⇒ 道空了就**按那条道单独检索并抓**，别指望主检索式顺带抓到。

### ④ PD 判定**必须打开正文看**，元数据挡不住

`access-restricted-item` 与 `IA year > 1930` 两道**都没拦住** 6 份在版权期内的材料，
因为 **IA 的 `date`/`year` 记的是原作年不是版次年**：
`kantsgesammeltes0000kant_l9l8` 元数据写 **1902**，书里印着 **`© 1978 by Walter de Gruyter`**。
⇒ 抓完必跑 `scan_copyright.py`，**并逐条读命中**：
  首扫 21 条红，读完只有 6 条成立，其余 12 条是 1882–1903 年老书上的
  `All rights reserved`（当年的套话，版权早已到期）、3 条是数字化年/OCR 噪声。

### ⑤ ★★★ 抽样要**按哈希值**抽，不要按位置抽

`assign_holdout.py` 首版的 k 词片是 `for i in range(0, n, 5)` —— **每 5 个位置取一个**。
两份文档若在共享段上的**起始偏移模 5 不同**，抽到的片**一个都不会重合**，
哪怕那一段逐字相同。**漏报概率 4/5。**

正对照（同一段 **3096 词逐字相同**，两边偏移错开 3 vs 7）：

    按位置抽样：A 616 片 / B 616 片，**重合 0 片** → 报 **0.0%**
    按哈希抽样：A 614 片 / B 615 片，**重合 613 片** → 报 **99.8%**

⇒ 改成 `h[0] % SAMPLE == 0`。**同一段文字无论落在哪个偏移上，被抽中的片都一样。**
★ 全库核过：`dedup_corpus.py` 用的是 min-hash（全部 k-gram 取最小的 keep 个），
  **按值选，不受影响**（对上面那段报 99.5%）；再无第二处按位置抽样。

### ⑥ **换尺子之后要给新尺子做正对照**

我先写了「代理指标会骗人，用判据自己的量」并照做 —— **换来的是另一把坏尺子**（上一条）。
⇒ 造一段**答案已知**的输入喂给新量具，看它报什么。
  不做这一步，就是**用一个没验过的量具去否定一个验过的结论**。

### ⑦ 声口要单独量，而且要先读命中

门数的是**来源**不是**声口**。Coffin #130 三道门全过、17 万字里实质的话只有 8 句。
量之前先修折行断字，量完先读 8 条原句 —— 第 1 批实测：
Marshall 的第一人称**是华盛顿的**（传记里引的书信），
他自己的史书叙述修断字后是 **0.02/千词**。

---

## 语料不进 git，仓里只放指针

`_corpora/.gitignore` 忽略 `*/*/raw/*.txt`，放行 `_ids*.txt` 与各 `_*.json`。
**权威重建清单是 `_ids-rebuild.txt`**（从 manifest 的「已取回」生成）——
任何 `_ids-*.txt` 都重建不出这批：清单是「打算抓的」，manifest 是「真抓到的」。

```bash
python3 $PL/fetch_ia.py --ids-file <raw>/_ids-rebuild.txt --out <raw>
```

**已端到端验过**：干净目录重抓 4 份，sha256 与仓内 manifest 逐份相同。

---

## ★★ 第 8–10 个坑（2026-08-12 下午续，都是**改了工具才发现的**）

### ⑧ 取样恒定停在卷首 —— 我在最脏的那一段里取了七次

`pull_quotes.py` 第一版每份文件 `break` 在**第一个命中**上，注释写着「保多样性」。
多样性在**源之间**，深度上却恒定停在开头。实测偏移中位数：

| 人 | `--pick first` | `--pick median` |
|---|---:|---:|
| Lincoln | 8,943（最大 11,506） | **286,560**（最大 1,007,931） |
| Jefferson | 5,568 | **346,107** |
| Rousseau | 1,723 | **155,968** |
| Marshall | 41,884 | **793,105** |

**卷首正是编者序、献词、题名页、数字化声明住的地方**——
本批 9 次「第一人称属于别人」里有 4 次是这么捡回来的。
`--pick` 默认已改 `median`。

同批另一个偏移缺陷：`off = norm.find(s)` 取的是**全文首次出现**的位置，
不是刚匹配到的那一处；同一句重复出现时（重印全集里常见）上下文会读到**错的那一处**，
而**自校验查不出来——两处文本本来就一样**。已改 `m.start()`。

### ⑨ 「第一人称属于别人」有**九种载体**，只有前八种能被机器提示

已落成 `flag_borrowed_voice.py` 的四条规则覆盖①②③④；
另外几种是**读上下文才认得出的**：

- **书简集里两个方向的信都有** —— Kant 一条句子像极了他，后面跟着呼语 `mein lieber Kant`
- **选集把本人的文字选进了「二手」那一道** —— 法文《Kant. Choix de textes》里
  一条第一人称的前文写着 `ce reproche fait à ma théorie`
- **编者引诗颂扬传主** —— Kant 一份英译本里 `Of him, more than of any child of man,
  the poet's words are true—` 后面是歌德的句子
- **编者写的年表条目**（第三人称）—— Fröbel 会话道 3 条候选全是这种

⇒ 工具的作用是**把可疑的先标出来**，不是替人判。

### ⑩ 题名词会造出**不存在的道**，而且误差单向朝「够得着更高档」漂

`assign_lanes.py` 按题名词分道，实测三类误配：
`chronolog` ⊂ `in chronologischer Reihenfolge`（**版本编排方式**）、
`judgment` 命中《判断力批判》（**书名**）、
`oration` ⊂ `commemoration`（**纯子串**）。
**Kant 的 6 条道里 3 条是假的，修正后 3 条，档位由 deep 落到 quick。**

★ 为什么单向：一份本该进 `writings` 的书被放进**空着的**道，`lanes` 就 +1；
而 `writings` 在任何有语料的人身上都非空，residual 落回去只会让计数不变。
**凡是「越错越好看」的指标，都要主动去查，不能等它报红。**

另：`discourse／discours／discorsi` **分不出讲辞和专著**（Rousseau 的《论人类不平等》、
Machiavelli 的《论李维》都是专著），已整个从 `expression` 移除。

审计口径：676 份先按词边界扫出 **142 条，逐条读完只有 3 条成立**
——其余是 `decision`→`decisions` 这类词形变化与 `Bismarckbriefe` 这类德语合成词。
**报率之前先读命中。**

### 附：`external` 那一道本来就该是二手

`pull_quotes.py` 只收 `tier=P1/P2`，于是 Kant 与 Machiavelli 的 `external`
永远取空——**而那正是这条道的定义**（别人怎么看他）。
已加 `--allow-secondary`，**并要求观察节里写明说话人是谁**。



---

## ★★ `measure_voice` 的多人对话体检测（2026-08-13 新增）

命中条件：**说话人标记密度 ≥0.5/千词**（`Mr. X.` / `Senator X.` / `ΣΩ.` 之类）。
**只报不拦，而且不判方向** —— 命中只说明「这一份里不止一个人说话」，
**不等于「这些第一人称不是他」**。全库实测 **58 份**，三种含义完全不同：

| 工作区 | 命中 | 含义 | 处置 |
|---|---:|---|---|
| **Lincoln #174** | **29/66（43.9%）** | 辩论与演说集，**他本人正是其中一位说话人** | **逐句归属，不排除**。实测：去掉后中位 6.79→6.43，**几乎没变**，判定不受影响 |
| **Plato #186** | **20/52（38.5%）** | 对话录，**那个「我」是他笔下的人物** | **不能当他的声口**（已定案：只用《书信集》） |
| **Brandeis #172** | 4/31（12.9%） | 国会听证，**他是众多证人之一** | 逐句归属；抽样实测「`Mr. Catchings. My point would be…`」不是他 |
| Jefferson 3／Leonardo 1／Marshall 1 | 少量 | 混合 | 逐句归属 |
| 其余 8 个工作区 | **0** | 单一作者 | — |

★★★ **我第一版把提示写成「这些份里的第一人称大量不是他说的」—— 那对 Lincoln 是错的**，已改成
「必须逐句判说话人」。**同一个信号，三个人物三种含义；工具不该替人下方向。**

★ 顺带一次自己的错：这段新代码**语法检查绿而一跑就 NameError**
（词数变量写成 `words`，真实名是 `n`；键名也写错两处）。
**`ast.parse` 过不代表工具能跑 —— 必须真跑一遍。**
