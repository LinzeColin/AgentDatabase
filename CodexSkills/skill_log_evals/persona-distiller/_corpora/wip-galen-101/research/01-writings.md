# 01 · 著述路：一个人写下的东西，占了存世古希腊文献的十分之一

## 语料规模与它的两面

`galenus_cts` 收 105 部，本工作区解出 **89 部真作**（希腊文合计 **2,442,576 词**）
与 **16 部伪托／存疑**（后者一条都没有灌进训练，理由见下）。
代表性主干：`src-4e9624fcbf1d`《De placitis Hippocratis et Platonis》94,934 词、
`src-228e52e2e60e`《De anatomicis administrationibus》78,654 词、
`src-9431686c4a13`《De naturalibus facultatibus》31,978 词、
`src-24484ad96665`《De temperamentis》27,769 词、
`src-029ba2047da6`《Ars Medica》16,227 词、
`src-4f3b62774f0d`《De elementis ex Hippocrate》13,451 词、
`src-d525f8632f76`《De constitutione artis medicae》12,003 词。
另有英译两种可逐字引用：`src-9431686c4a13` 的 Brock 1916 Loeb 全译、
`src-228e52e2e60e` 的 Singer 1956 全译。

**规模大到反而要先说它的代价**：这一路的富足是「他自己写的多」，
不是「关于他的记载多」。见 `04-external.md`。

## 真伪分层：为什么必须在灌库之前做

两个公开语料库**都没有机读的真伪标记**——`galenus_cts` 105 部里只有一个加星，
是噪声不是体系。**照单全收会让伪作以 P1 身份进账本而无人拦截**，
而它们的现代版扉页署名与真作一模一样。

因此分层由**外部权威**在灌库前决定，写死在 `meta.json:attribution_basis`：
他本人的《De libris propriis》真作目录（`src-ba4df545a0f2`）＋
Fichtner《CORPUS GALENICUM》伪托目录。裁定为伪或存疑的 16 部
（tlg034/035/040/048/049/052/063/071/073/079/086/096/106/111/114/115）
**一条都不灌**——`ingest` 没有 `P1-D` 这一档，塞成 S2 只会让它们以「材料」身份进入下游，
而真伪分层的意义就是不让它们进训练。

## 这一路能支持什么、不能支持什么

**能**：方法论主张、生理与解剖学说、他对前人（尤其希波克拉底派）的读法与改写。
**不能**：任何需要外部佐证的生平事实。他的著作是他自己的口径，
`04-external.md` 里没有任何一条能独立校准它。
