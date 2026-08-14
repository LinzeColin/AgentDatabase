# Kramerius 首次实取：一个 PID 里装了两部书

**2026-08-14**｜工具：`_ledgers/_pipeline/fetch_kramerius.py`（本轮新写，py3.9，`--selftest` 9/9）

## 取回了什么

    host        kramerius5.nkp.cz（捷克国家图书馆）
    PID         uuid:32d4d830-bcc0-11e4-9541-005056827e51
    题名        Korrespondence（1892，A. PATERA 编，České akademie 出版）
    页          322 页 → **有字 316／空 6**
    正文        143,711 词｜977,847 字节
    落盘        （**只在会话 scratchpad，没有进工作区**——理由见下）

单请求实测延迟 **2.586 s**（`children` 端点，95,615 字节）⇒ 一部 322 页的书约 **15 分钟**。
**不绕任何访问控制**：只取 `dostupnost=public`。

## ★★ 它和库里已有的那卷**不是**同一部作品（量过了）

    1892（新，Patera 编）   shingle 18,072
    1898（库里已有）        shingle 14,242
    交集                    **12**
    Jaccard 0.0004｜包含率(÷较短) 0.0008   ⇒ same_work = **False**

⇒ 若落账，`conversations` 道会有 **2 部独立作品**，不再是纸面道。

## ★★★ 但**没有落账** —— 一个 PID 里装了不止一部作品

切 40 块逐块数虚词（不猜，数）：

| 块 | 位置 | 语种 | 是什么 |
|---|---|---|---|
| 0–1 | 0–5% | 捷克 | **Patera 的编者序**（讲手稿 1841 年怎么从莱什诺买回布拉格，整段引 Palacký 的信） |
| 2–27 | 5–70% | **拉丁** | **Comenius 本人的书信** —— 书眉 `Ad eundem.` ×11、`Ad Patronum.` ×6、结尾套语 `observantissimus` ×10、署名 `Comenius.` ×7 |
| 38–39 | 95–100% | **德语** | **另一部作品**：18 世纪一封讲「烧死两个老妇当女巫」的德文信。**他 1670 年就没了。** |

封面写着 `ROZPRAVY ČESKÉ AKADEMIE … ROČNÍK I. TŘÍDA III. ČÍSLO 2` —— 这是**一期刊物**，
扫描件把邻期一并装了进来。[[catalog-says-one-person-bytes-are-another]]

### 我差点用错的那个边界

想按「第一个独立成行的 `1.`」定正文起点 —— 它落在全文 **95.9%** 处，
打开一读，是**德文那封女巫信的开头**。
[[stopping-at-the-first-answer-that-holds-together]]｜真正管用的信号是**书眉的周期性**
（`Ad eundem.` 那一族），同 [[front-matter-of-his-own-book-is-not-his]]。

## 裁定（我定的）

**不落账，Comenius #182 维持延后。** 三条理由，每条都可复核：

1. **归属没做完**：整卷是 Patera 编的，含编者序 ＋ 别人的信 ＋ 一部无关的德文作品；
   直接进 `train/P1/HIS-OWN` 就是 [[related-to-him-is-not-written-by-him]]
   （Liebig 那次混进 9 份，一手占比 0.7419 → 0.5192）。
2. **要切片才用得了**，而切片必须走本项目已有的「配方能从原件复现出台账记的 sha256」那条路，
   不是随手截一段。
3. 语料不进 git（[[corpus-lives-outside-git-verify-the-pointers]]），落账要连 manifest 指针一起做。

**解冻条件（写死，供下一位接手）**：把 5–70% 那段拉丁书信按配方切出来、
逐段核归属、连 sha256 一起写进 `source-ledger.jsonl` 与 `_fetch-manifest.json`；
届时 `conversations` = 2 部独立作品，`lanes = 3` 且**不是纸面道**。

## 复现

```bash
python3 _ledgers/_pipeline/fetch_kramerius.py --host kramerius5.nkp.cz \
  --query 'dc.creator:Komensk* AND fedora.model:monograph AND datum_begin:[* TO 1930] AND dostupnost:public' \
  --rows 10 --list
```

