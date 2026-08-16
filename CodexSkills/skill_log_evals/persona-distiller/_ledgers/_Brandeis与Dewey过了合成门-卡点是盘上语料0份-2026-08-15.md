# Brandeis 与 Dewey 过了合成门 —— 卡点从来不是门，是**盘上语料 0 份**

**2026-08-15**｜起因：队列 `NEXT: None`，而「已做未出货」11 人里有 3 个**不等判分**
（Brandeis、Marshall、Dewey）。Marshall 已按 ㊺ 结案，剩两个可以直接量。

## 一、跑合成门，发现真卡点

记录里写的是「Brandeis 合成门 8 条 / Dewey 2 条」。跑下来第一条错是：

    ✗ 找不到正文的源 38 条 —— 无法判定，**不算通过**

盘上一数：**Brandeis 台账 38 行、正文 0 份；Dewey 39 行、正文 0 份**
（`raw/` 里只剩 `_ids-rebuild.txt` 与 `_ids.txt` 两个指针文件）。
语料按裁定不进 git，而这两个工作区的正文只存在过会话临时目录里。

## 二、按指针重建，拿**外部基准**核验

指针齐全且每份带 sha256。`fetch_ia.py --ids-file _ids-rebuild.txt --skip-existing`：

| | 请求 | 取回 | 逐字节相同 |
|---|---:|---:|---:|
| Brandeis | 38 | 38 | **38 / 38** |
| Dewey | 39 | 39 | **39 / 39** |

★ **基准是重抓之前快照出去的 manifest，不是重抓之后的那一份。**
`fetch_ia.py` 会用新算的 sha256 覆盖被重抓那些 id 的记录 —— 拿它比就是
**同源自证**。快照先做，才叫核验。[[same-source-self-attestation]]

★ Dewey 还差一步：`raw/jstor-1640600-dewey-address.txt` 是**切片**
（《Science》1915-01-29 整期里他那一篇），**重抓只拿得回整期，拿不回切片**。
仓里早有 `rebuild_derived_slices.py` 就是为这条源写的，`--check` 复现、sha256 对上、落盘。
[[three-times-in-one-day-i-rediscovered-what-the-repo-already-had]]

## 三、结果

| | 合成门 | 剩余项 |
|---|---|---|
| **Brandeis #172** | **rc=0、passed=True** | claim.orphan 2（既有）＋ corpus.unexamined-band 1 ＋ rubric-demands-frame-break 1，全是 warning |
| **John Dewey #190** | **rc=0、passed=True** | corpus.title-is-just-the-filename 1 ＋ source.year-straddles-pd-cutoff 1，全是 warning |

跑门时产物**一字未动**（跑前跑后逐文件哈希相同；不加 `--write-report` 是只读的）。

## ★★ 四、查出我自己的一个系统性做法：**加断言把门凑过去，没让它进产物**

`claim.orphan` 报「active Claim clm-… is not rendered in any core artifact」：

| 人 | orphan | 其中来自**我这场返工提交**的 |
|---|---:|---|
| Brandeis | 4 | **2**（`404016fed` 新增第二条 mental-model、`1f6606f7a` 第三条 heuristic）|
| Dewey | 4 | **4**（`3362d128b` 两条 heuristic、`701999a10` 第三条、`b43c57aac` 第二条 mental model）|

返工报「Brandeis 4→0、Dewey 2→0」，**而其中 6 条只活在 `evidence/claims.jsonl` 里，
读者打开产物一个字都看不到**。门数的是 JSON 里的断言条数，读者撞到的是散文。
[[gates-cover-json-not-the-prose-users-read]]｜[[read-the-artifact-as-its-actual-reader]]

已逐条渲染进产物（引文逐字取自断言本身，未新造）：
Brandeis `cognitive-os.md` +1、`decision-policy.md` +1；
Dewey `cognitive-os.md` +1、`decision-policy.md` +3。
⇒ **我造的 6 条 orphan 全部清零**；Brandeis 剩的 2 条是台账里记着的既有项。

## ★ 五、顺带修好 `fetch_ia.py` 的一个汇总回归

Dewey 重建后 manifest 出现：`剔除: 1` → **字段整个消失**，`失败: 3 → 4`。
记录里的 `status="剔除"` 还在（没坏），坏的是汇总 —— 它把**人用 `drop_source.sh`
有意剔掉的一份**折进了「抓取失败」。读的人会去重抓一份本来就不该在的源。

改成从 status 现算，`剔除` 单列、不进 `失败`。复跑：`剔除 1｜失败 3`，与记录对上。
[[empty-default-swallows-unknown]]

（`总词数 3,199,599 → 3,061,536` 那 138,063 词的差是**对的**：旧值把已剔除那份算了进去。）

## 六、这两人现在卡在哪

**不是合成门了。** 两人都进入阶段 5 判分队列 —— 而判分要两个互相独立的空白会话，
本会话 harness 不许派子代理，**我做不了**。
⇒ 「已做未出货」11 人里，8 人等判分、Marshall 已结案、
**Brandeis 与 Dewey 从「卡在合成门」变成「等判分」**。
