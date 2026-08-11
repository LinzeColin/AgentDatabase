# Conversations and interviews

## Scope and assigned sources

**本道分到 1 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-2c00f19a2df5` | 1773 | P1 | A Reply to Dr. Priestley's Remarks on the Fourth Volume of…adelphia, M DCC LXXIII [1773] |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

★★ **本道不含任何我从正文提取的逐字引文**：本道分到的印本，长 s 被 OCR 读成 `f`（讹字率见 `metrics.longs_corruption`），**取不出可核的逐字串**。下面凡带反引号的字符串，都是**台账 `attribution` 字段里抓源方逐字照录并硬校验过的扉页／首行**，已标明出处；**不是我自己从正文里截的**。一个字都没有改。

1. **这一份是一场印出来的往复里的一方。** `src-2c00f19a2df5` 是他对 Priestley
   就《释义》第四卷所提意见的答复；同一年的合刊（见 04 道）把三方文字排在一起，
   顺序是「对方的意见 → 他的答复 → 对方的再答」。**对造是谁、争的是哪一卷，都是定死的。**

2. **他答复时不署名，靠认领作品来定身份。** 台账照录的分辑扉页作
   `B Y T H E AUTHOR OF THE COMMENTARIES`——**印本上没有他的名字**；
   正文起首照录 `his Remarks on ſome paragraphs in the fourth volume of my Com- mentaries,
   I find my ielf called upon`，以第一人称认领《释义》。

3. **他给答复落了地点与日期**：台账照录文末作 `IVaUuigford^ Sep. 2…`（`IVaUuigford` 为
   OCR 讹形，指 Wallingford）。→ 这是一次**具名到地点与日期**的公开答复，不是匿名投书。


## Candidate Claims

- **clm-bs-dial-01｜与人争论时，他认领的是作品而不是名字：不署名，但第一人称说「我的《释义》」。**
  证据：`src-2c00f19a2df5` 台账照录的分辑扉页与正文首行。
- **clm-bs-dial-02｜争点被限定在具体一卷、具体段落上**（对方针对第四卷若干段，他就答那几段）。
  证据：同上扉页 `REMARKS ON THE FOURTH VOLUME OF THE COMMENTARIES`。


## Contradictions and alternative explanations

- **「不署名」在 18 世纪的论战文里很常见**，未必是他个人的做法。
  **本道只有他这一份**，没有同代其他论战者的对照，**分不开「他的习惯」与「当时的体例」**。
- `src-2c00f19a2df5` 是从 04 道那份合刊里**逐字截出的子集**（台账已声明 `derived_from`，
  重叠 containment 1.0）。**它与那份合刊不构成两处独立证据。**


## Unknowns and source gaps

- 本道印本长 s 讹字，**取不出可核的逐字引文**；上面的字符串全部来自台账照录，已标明。
- 他在这场往复里**改没改口、退没退让**，本道判不了——只有他这一方的一篇。


## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

- 用例方向：`case-contrast-*`——有人指名道姓反对他时，他答哪一段、不答哪一段。

## Handoff to adjudication

- 两条候选断言均带 source_id；**证据是台账照录的扉页与首行，不是正文提取**，已在正文标明。
- ★ `clm-bs-dial-01` 的「不署名」一项**不得写成他的个人特征**——本道分不开体例与习惯。

