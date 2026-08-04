# Research and source completeness

## Six base lanes

1. Systematic outputs: books, papers, essays, courses, code, patents, formal artifacts.
2. Conversations under pressure: interviews, debates, Q&A, hearings, conflicts.
3. Expression and interaction: rhetoric, editing, collaboration, live response.
4. External triangulation: colleagues, competitors, criticism, biography, peer review.
5. Decisions/actions/outcomes: what was chosen, rejected, delayed, reversed, failed and learned.
6. Timeline and facets: period, role, institution, incentives and changed beliefs.

Each identity adds its own high-value sources from `registries/identity-families.json`.

## Source records

Record source ID, canonical origin, URL/local locator, author, publication/event date, retrieval date, language, rights/authorization, source tier, role/period, lane, content hash, near-duplicate cluster, transcript method, redaction, and injection flags.

## Claim graph

A Claim stores statement, epistemic type, supporting and counter sources, independent origin clusters, contexts, role/period, confidence, applicability, falsifiers, alternatives and supersession. Citation count is not source independence.

## Completeness and stopping

Use a coverage cube across identity × role × period × lane × source family × language × decision context × success/failure. After the initial pass, search only the critical gaps. Stop when two successive gap-driven rounds add no high-impact Claim and every critical cell is evidenced or explicitly unresolved. Report what could not be accessed; never claim literal global exhaustiveness.

## 分一手还是三方：**看署名，不要看标题**（2026-08-05 实测）

派抓源指令时我写过一句「标题里有他的名字**通常**意味着是别人在写他」。
**「通常」是错的**，当场用全库 1,278 条来源台账量了一遍：

| 条件 | 实际是三方(S2) |
|---|---|
| 标题含本人姓名 | **32.3%**（30 / 93） |
| 全库基准率 | 6.7%（85 / 1,278） |

**近三分之二仍是一手**——63 条 P1/S1 的标题里就带着他自己的名字
（`fam-barton-…`、`fam-hannah-blackwell-母` 之类的命名约定占了不少）。

**口径**：
- 「标题含其名」是**弱信号**，约 5 倍提示强度——**值得多看一眼，不足以据此跳过。**
- **唯一可靠的判据是署名本身**：正文/扉页署他为作者 → P1；
  编辑部或他人署名而正文在写他 → S2；署名看不清 → `U` / `ATTRIBUTION-UNCLEAR`，**不许猜**。

★ 这条写进来是因为**我先把弱信号说成了规则，再去量才发现说错了**。
弱信号当规则用，会让抓源方静默漏掉真一手，而漏掉的东西不会出现在任何门的报告里。
