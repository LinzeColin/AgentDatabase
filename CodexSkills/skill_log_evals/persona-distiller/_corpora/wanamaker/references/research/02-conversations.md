# Conversations and interviews

## Scope and assigned sources

**本道无独立 train 源。** 台账里没有任何一份属于 conversations 维度的文献（source-ledger 的 `dimensions` 全部落在 writings/expression/timeline）。本道不产出"独立对话记录"；下面如实记录**间接提取**的口头/对话性声口：语料中最近似"对话/口头交流"的是 expression 道的两篇**口头发言记录**——`src-4e53b2952a15`（1914 年对通道经理的讲话，属"对内讲话+征询意见"的半对话体裁）与 `src-2f57e8856a02`（1912 年 Taft 献词的典礼发言）。这两份均在 train split 内，可安全引用；但它们**不是**一对一访谈，引用须带"讲话记录"而非"对话"的声口标注。

★ 本节由台账机械导出（`emit_lane_scope.py`）**不适用**（本道 0 源）；以下内容由 expression 道间接提取。

## Source-linked observations

### ① 对通道经理的讲话（1914，src-4e53b2952a15）——半对话体：征询式开场 + 反问 + 现场轶事

`src-4e53b2952a15` 虽题名 "Address"，实为对内座谈记录——开场即把话语权让给听众，用反问推进：

> it is not necessary to have a long discussion. It would be very much more interesting to all of us if you would tell me what is on your minds.
<!-- src-4e53b2952a15 -->

> Suppose we commence on the 15th of June next year and run until the 15th of September; that would be three months. Why not?
<!-- src-4e53b2952a15 -->

- **现场对话片段（与清洁工的即兴对话，OCR 损伤较重，只取可核短句）**：

> "Well, I see you're back at your old job again." "Yes, sah!"
<!-- src-4e53b2952a15 -->

（续句大意"我在想您是否每天都要擦一遍、昨天擦干净了今天又是新的脏——是的，先生，这是每天都要重做的新事"——语料 `something ew`、`what /e do today` 缺首字母（ew=new、/e=we），无法逐字成句，改述。）

- **"问听众要主意"的收尾**（改述）：大意"我还想做些别的事，希望你们给我建议，把脑子动起来"——语料 `ust`=just 缺字，改述衔接。

⇒ 声口：**对"自己人"的商量式讲话**——不端着、承认不完美、当场讲轶事、把决定开放给听众。这是全库最接近"对话"的文本，但仍是单向发言+修辞性征询，不是问答记录。

### ② Taft 献词（1912，src-2f57e8856a02）——典礼声口对照

`src-2f57e8856a02` 是向总统致辞的正式讲稿，声口与①判若两人：全篇第一人称致敬（`His honor who presides here to-day in his official capadty is also here as Rudolph Blankenburg, an old merchant of Philadelphia and my personal friend of upward of thirty years.`，`capadty`=capacity 讹形照录），几乎无问答、无轶事，只有颂扬与政策呼吁。**两卷并置可见其声口随场合切换**：对雇员拉家常、对总统唱高调。

## Candidate Claims

- C-C1（lineage）：本道无独立 conversations train 源；口头声口只能间接取自 expression 道的两篇讲话记录（src-4e53b2952a15 半对话体、src-2f57e8856a02 典礼体）。
- C-C2（expression）：对雇员=商量/征询/拉家常，对总统=颂扬/庄重（src-4e53b2952a15 "It would be very much more interesting to all of us if you would tell me what is on your minds."；src-2f57e8856a02 致敬开场，改述）。

## Contradictions and alternative explanations

- **"商量式"不等于"真商量"**：Aisle Managers 的征询（"请你们告诉我你们在想什么"）与"我已经定下周六休息方案"并存——修辞性征询在先、决定已定在后；不能据此断言他是"民主决策"型管理者。
- **声口随场合是策略还是本性**：对雇员拉家常、对总统颂扬，可能都是"得体"的场合管理，未必反映真实性格——下游建模须谨慎，不以单一场合声口推定全人。

## Unknowns and source gaps

- 全库**没有任何一对一访谈、书信往来、会议记录**类文献；"对话中的 Wanamaker"只能由两篇讲话记录间接逼近。
- Aisle Managers 讲话的"现场问答"部分（若有）未单独标注：该记录只有 Wanamaker 单方讲话，听众回应未录。
- Taft 献词为正式讲稿（可能经润色），非即席对话。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- C-C1 作为 lineage 元断言：说明 conversations 道由 expression 道间接支撑，下游不得声称有"对话记录"证据。
- C-C2 供 persona 声口建模：区分"对内商量式"与"对外典礼式"两个寄存器。

## 这一道给下游的东西

- **两个口头寄存器样例**：商量式（"tell me what is on your minds"、轶事开场）与典礼式（对总统的致敬）——persona 文档的沟通风格素材。
- **改述纪律**：Aisle Managers 卷 OCR 损伤重，凡缺首字母句（`something ew`、`/e do today`）一律改述，不补字。

## 未做完 / 未核

- 未从 train 语料其他卷（Primer 内的 Lincoln 轶事对话、Williamson 传内的引语）反向排查"对话性内容"——那些是被引用的他人对话，非 Wanamaker 的对话，故不归本道。
- 两篇讲话记录是否曾发表于报刊/是否有第二手转录，本语料无法核。