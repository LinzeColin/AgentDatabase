# Conversations and interviews

## Scope and assigned sources

**本道分到 8 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-7d22c26873fd` | 1906 | P1 | Briefe |
| `src-e1168364413e` | 1908 | P1 | Vincent van Gogh : Briefe |
| `src-5fb2d553bd1a` | 1911 | P1 | Briefe |
| `src-f5617484c043` | 1912 | P1 | The letters of a post-impressionist; being the familiar co…spondence of Vincent van Gogh |
| `src-5751a200cf57` | 1913 | P1 | The letters of a post-impressionist : being the familiar c…spondence of Vincent van Gogh |
| `src-ac0ac7a914af` | 1913 | P1 | The letters of a post-impressionist; being the familiar co…spondence of Vincent van Gogh |
| `src-eb5be7530935` | 1918 | P1 | Briefe |
| `src-683020755a90` | 1927 | P1 | the letters of vincent van gogh to his brother 1872-1886 |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

- **对话/通信道 = 书信主体**：conversations 道集合了致 Theo 的英文两卷之一（1927，
  `src-683020755a90`）、致 Émile Bernard 的英文书信（1912-1913 三扫描，
  `src-f5617484c043`/`src-5751a200cf57`/`src-ac0ac7a914af`，主件 `src-5751a200cf57`）
  与德文《Briefe》各印次（1906/1908/1911/1918，主件 `src-eb5be7530935`）。
  这是梵高「说话」最密集的一批材料。
<!-- src-5751a200cf57 -->
- **色彩观是他的核心信条**：致 Bernard 的信里，梵高把「色彩高于明暗（values）」当
  方法论宣言："It is impossible to attach the same importance both to values and to
  colours. Theodore Rousseau understood the mixing of colours better than anyone. But
  time has blackened his pictures, and now they are unrecognizable. One cannot be at the
  Pole and at the Equator at once. One must choose one's way; at least this is what I
  hope to do, and my way will be the road to colour."
<!-- src-5751a200cf57 -->
- **画法从「再现」转向「表达」**：他主张有意识地歪曲真实以达到情感强度："I treat the
  colouring in a perfectly arbitrary fashion. What I aim at above all is powerful
  expression."（致 Bernard）
<!-- src-5751a200cf57 -->
- **卧室画的自述**（1890 年前后，法语引文出处同 Bernard 书信集）："I will simply paint
  my bedroom. This time the colour shall do everything. By means of its simplicity it
  shall lend things a grand style, and shall suggest absolute peace and slumber to the
  spectator."
<!-- src-5751a200cf57 -->
- **德文版证实同一批致 Theo 书信**：`src-eb5be7530935`（1918 第八九版）开头即
  "Du mußt es mir nicht übel nehmen, lieber Bruder, daß ich Dir schon wieder schreibe, —
  es geschieht nur, um Dir zu sagen, daß das Malen mir ein so ganz besonderes Vergnügen
  macht"——与荷文/英文致 Theo 书信同一脉络。
<!-- src-eb5be7530935 -->
- **1927 英文两卷是致 Theo 书信的完整英译**（`src-683020755a90` 为第 1 卷，题名页
  "VINCENT VAN GOGH TO HIS BROTHER 1872-1886 ... IN TWO VOLUMES"），含弟媳所撰
  Memoir 与按年编排的书信；第 2 卷（1886-1890 段）另行处理。

## Candidate Claims

- 梵高把「色彩/表达」置于「忠实再现/明暗法」之上，形成明确的画论立场
  （`src-5751a200cf57`）。
- 其艺术观通过书信反复自陈：色彩即情感强度的载体，允许对形与色做「任意」处理
  （`src-5751a200cf57`）。
- 致 Theo 的书信是贯穿其一生的对话，构成其文字作品的主体（`src-683020755a90`）。

## Contradictions and alternative explanations

致 Bernard 的信与致 Theo 的信读者不同、语气有别：给 Bernard 的多谈理论，给 Theo 的
多谈生活与经费。翻译（Ludovici 英译、Mauthner 德译）在措辞上各有取舍，引文须以所在
载体为准。

## Unknowns and source gaps

1927 英文第 2 卷（1886-1890 段）不在本道范围；梵高致 Theo 的信原文为荷兰文，英文两卷
是英译而非原卷。1906 年《Briefe》的 20.-24. 版与 1918 年第八九版内容近似，作同一译本。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

conversations 道承载梵高的「说话」：色彩高于明暗的画论、主动歪曲以求表达的创作观、
以及以 Theo 为唯一长期对话者的通信结构。
