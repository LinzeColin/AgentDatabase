# Conversations and interviews

## Scope and assigned sources

**本道无独立 train 源**：台账里没有任何 `split == train` 的对话/访谈类文献（`dimensions` 无 conversations 项）。语料 8 份全是 Carnegie 本人的著作/演讲/自传，**没有访谈录、书信集或记者问答**。

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### ① 道内无直接观察——如实说明

- 本道**没有可以逐字核的对话/访谈文献**，因此不设"逐份引文观察"。
- 但对话性材料**可从其他道间接提取**，且明确注明出处与声口：

1. **自传（06 道，src-f942339e1cea）里的复述对话**：Carnegie 与德国皇帝威廉二世的见面（1907 基尔港），他当面说 "No, Your Majesty, I do not like kings, but I do like a man behind a king when I find him."（改述句意，引文见 06 道）——这是自传转述的私人交谈，属"他笔下再现的对话"，不是访谈实录。
2. **Stanton 纪念演讲（03 道，src-5a457dfece71）里的"引语转述"**：他复述 Stanton 在内阁说的话（"its surrender by the Government would be a crime equal to that of Arnold"）、复述林肯的话（"Yes, the Army will move now, even if it move to the devil"）、复述 Grant 的信件——这些是演讲里**他转述的他人话语**，声口归他人、由 Carnegie 担保。
3. **自传里的"电报/信函往来"**：1869 年他匿名电告英国阁员 John Bright "First and best service possible for Monarch, bringing home body Peabody"（引文见 06 道）——一次以电报为媒介的"准对话"，可见其早期行事风格。
4. **《League of Peace》（03 道）的林肯轶事**：他讲林肯年轻时在密西西比河奴隶市场立誓 "If ever I get a chance, I shall hit this accursed thing hard"（改述，引文见 03 道）——用"故事里的对话"做道德动员。

⇒ 结论：本道的"对话声口"只能靠 03/06 道转述的引语间接重建，**无法独立成链**；任何"他说过 X"的对话式断言，须回落到 03/06 道的一手引文并标注转述层。

## Candidate Claims

- 本道**无独立候选断言**（无独立 train 源，无法形成"对话道专属"的 claims）。
- 可移交跨道：自传转述的"我不喜欢国王、但喜欢国王身后的人"（06 道）、Stanton 演讲复述的内阁对峙（03 道）——这类**他人话语的转述方式本身**是表达特征（他爱用戏剧化引语+林肯/华莱士式比喻），已由 03/06 道承接，本道不重复计。

## Contradictions and alternative explanations

- **"转述对话"≠"逐字实录"**：自传与演讲里再现的对话（与皇帝、与林肯、与 Grant）都是**多年后凭记忆重写**，非访谈笔录；逐字可靠性存疑，只能当"他愿意怎样呈现那次交谈"的证据，不能当当时逐字的证据。
- **"匿名电报"与"公开演讲"的声口差**：1869 年匿名发报（不出声地做一件机灵事）与 1906 公开演讲（面向圣安德鲁斯学生喊话）是两种极端的表达姿态——前者藏名、后者扬名；本道无源，只能由 03/06 道各自呈现。

## Unknowns and source gaps

- **语料无任何访谈/书信/记者问答**：Carnegie 一生大量接受报刊采访（史实层面众所周知），但 train 语料里一份都没有；任何"据某次访谈他说过"的断言在本库均无一手依据。
- **自传里的书信/电报只选编了少量**：他一生书信极多，但语料未收书信集；只有自传里零星转述（给 Bright、给 Cremer、Grant 给总统的信等）。
- 若下游需要"访谈声口"，须另案补语料（如当时报刊访谈的 PD 文本），本道在现状下无路可走。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- 本道**不产 claims、不出题**（无独立 train 源，无从设题；道稿末节的"保留题占位"系模板要求，本道不适用）。
- 对话性材料一律**借道 03/06**：由 expression 道收"演讲中复述他人话语"的表达特征，由 timeline 道收"自传转述的交谈与书信"的事实层；合成时注意把"转述"标为二手声口。

## 这一道给下游的东西

- 明确的**道空声明**：conversations 无 train 源，建模时不得假装有"访谈体"材料。
- 三个可借的间接入口：自传转述对话（皇帝/林肯）、演讲复述内阁话语（Stanton）、自述书信往来（Bright/Cremer）——都在 03/06 道。

## 未做完 / 未核

- 本道**全部未做**（无源可做），非"未完成"而是"不适用"。
- 未核：自传与演讲里转述的对话在史实上的真实性（如皇帝见面的具体日期、Bright 回应的措辞）——超出语料核验范围，交 06 道按一手转述对待即可。
