# Conversations and interviews

**本路 29 份，但 P1 只有 5 份。**
**前两位人物（#115 Slavyanov、#116 Watson）都死在这一路为 0 上——
她这一路有东西，但「有东西」和「是她的话」是两件事。**

## Scope and assigned sources

train 分割 29 份：**P1 5 份、S1 24 份**。

P1 五份：
- src-0950255a39b2　`rc-in-cuba-1898`（*The Outlook* 1898 年逐问逐答访谈）
- src-150efff3c370　`fam-barton-…-notes-from-clara-barton-during`（1911–12 病中字条）
- src-4b789fe8829a　1870 年日记，**含发出信件的抄件**
- src-8d505b3e1a82　1871–74／1881 日记，含致 Lou 的信抄件
- src-e49658958e9d　1878–80／1882 日记，含信件抄件

**S1 二十四份是 LOC 通信卷，定 S1 不定 P1**：抓源方逐卷实测过，
**来信占压倒多数**（Willard 卷她的落款 0 处、写给她的 22 处）。
**把整卷提成 P1 就是靠技术性做高一手占比，本项目不接受。**

## ★★ Source-linked observations 一：访谈是转述，不是速记 —— src-0950255a39b2

刊头署名 `The Red Cross in Cuba / By Clara Barton / As Interviewed by Elbert F. Baldwin`。
编者说明逐字照录：

> `Miss Clara Barton has been good enough to tell the readers of The Outlook,`
> **`through a member of its editorial staff,`** `some salient facts concerning actual`
> `conditions of distress in Cuba…`
> `the interesting inter-views described in these questions and answers took place`
> `on Wednesday and Thursday of last week at Miss Barton's residence, Glen Echo,`
> `six miles from Washington`

**`through a member of its editorial staff` 这半句是本路最重要的一条限制**：
她的话是**经编辑转述见刊**的，不是逐字速记。
时间地点是确的（上周三、周四，Glen Echo 寓所），**措辞不是**。

**处置**：本份可用于「她当时怎么判断古巴局势」，
**不可用于「她的原话是怎么说的」**——那需要速记稿，而十九世纪末的期刊访谈没有。

她答话的实际形态（同份，照录）：

> `it is not so much from the Spanish soldier. The Spanish can generally control`
> `their soldiers. All the reconcentrados could cultivate much land, still left to them`
> `inside of the trochas and inside of the forts, but as soon as they have got`
> `something raised, in comes the lawless guerrilla and takes it.`

**可注意的一点：她把责任分层，不作笼统谴责**——
先排除西班牙正规军，再指向游击队。这与 01 路里她「交账」式的自我定位一致。

## Source-linked observations 二：三册日记里的信件抄件

src-4b789fe8829a／src-8d505b3e1a82／src-e49658958e9d 的 LOC 卷题
自述含 `includes copies of letters`——**是她发出信件的抄件**，
因此归 `conversations` 而非 `timeline`。
**这是本路仅有的「她主动说给别人听」的成规模材料。**

## Contradictions and alternative explanations

- **信件抄件是她自己抄的，可能与实际寄出稿有出入。** 抄写时的删改无从查证。
- **随行人员日记（S1，`otherdiary-*`）与她本人日记用词重合可达 17%**，
  实测逐字相同句段仅 8/933——**那是同场活动，不是转载**；
  但它一个字都不是她写的，**不许当作她的话**。

## Unknowns and source gaps

- **LOC Letterbooks 52 卷（她发出信件的存底）未取到**：分面统计显示
  该系列命中 "online text" 为 **0**，即**已数字化但只有图像、没有转录**；
  再查时 www.loc.gov 返 Cloudflare 质询，**未绕过**。
  **这是本路最大的缺口，也是本人物一手占比差 0.0078 的最自然补法。**
- **没有速记稿、没有录音。** 凡「她当场原话」类断言，本路给不出证据。

## Proposed Holdout cases

不从本路提取 holdout（P1 仅 5 份，抽走任何一份都会掏空本路）。
现有 holdout 为四册单副本日记，已跑 `check_holdout_overlap`：硬失败 0，
其中 1897 册与随行人员日记的 17.1% 重合已逐条核为「同场不同记」。

## Handoff to adjudication

1. **访谈类材料的引文口径**：可引其判断，**不可称其为原话**——
   须在答案里写明「经编辑转述」。
2. **LOC 通信卷维持 S1**，不因一手占比差 0.0078 而重判。
