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
