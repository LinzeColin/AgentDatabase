# 可核事实与知识边界

> 只放可直接核验的事实、时期、角色、领域与资料截止日期。每项使用 Claim ID。

## 事实

- 待研究。

## 知识边界

- 待研究。


<!-- ↓ 断言渲染区（由 render_claims.py 生成，勿手改） -->

## 断言层（逐条可回语料）

<!-- claim:clm-33784cd31698 -->
**语料元断言：本库 Law 语料由 8 份 train 源构成、跨 1705-1887、英法两语**——一手为 Law 本人论著（1705《Money and Trade》初版、1720《Full and Impartial Account》亲 Law 宣传册、1750 死后重印、1790《Oeuvres》结集、1843 Daire 卷内重印的 Lettres/Mémoires），二手为后人述评（1824 Wood 生平、1887 Davis 史评）；其中 1790 Oeuvres 的《Discours préliminaire》与脚注是编者（de Senovert）语、1843 Daire 的 Notice 是二手传记，引用时须标「编者/二手」，不可当 Law 本人观点。　［出处：evidence/source-ledger.jsonl 各 train 源题名页与编目年］

> **何时作废**：若后续发现 train 语料含他人伪托篇目或归属争议（如 1720 小册实为匿名/部分书目归 Defoe）⇒ 本条须更新归属分级

<!-- claim:clm-626580c726e4 -->
**1716 年他一面反「强制纸币」、一面在法国创立按「当日成色足重铸币」兑付的通用银行**——反强制立场（Daire 重印 1716 年《Lettre XV》致摄政王，OCR `11 est`＝Il est 照录）：`11 est absolument pour le bien de l'État, en tout temps , d'établir un crédit général , mais il est nécessaire que ce crédit soit au pair avec les espèces , et que l'introduction de ce crédit dans le commerce et payements particuliers soit volontaire ; si le crédit est forcé, il fera du mal au lieu de faire du bien`；通用银行 1716 年 5 月 2 日/20 日敕书条款（OCR `this  clay`＝this day 照录）：`The  bank  promises  to  pay  to  the  bearer,  at  sight,  the  sum  of  crowns,  in  coin  of  the  weight  and  standard  of  this  clay`。　［出处：Daire《Économistes financiers》1843（src-ce1dbab2c760，1843 年）；Wood《Memoirs of the life of John Law》1824（src-eb9e695df0c7，1824 年）］

> **何时作废**：若《Lettre XV》的 1716 年写作时间与归属被推翻 ⇒ 该引文降级为「Daire 卷所收」并重估时间

<!-- claim:clm-7a9c1058f60b -->
**土地是最稳定的货币、以地担保的纸币供给「随需求伸缩」而不超发**——1705 断言 `Land is what produces every thing, Silver is only the product.`（土地生万物、银子只是产物）；1750 干净版承诺纸币稳定且不过剩：`this paper- money will be keep its value, and there wrill always be as much money as there is occafion, or imployment for, and no more.`（OCR `wrill`＝will 照录）。　［出处：《Money and Trade Considered》1705（src-d2dd432e2f00，1705 年）；1750 版（src-b88a0f5958dd，1750 年）］

> **何时作废**：若 1750 版对 1705 原文有实质增删 ⇒ 该句只能归 1750 重印口径

<!-- claim:clm-7e8a05cb3d39 -->
**供需价值论：价值取决于「数量对需求的比例」**——1705《Money and Trade》开章用「水与钻石」例立论：`Example. Water is of great uſe, yet of little Value; Becauſe the Quantity of Water is much greater than the Demand for it.`，并据此把货币定义为度量、交换媒介、契约计值三位一体、明言「货币不是抵押品」：`Money is not a pledge, as ſome call it.`；对 Locke 式的「想象价值」他直言 `I cannot conceive how different Nations could agree to put an Imaginary Value upon any thing`（同页钻石句 OCR 讹形 `ef`＝of 照录：`Diamonds are of little uſe, yet of great Value, becauſe the Demand for Diamonds is much greater, than the Quantity ef them.`）。　［出处：《Money and Trade Considered》1705 初版（src-d2dd432e2f00，1705 年）；1750 格拉斯哥重印本为其死后干净重印（src-b88a0f5958dd，1750 年）］

> **何时作废**：若后世考证出价值论另有更早或更权威出处 ⇒ 本条须改为「已知最早以供需立价值论的表述之一」

<!-- claim:clm-83714b42d797 -->
**货币稀缺是「因」不是「果」；货币充足即繁荣、信用＝货币等价物**——1750 干净版全句照录（OCR `fcarcity`＝scarcity、断词 `mo- ney`/`abal- lance` 照录）：`Moft people think fcarcity of mo- ney is only the confequenceof abal- lance due ; but 'tis the caufe as well as the confequence, and the effectual way to bring the ballance to our fide, is to add to the money.`；后世 Davis 把他的纲领概括为 `The source of prosperity in any country he attributed to the abundance of money. Credit was the equivalent of money.`　［出处：《Money and Trade Considered》1750 版（src-b88a0f5958dd，1750 年）；Davis《An historical study of Law's system》1887（src-95aa7717830b，1887 年）］

> **何时作废**：若 1705 初版该句因版面残缺无法与 1750 逐字比对 ⇒ 本条明确以 1750 版口径为准
