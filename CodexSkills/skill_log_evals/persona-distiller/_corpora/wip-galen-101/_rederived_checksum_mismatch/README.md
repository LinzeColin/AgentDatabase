# 这 55 份**不是**账本attest 的那份字节——所以它们不在 `raw/` 里

2026-08-04。Galen #101 的账本有 60 条，`raw/` 里只有 9 份 .txt（判据
`check_corpus_presence.py` 报「缺 51」，逐条比对是 57 条对不上文件）。

缺的 55 条全部指向同一个来源：`https://github.com/galenus-verbatim/galenus_cts`
（TEI-XML，CTS `urn:cts:greekLit:tlg0057`）。那个仓库的副本还在本次会话的
scratchpad 里，于是我把 TEI 正文转成纯文本，写回账本记的 `local_path`。

**55 份的 sha256 与账本记录的 `checksum` 无一相同。**

```
galen_tlg001_grc.txt: 账本 e8c851e990d2… vs 现盘 919d51eecb6d…
galen_tlg002_grc.txt: 账本 ebf8865c0051… vs 现盘 455fb20ae64b…
galen_tlg003_grc.txt: 账本 fea0902dd7f3… vs 现盘 b806d47f8812…
```

（账本的 `source_id` 就是 `src-<checksum 前 12 位>`，两者互证，
说明账本记的确实是当初入库那份文件的哈希。）

差异的原因是**抽取方式不同**：我只取 `<text>` 丢掉 `teiHeader`，
并做了空白归并；当初入库用的是别的做法，具体是哪一种已不可考。

## 为什么撤下来而不是留在 `raw/`

留在那里，`check_corpus_presence` 会变绿（它只数份数），
而引文核查、`primary_ratio`、覆盖率会**对着另一份文本**算。

台账里已经记过三次「判据绿了但指错了文件」。
**这一次是我自己造的，所以立刻撤下。**

## 它们仍然有用

内容确实是 Galen 的希腊文原著，来源可查。
将来若要重蒸 Galen（任务 #29），**正确做法是找回当初的抽取脚本、
或者重新入库并让账本记录新的校验和**——
而不是把这批文件塞回 `raw/` 假装它们是原来那批。

## 由此落成的判据

`check_corpus_presence.py` 原本**只数份数不验校验和**——
55 份错文件能让它变绿。v0.0.0.64 加了逐份校验和核对。

---

## ★ 2026-08-04 后记：这 55 份已被真件取代，**但不删，留作记录**

清 C 档前逐目录核校验和，在 `scratchpad/pd-work/galen-corpus/` 里找到了
**账本 attest 的那一批**，60 条全部按 sha256 对上并已还原。
`check_corpus_presence` 现在：`wip-galen-101　60 / 68 / 指得到 60`。

**这 55 份重转件留在这里，是因为它记着一件事**：
我当时把它们写进账本记的 `local_path`，份数当场 9 → 64、**判据变绿**，
而 55 份的 sha256 与账本无一相同。
**若那天没有逐份核校验和，这批错文件会一直冒充语料，而所有判据都会说「齐」。**