## ★★ 第二部取回了，**但一个字都用不了**

    PID     uuid:0a2b2630-894d-11dd-9988-000d606f5dc6
    题名    J.A. Komenského Modlitby křesťanské（1882）  ← expression 道的候选
    页      **240 页全部有字、0 页空**｜57,182 词｜584,217 字节

看计数比第一部还健康。打开一读是**逐字母加空格 ＋ 变音符全坏**：

    J .   A .   K O M E N S K � H O
    M O D L I T B Y   K XE S dA N S K � ,   t o t i ~

全文 **U+FFFD 17,136 个**（每千字 31.2），四位年份 **一个都找不到**
（`1882` 被 OCR 成 `i S S a`）。[[aggregator-ocr-can-be-silently-broken]]

### 判别式：**「≥2 个连续字母的词」占 token 的比例**

| | token | 连续字母词占比 | U+FFFD |
|---|---:|---:|---:|
| 1892 Korrespondence | 143,711 | **0.9256** | 0 |
| 1882 Modlitby | 57,182 | **0.0000** | 17,136 |

两侧之间是空的 ⇒ 门放 **0.50**，余量都极大。已写进 `fetch_kramerius.py`：
每份 manifest 记 `letter_run_ratio` / `replacement_chars` / `ocr_verdict`，
打印时直接标「**乱码，不许落账**」。自测 12 条全绿（正反例逐字取自这两份）。

### ★★★ 我第一个想用的判别式，方向是反的

「平均 token 长度」：**坏的 8.61 > 好的 5.60** —— 坏的看上去「词更长＝更像正文」。
**两份都跑了才看见。** 只跑一份，任何判别式都会自洽。
[[my-diagnostics-manufacture-false-leads]]
★ 这条**没有写成自测断言**：它是整份文件的统计，而自测里只有一小段摘录，
  摘录复现不出那个形状；把夹具改到能过就等于编一个假现象。
  [[fixtures-cleaner-than-the-real-thing]]

## 对 Comenius 的净影响（更新）

- `expression` 道：**仍然是空的** —— 唯一候选的 OCR 坏了，本机换不出好版本。
- 因此 quick 的 3 道只能是 **writings ＋ external ＋ conversations**，
  而 conversations 要靠 1892 那卷切片后与 1898 那卷凑成 **2 部独立作品**。
- ⇒ 解冻条件不变，仍是「切片 ＋ 逐段核归属 ＋ 落 sha256」。

## ★★★ 归属实测：**这卷里有一大半不是他写的，而编者的脚注正好能判**

拉丁段（5–70%，**616,306 字／92,056 词**）逐项数：

| 信号 | 数量 | 说明 |
|---|---:|---|
| 独立成行的署名 `Comenius.` | **7** | 他签的信 |
| 结尾套语（`observantissimus` 等） | 23 | 书信体，不分方向 |
| `Ad <某人>.` 式抬头 | 9 | `Ad Patronum.`×6、`Ad Mochingerum.`、`Ad Niclassium.`、`Ad Maecenatem.` |

通信对方在拉丁段的出现次数（**对方 ≠ 作者**）：
`de Geer` **44**、`Hartlib` **43**（另 `Hartlibius` 6）、`Wolzogen` **23**、
`Figulus` 9、`Mochinger` 4、`Ravius` 3、`Rulitius` 1
—— 全是 Comenius 真实的通信人（Samuel Hartlib、他的赞助人 Louis de Geer、
Ludwig von Wolzogen、女婿 Petr Figulus），**这卷确实是他的往还**。

### ★★ 决定性证据在 Patera 的**捷克文脚注**里

拉丁段含 `Komensk*` 的行 **62** 行，全是编者脚注，原样例如：

    * Psáno rukou Komenského.                          ← 此信为他手书
    * Koncept vlastnoruční Komenského na ⅔ listu…      ← 他的亲笔草稿
    * Po straně připsal Komenský: Finspongam.          ← **他在别人来信的页边批注**
    * Po straně od Komenského připsáno: Obtuli Januam R.
    ** Atrium intimum quid? (Rovněž připsáno od Komenského.)

