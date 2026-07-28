# 产物体检工具（2026-07-28 立，Jesse Vincent #94 那轮长出来的）

官方 `quality_check.py` 三阶段全绿**不代表产物没有事实错误**。
Vincent 在三门全绿的状态下被评委抓出三类错误，每类平均散布在 **4 个落点**，
其中只有 1–2 个在评委看得到的用例里——**产物文档没有评委**。

## 入口

```bash
python3 verify_product.py --workspace <target> \
    --cache <语料目录...> [--rules <人物专属语义规则.json>] [--extra <judge payload.json>]
```

它会**先跑三个硬门检查器的负对照，再跑产物检查**。负对照不过，后面所有「全绿」都不作数。

## 各件

| 脚本 | 拦什么 | 负对照 |
|---|---|---|
| `check_claim_coverage.py` | 装饰性引用：引了源，但源里没有这个事实 | 5 向 |
| `check_quote_integrity.py` | 伪造引文：引号里的英文原句语料里没有 | 4 类伪造全抓、0 误报 |
| `check_semantic_residue.py` | 订正残留：同一个错换个措辞又活了 | 双向（抓残留／豁免订正）|
| `check_absence_claims.py` | 无依据的「从未／只有／完全没有」 | 只列不判 |
| `classify_early.py` | 分类表模板：把举例式断言换成按计数穷尽的分类 | 双向核对，无兜底 |

## 三条必读纪律

**一、0 命中不是结论，是「换个方式再查」的信号。**
本库有七次「正则写窄 → 0 命中 → 判定不存在」的记录，
最贵的一次差点划掉语料最厚的候选人。至少两种独立形态的模式都得 0，才可写「不存在」。

**二、检查器必须报「实际检查了几条／共几条」。**
`check_claim_coverage.py` 曾长期报「0/29 通过」，
而实际有 4 条因抽不出关键实体被**静默跳过**——分母是假的，看报告的人看不出来。

**三、没有负对照的检查器，它的「全绿」不构成任何证据。**
只证明脚本跑完了。引文检查器前两版误报率都是 100%，
若照着误报去订正，会把真引文改坏——这已经差点发生过一次（`double- ESC`）。

细节见 `../RUNBOOK.md` 第十六、十七、十八种失败模式。

## `check_holdout_overlap.py` —— holdout ↔ train **内容级**判重（硬门，Robertson #97 新建）

`check_material_split.py` 查的是**成员**（哪个文件在哪个 split），
这一件查的是**内容**。两件都要跑，因为**成员对 ≠ 内容不重合**。

Robertson #97 实测：holdout 里的一份 2019 年 Medium 文章
与 train 里一份 2012 年访谈是**同一篇**（转载），shingle 覆盖率 63%。
文件名年份、URL、域名、source_id 四个维度全都不同，**成员级检查一路绿灯**。

    python3 check_holdout_overlap.py --workspace <target> --cache <corpus dir> [<dir>...]
    python3 check_holdout_overlap.py --self-test

判据是**覆盖率**不是 Jaccard（Jaccard 会被长度差稀释）；
≥0.30 硬失败、0.10–0.30 人工核。
内置两条站点无关的样板过滤（纯数字 shingle 丢弃 + 文档频率过滤），
**不维护站点黑名单**——它自己第一版就因为归档侧栏误报过 37.8%。

**跑的时机：抽完 holdout、写 known 用例之前。**

## `check_anchor_coherence.py` —— 锚点**内容**一致性（只列不判，Robertson #97 新建）

`check_claim_anchors.py` 查引用关系（锚点在不在、有无孤儿幽灵），
这一件查**内容一致**：锚点之后那段正文，讲的还是不是这条断言。

Robertson #97 实测抓到：一条断言按原文订正过（「他从未把两者并置讨论」→
「他一口气把三件事连说」），`claims.jsonl` 改对了，
而渲染它的 `divergence-map.md` 整节还是旧文本——**两处直接互相否定，所有门却都是绿的**。

    python3 check_anchor_coherence.py --workspace <target>
    python3 check_anchor_coherence.py --self-test

判据是**中文字符三元组覆盖率**（断言 ∩ 锚点后 1400 字）。
第一版用「英文引文 + 英文专有名词」当标记，中文正文渲染中文断言时全部误报
（标记是 `New Zealand`、正文写「新西兰」）——**判据用错语言就会把噪声和真错对调**。

**只列不判**：低覆盖有合法情形（指针段、断言几乎全是英文引文）。
但列出的必须逐条看完 —— 那次真错排在最低第三位，
按「都是中英混排噪声」划掉就漏了。

## `check_verbatim_quotes.py` —— 文档层与用例层的逐字引文核查（Robertson #97 新建）

`check_quote_integrity.py` 只扫 `evidence/claims.jsonl`。
而**渲染文档、身份分面、评测用例里的引文一样会伪造**——
此前没有常规检查，每个人物都在临时写脚本。

    python3 check_verbatim_quotes.py --workspace <target> --cache <corpus dir> \
        [--extra judge_payload_x.json ...]

判据是**引号内没有汉字**。这个判据本轮先后错过两版，记着免得再错：
「含 ≥4 个连续拉丁字母」把「Tiger 由他与 Thorpe McKenzie 共同创立」误判成英文引文；
改成「拉丁字符占比 ≥60%」仍误判——专名把短中文句撑到了 73%。
**一段逐字英文引文里不会出现汉字**，这才是干净的维度。
