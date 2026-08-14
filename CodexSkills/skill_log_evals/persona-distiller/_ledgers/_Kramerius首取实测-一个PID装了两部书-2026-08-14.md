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
