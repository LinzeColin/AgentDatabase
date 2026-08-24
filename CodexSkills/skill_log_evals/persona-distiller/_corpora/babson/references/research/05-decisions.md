# Decisions and actions

## Scope and assigned sources

**本道分到 3 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-7f7930c5bcaa` | — | P1 | A BUSINESS MAN'S VIEW ON HOW TO SECURE PERMANENT PEACE AFTER THE WAR |
| `src-ca4e13110fb8` | — | P1 | A Constructive Policy for Mexico |
| `src-e8a7e154615a` | — | P1 | Ascertaining and Forecasting Business Conditions by the Study of Statistics |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### ① 《Ascertaining and Forecasting Business Conditions by the Study of Statistics》（1912 刊，1911-12-29 在美国统计学会宣读）——把"决策"建立在统计上的方法论自述
`src-e8a7e154615a` 是他面向统计学会的方法宣讲，但**同时也是"商人该怎么决策"的操作指南**。开篇先拆两种错误信念——"我的生意只取决于本地/本行"：

> his business in his own small locality is dependent upon conditions throughout the entire country and the business in his own distinct line is dependent [版口：37] upon conditions in every other line
<!-- src-e8a7e154615a -->

（跨页断在 [版口：37]；上下文：他主张本地百货店的生意取决于全国钢铁/谷物/铁路状况的连锁，因此商人必须看全国统计——改述衔接。）

> tell me what the conditions outside of Pittsburg will be, and I will tell you what the conditions in Pittsburg will be.
<!-- src-e8a7e154615a -->

- 他当时已向订户发行两周一次的全国商业报告＋两张美国地图（"乐观图/悲观图"），并自评价值：

> our statisticians are simply supplying suppressed news months [版口：39] before it appears in the public press and magazines
<!-- src-e8a7e154615a -->

- 预测部分的核心——**商业像风暴一样在国与国之间成波移动**：

> business conditions travel from one part of the country to another in distinct waves, as do storms
<!-- src-e8a7e154615a -->

- Composite Plot（综合图）的用途——"给全国做一张试算表"：

> This gives a sort of trial balance for the entire country.
<!-- src-e8a7e154615a -->

- 他的预测理论依据——**把力学法则直接搬到商业**：

> the fundamental law of "action and reaction being equal when the total force involved is considered" applies to business as well as to mechanics, chemistry, and every other known art or science
<!-- src-e8a7e154615a -->

- 船长类比（应看"变化的方向"而非当下读数）：

> the captain of an ocean liner wants to know what the weather is today
<!-- src-e8a7e154615a -->

（后文："像海员盯气压表的变化方式而非即时气压那样看每周图与数字，商人就能预判未来变化"——改述。）

- 全文收在"美国的未来靠牧师与统计师"（呼应他对宗教与商业的双重信念）：

> the future of this country depends on the preacher and the statistician
<!-- src-e8a7e154615a -->

⇒ 声口/论点：这篇把"决策"明确描述成**先测全国与全行业的根本条件、再据此买卖/放贷/扩信用**的流程；他把自己的机构定位成"替商人看全国的晴雨表"，并宣称这比关税/补贴/谢尔曼法更能解决国家问题（"the future... depends not on tariffs or ship-subsidies... but on educating our bankers, manufacturers, and merchants in the fundamentals of uprightness and economics"，改述）。

### ② 《A Business Man's View on How to Secure Permanent Peace After the War》（1916，Advocate of Peace）——"国际事务的国际管控"：从经济因果推时局主张
`src-7f7930c5bcaa` 是他 1916 年 5 月发表于《Advocate of Peace》的政论。**他的出发点仍是经济框架**——战争有真实的经济原因，必须消除原因而非筑坝拦流：

> war will be abolished only when some method is devised for enabling nations to obtain peaceably what they would otherwise secure through an armed conflict
<!-- src-7f7930c5bcaa -->

> there are real economic causes of war which must be eliminated before there can be world peace
<!-- src-7f7930c5bcaa -->

- 他列三个"经济战争原因"：歧视性关税/移民法、各国独立护其贸易航线与殖民者、缺乏干预经济改革的跨国中央权力（改述三项）。他的药方是商人圈的口号：

> "International Control of International Affairs."
<!-- src-7f7930c5bcaa -->

- 论证靠"作用=反作用"法则外推——**让利给他人最终利己**：

> we as nations, classes, and individuals, can permanently prosper only as we co-operate in some plan which enables others to prosper with us
<!-- src-7f7930c5bcaa -->

> only through economic co-operation with other nations can our own interests finally be fully developed and protected
<!-- src-7f7930c5bcaa -->

- 他把美国建国史当先例——"用选票代替子弹"：

> ballots are used instead of bullets
<!-- src-7f7930c5bcaa -->

（上下文：十三州当年靠立法机关做"安全阀"、使武装革命失去意义，可推广为国际议会按人口加权投票——改述。）

- 对"军事备战"的态度：承认暂时必要，但"战舰、潜艇、飞机只是贴在病人身上的膏药"（"battleships, submarines, and aeroplanes are merely like plasters stuck on to the body of a sick man who needs a surgical operation"，改述）。

⇒ 声口/论点：**把"经济因果+等量反应"法则从景气预测一路推到国际和平主张**；立场是务实的国际合作（非空想和平主义），并自称这是"经济事实、不是理想主义"（"This is not offered as an idealism, but as an economic fact"，改述）。

### ③ 《A Constructive Policy for Mexico》（1920，美国政治与社会科学院）——"墨西哥属于墨西哥人"：时局干预的边界
`src-ca4e13110fb8` 是他 1920 年关于墨西哥干预政策的政论（自署"联邦中美洲委员会 1916 年成员"）。**他先否定"直白军事干预"，再给替代方案**：

- 干预无法避免（欧洲可能先动手、共和党若胜选必干预——改述），问题只在**形式**：破坏性 vs 建设性。他借 Interchurch Movement 的数字说"六个月的边界战役足够在每个 4000 人以上的墨西哥城市建公立学校/农学院/现代医院"（改述）。

> "Mexico for the Mexicans," rather than "Mexico for the Americans."
<!-- src-ca4e13110fb8 -->

（建设性干预成功的条件：财产控制权必须留给墨西哥人；"这是干预讨论最终搁浅的礁石"——改述衔接。）

- 他的发展观——**成长无捷径**：

> It seems to be a law of nature that nations and individuals must work out their own salvation and find themselves through struggle and sacrifice.
<!-- src-ca4e13110fb8 -->

> There is no short road to growth. Development takes time.
<!-- src-ca4e13110fb8 -->

- 结尾落到"宗教政治家"的呼唤（与《Religion and Business》同主题）：

> The great need of the hour in Washington and the capitals of Europe is more religion.
<!-- src-ca4e13110fb8 -->

（"需要既敢碰大问题、又敢用新方法的宗教政治家"——改述。）

⇒ 声口/论点：这篇展现他的**时局决策风格**——承认现实约束（"we must adapt ourselves to conditions rather than to theories"，引 Grover Cleveland），在两害相权里选"建设性干预"，并坚持把"墨西哥人保有财产控制权"设为底线；同时把政治问题带进宗教话语。

## Candidate Claims

- C-D1（fact）：决策应建立在"全国+全行业"的根本统计上——本地生意依赖全国与全行业条件（src-e8a7e154615a，与 writings/expression 的根本统计簇同源）。
- C-D2（mental-model）：商业像风暴成波移动；看"变化方向"而非当下读数；用"等量反应/面积"预测（src-e8a7e154615a）。
- C-D3（value/decision）：政策问题优先看经济因果——战争有真实经济原因、须消除原因；"国际事务的国际管控"；让利他人最终利己（src-7f7930c5bcaa）。
- C-D4（value/decision）：对政府干预取实用主义中间路线——军事干预"破坏性 vs 建设性"二分、"墨西哥属于墨西哥人"、财产控制权留给当地人（src-ca4e13110fb8）。
- C-D5（mental-model）：发展观——"民族与个人只能靠挣扎与牺牲自救""成长无捷径"；与"等量反应"同构（src-ca4e13110fb8、src-7f7930c5bcaa）。
- C-D6（value）：宗教是时局问题的最终解法——"华盛顿与欧洲首都最大的需要是更多宗教"；与"preacher and statistician"呼应（src-ca4e13110fb8、src-e8a7e154615a）。

## Contradictions and alternative explanations

- **"干预不可避免" vs "墨西哥属于墨西哥人"**：Mexico 文既说"某种形式的干预不可避免"（否则欧洲会动手），又说建设性干预的底线是"财产控制权留给墨西哥人"——他是"不得不干预、但干预必须被约束"的立场，不是一边倒反干预。引用时不能只取一半。
- **1916 和平文 vs 1920 干预文**：和平文主张"国际管控"、1920 干预文承认"现实逼人干预"——前者是理想框架、后者是现实折中；他在干预文里明说"理论上我赞同 Wilson 的观望政策，但欧洲没有那个远见"（改述）。两条主张并存于不同年份，不是打脸，但须按时间与语境取用。
- **"Preacher and statistician"的宗教-统计并置**：1912 统计学会文与 1920 墨西哥文都把宗教当作社会问题的解法——统计解决经济预测、宗教解决政治伦理，两者并行不悖；这是他后期世界观的连续性，而非矛盾。

## Unknowns and source gaps

- 三篇均为期刊政论（1912/1916/1920），无私人决策记录（无日记/书信/内部备忘录）；"他当时为什么这么选"只能从文中推断。
- 1916 和平文发表于战时，其"国际管控"主张后续是否被修订不可考；Mexico 文的"若共和党胜选必干预"预测（1920-11 大选）后续未在语料内校验。
- 三篇没有 Babson 个人投资决策的具体记录（他自己的买卖决策不在语料）。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- C-D1/C-D2 与 writings/expression 的根本统计簇跨道合流（同一方法三处表述：教科书/期刊/学会宣讲）。
- C-D3/C-D4/C-D5 合成"时局决策"簇：经济因果→国际合作；现实约束→建设性干预；成长无捷径。
- C-D6 与 Religion and Business（writings）互证"宗教作为社会解法"；可作为 Babson 后期思想（1920s 宗教转向）的证据链。
- 引用须知：三篇均为本名署名一手政论；跨页断处已用 [版口] 标出；Grover Cleveland 引语归 Cleveland。

## 未做完 / 未核

- 三篇都只精读正文论旨与关键段落：Ascertaining 文中间的统计表格/地图说明（Exhibit A/B/C）、Peace 文对具体国际机制（海牙法院/仲裁）的展开、Mexico 文对"1917 前合法投资"的具体界定未逐段核。
- 未把 Peace 文与 Mexico 文做"1916→1920 立场演变"的逐段对照（只确认"国际管控→建设性干预"方向，未核中间是否有别处转折）。
- 三篇的期刊卷页（Advocate of Peace 1916/135、American Statistical Association 1912/36、AAPSS 1920/209）按版口标出，未逐一与刊目核对。