「**Po straně připsal Komenský**」（他在页边批注）反复出现
⇒ 这一批是**他收到的信**，他只在边上批了几个字。
把整卷判成 `HIS-OWN` 就是 [[related-to-him-is-not-written-by-him]]
（Liebig 那次混进 9 份，一手占比 0.7419 → 0.5192），
也正是 [[gates-count-sources-not-voice]] 的形状：
三道门全过，而 17 万字里他自己的话只有 15 句。

### 因此解冻条件再细化一格（**可执行，不是态度**）

不是「把 5–70% 整段切下来」，而是：
**按 Patera 的脚注逐信定方向** —— `Psáno rukou Komenského` / `Koncept vlastnoruční`
判 `HIS-OWN`；`Po straně připsal Komenský` 判**他收到的信**（对方是作者，
只有那几个批注词是他的）。切片配方要能从原件复现出台账记的 sha256。

★ 本会话**没有做这一步**，因为它需要逐信读脚注、不是正则能收干净的
（62 行脚注对应的信数还没数清）。**明说未做，不写成「已核」。**

## ★★★ 逐封信数完了：**117 封，其中至少 10 封连他都不在场**

拉丁段里独立成行的罗马数字编号 ＝ 一封信，共 **117** 封。
逐封取紧随其后的抬头行，归类：

| | 封数 | 判据 |
|---|---:|---|
| **他发出** | **67** | `Ad <人名>`（`Ad eundem.`／`Ad D. Mochingerum`／`Ad illustrissimum D D. Palatinum Belzensem` …） |
| 别人写给他 | 1 | `Epistola M. Mersenni ad J. A. Comenium.` |
| 方向不明（已全部原样列出） | 49 | 见下 |

### 那 49 条读下来，**三类**

① **仍是他发出的**（抬头换了写法）：`Ex literis ad dominum Hottonum.`（×3）、
   `Ex literis ad dominum Joh. Loccenium`、`Ex epistola ad d. d. Zb. Goray`、
   `Domino Ludovico de Geer.`、`Domino Joh. Wolzogen.`、`D. d. Baroni Sadovio.`、
   `Bratru Chodniciovi.`、`Ex literis J. Comenii ad N. Arnoldům.`、
   `Responsum ad Susannam Lorántfy.`、`Já, Jan A. Komenský, zanechávám po sobě…`
② **★★ 他根本不是当事人的**（收信人与写信人**都不是他**）：
   `MR Pell to Mr. Hartlib.` ＋ `Mr. Hartlib to Mr. Pell.` **×5**、
   `Ex literis P. Figuli ad Nicolaum Arnoldům`、
   `Ex responso S. Maresii Nikolao Arnoldo`、
   `Literae Seniorum ad Susanna Lorántfy`、`Susanna Lorántfy, …` ×3（她署名的文书）
   ⇒ **至少 10 封**，收录理由是「谈到了他」。
③ 只有问候语开头、抬头判不出方向的：`Gratiam et pacem !`、`Salutem et observantiam !`、
   `Reverende Vir!`、`Pacem Jesu Christi!` 等。

### 结论

**这一卷整卷判 `HIS-OWN` 是错的** —— 里面既有他收到的信，也有
**Hartlib 与 Pell 之间的往来**（两头都不是他）。
[[related-to-him-is-not-written-by-him]]｜[[creator-field-is-not-authorship]]

**可执行的解冻路径（已量到可以照做的粒度）**：按 117 个罗马数字编号切段 →
抬头形如 `Ad …`／`Ex literis ad …`／`Domino …`／`Ex literis J. Comenii ad …` 的判 `HIS-OWN`（**67 ＋ ①**）→
`X to Y`／`Epistola X ad Comenium`／`Literae … ad …` 的判 `OTHER`（**②**）→
剩下只有问候语的**逐封打开读**（**③**）→ 每段落 sha256 与配方。

### ★ 顺带：同一个正则我今天写窄了**三次**

`^Ad\s+[A-Z][a-zé]+\.?$` → 漏掉 `Ad eundem.`（小写）与 `Ad.`（带点）与多词抬头；
第一次报 9 条、第二次 35 条、第三次 67 条 —— **同一份文件，三个数**。
[[the-comment-states-the-rule-the-code-narrows-it]]｜[[my-checkers-are-mis-cut-six-times-in-one-day]]
★ 报数之前先把命中**全部原样打出来读**，是这三次里唯一每次都救了我的动作。

