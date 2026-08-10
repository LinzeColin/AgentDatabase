# decisions 道 —— 演说（元老院／公民大会／法庭）

本道 4 份：反喀提林与土地法演说（`src-0ba7893f2714`）、Philippics 14 篇（`src-1a59d21f7eab`）、
In Verrem 全套（`src-a2c6cff7217a`）、拉丁原文反喀提林第一篇（`src-666ef6034aa2`）。

★ **这一道是本人物第一人称密度最高的一道**：演说里说话的就是他本人，
不像 writings 道那样隔着对话体的代言人（见 01 道的对照表）。

## ★★ 这一道有过一次翻车，记在这里

Philippics 与 In Verrem 第一轮抓到的是 **Perseus 的目录页与分节导航**，
剥标签后只剩 **1,561 词**与 **643 词**，而正文分别在 **10 万**与 **15 万**词量级。
两个页面各 114 KB / 70 KB，**按字节看毫无破绽**。
重抓后实测 **103,626** 与 **195,641** 实词。
→ 判读法：**语料够不够，要数剥完标签的实词，不能数字节。**

## 观察 1：他起诉时，第一步是**解释自己为什么改变惯例**

`src-a2c6cff7217a` @2995，In Verrem 开篇（Divinatio in Caecilium）：

> `I.  IF  any  one  of  you,  0  judges,  or  of  those  who  are  present`
（Bohn 全集卷一 Yonge 译，*Divinatio in Caecilium* 开篇；下一行续 `here,  marvels  perhaps  at  me,`）

★ **照录：本份是双空格版面**。我第一版按单空格引，**那就不是逐字的**——
判据 `lane_quotes` 正是这样把它挑出来的。

**他把听众可能有的疑虑先替他们说出来**，再回答。这与 02 道里"亲属任命时自己先把利害说破"
是同一个动作：**抢在对手之前占住那个最不利的问题**。

★ 同一份 @2771 的前半句 `judges, having to decide on the arguments of the speakers alone, are
forced to guess their way. Cicero carried his point…` —— **那是译者/编者的引言，不是正文**。
同一屏里编者说明与演说正文相接，按偏移量取材必须分开。

## 观察 2：听众呼语是**场所标记**——★ 而它在本语料里带着一个 OCR 陷阱

呼语不是修辞装饰，它区分同一个人在**法庭**与**元老院**面对的不同对象：

| 场合 | 语料里的**逐字**形态 | 出处 |
|---|---|---|
| 法庭 | `0 judges`（@2995：`IF any one of you, 0 judges, or of those who are present here`） | `src-a2c6cff7217a` |
| 元老院 | `0 conscript fathers`（@6705：`BEFORE, 0 conscript fathers, I say those things concerning`） | `src-1a59d21f7eab` |

★★ **`O` 被 OCR 认成了数字 `0`。** 我第一次按 `O judges` / `conscript fathers` 去数，
三份文件**全部零命中**——差点据此写下"本语料没有呼语"。
实际是 132 处 `conscript`（Philippics）、500 处 `judges`（In Verrem）。

→ **下游任何按呼语定位场合的正则，必须写成 `[O0]` 并容忍多余空白**；
只写 `O` 会得到一个干净的零，而零很容易被读成"没有"。
（同族教训见 `regex-must-clear-the-corpus-language`。）

## 观察 3：拉丁那一份在本道里是**真的补进了新东西**

`src-666ef6034aa2`（反喀提林第一篇拉丁原文）与英译件的对应关系**不是**拉英对照——
本道的英译是 Yonge/Bohn 的**单语本**，不含拉丁。
这与 02 道的致阿提库斯正相反（那份因 Loeb 对照本而冗余）。
→ 5 份拉丁原文里，**只有这一份与 `de_oratore_liber1` 真的独立**，其余三份已判为冗余。

## 已知缺口（如实记）

- In Verrem 正文内有一处 `[The rest of this oration is lost.]`（Actio Secunda 卷一末）——
  **那是古写本本身的缺环**，不是下载缺陷；缺环范围未去查证。
- 本道语料为 OCR 文本，已观测到讹字（`OP`←`OF`、`THR`←`THE`、`C2ECILIUS`←`CÆCILIUS`）。
  **下游若要当逐字引文用，必须先核那一处的原字。**
  ★ 抓源时初版校验正则查 Actio Secunda 卷二报 **0 命中**，看着像整卷缺失，
  真因是 OCR 把 `OF` 读成 `OP`——**是判据看不见它，不是语料缺它**。