### ★ 试过第二把尺子（信末署名），**比抬头差，记下来省下一次重试**

按同样的 117 段切，取每封**末 14 行**找署名：

    末尾无署名（要读）   **69**    ← Patera 大量收的是**摘录**，结尾就是 `etc. Vale.`
    末尾有他的署名         31
    末尾有别人的名字       12    ← 其中有误报：`dominus Wolzogen, cum generosis…` 是**正文里提到**，不是署名
    两者都有（要读）        5

⇒ **抬头 67 判得出、署名只有 31**，且署名那一侧还带正文误报。
**同一批信、两把尺子、两个答案 —— 用抬头，不用署名。**
[[two-checkers-same-text-different-rules]]

## ★★★ 切段器写完并跑通了：**121 封，他自己占 81.7%**

`_ledgers/_pipeline/slice_letter_volume.py`（自测 **35 条全绿**，正反例逐字取自本卷真抬头）。

    取全文 5%–70% 段（616,306 字）→ **切出 121 封**
      HIS-OWN  **88** 封｜**75,065 词（81.7%）**
      OTHER     16 封｜ 6,416 词（ 7.0%）
      **?（要人读）17** 封｜10,361 词（11.3%）
    产物：121 个 `<罗马数字>.txt` ＋ `_slices.json`（逐封 sha256 ＋ 配方）

**OTHER 16 封逐条列出来读过**，无一误判：`Mr. Hartlib to Mr. Pell.` ×6、
`MR Pell to Mr. Hartlib.`、`Epistola M. Mersenni ad J. A. Comenium.`、
`Fragmentum epistolae Joh. Bythneri ad J. Comenium.`、
`Ex literis P. Figuli ad Nicolaum Arnoldům`、`Ex responso S. Maresii Nikolao Arnoldo`、
`Literae Seniorum ad Susanna Lorántfy`、Lorántfy 自己署名的文书 ×3、
`…clarissime Domine Comeni…`（抬头在称呼他）。

⇒ **就算 17 封 `?` 全不是他**，仍有 **75,065 词**他自己的书信 —— `conversations` 道
够得着，且与 1898 那卷是两部独立作品（Jaccard 0.0004）。

### ★★ 订正：不是 117 封，是 **121 封**

前一节写「117 封」，用的是 `[IVXLC]{1,7}`；切段器用 `[IVXLCDM]{1,8}`，
多认出 `CLXXVIII` 这类**八位罗马数字**。**同一份文件，两个数，以 121 为准。**
★ 今天这是**第四次**同一个病：抬头正则 9 → 35 → 67，编号正则 117 → 121。
[[the-comment-states-the-rule-the-code-narrows-it]]

### 自测里当场红掉的两条（**没让它跑到数据上**）

- `Nobüissimo et strenuo domino Johanni a Wolzogen.` —— OCR 把 `Nobilissimo` 出成
  **`Nobüissimo`**（i→ü），我写死的 `Nobi{1,2}lissim\w+` 落空。
  **锚点里的每一个字母都可能被 OCR 打坏** ⇒ 改成「开头 40 字内出现与格 `domino`」。
- `Fragmentum epistolae Joh. Bythneri ad J. Comenium.` —— 我把首字母缩写写死成
  `(?:J\.?\s*A\.?\s*)?`，遇到只有 `J.` 的当场判不出 ⇒ 改成 `(?:[A-Z]\.?\s*){0,3}`。

★ 另有一条是**读那 17 条 `?` 时逐条看出来的**，不是又想了一遍正则：
`Copia epistolae ad r. d. Ernestům Andreae` 是「致某某的信的抄件」，仍是他发出的
⇒ 补进规则后 `?` 18 → 17、HIS-OWN 87 → 88。

### 还没做的（**明说未做**）

- 那 **17 封 `?`** 没有逐封读（只有问候语开头，抬头判不出方向）；
- **一份都没有进工作区** —— 落账要连 manifest 指针、`rights_basis`、`locator` 一起做，
  且语料不进 git（[[corpus-lives-outside-git-verify-the-pointers]]）。
