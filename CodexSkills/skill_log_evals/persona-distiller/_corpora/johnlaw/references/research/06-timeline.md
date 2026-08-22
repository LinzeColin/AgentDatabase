# Timeline

## Scope and assigned sources

**本道分到 1 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-eb9e695df0c7` | 1824 | P2 | Memoirs of the life of John Law of Lauriston [microform] :…ion of the Mississippi system |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## 13 条实测发现（逐份）

★ 引文逐字照录 raw 扫描原文：**双空格排版与 OCR 讹形原样保留，行尾断词处的连字符按原文照录**（如 `pro-` / `fession`、`Comptrol-` / `ler`），不作静默拼接、不作「善意修正」——保证每条引文都能在 raw 中逐字 grep 命中。OCR 讹字例：`£l  10,000`（应为 £110,000，l=1）、`this  clay`（应为 this day）、`MISSISIPPI`、`PBOGRESS`（题名页应为 PROGRESS）。引文块中被省略的源行（页眉如 `6  LIFE  OF  JOHN  LAW`、脚注行、页码、空行）一律用 `[版口：…]` 在原位标出，不作静默跳行。

### ① 出生与受洗：1671 年 4 月生于爱丁堡，4 月 21 日受洗

> was  born  in  the  capital  of  Scotland  in  April
> 1671,  his  baptism  being  thus  entered  in  the
> Registers  of  Edinburgh  on  the  21st  of  that
> month,  "  William  Law,  goldsmith,  and  Jean
> Campbell,  a  son  named  John.

<!-- src-eb9e695df0c7 -->

- 生平年表的起点：1671 年 4 月生于苏格兰首府爱丁堡，4 月 21 日受洗入册。书中引录了爱丁堡登记簿的原文——「William Law 金匠与 Jean Campbell 得子名 John」，见证人包括多位商人；父亲 William Law 的职业在金匠之外兼有银行性质（见下条）。

### ② 家世：父为爱丁堡金匠兼银行家，购入 Lauriston，父卒于其未满 14 岁前

> He  followed  the  pro-
> fession of  a  goldsmith  in  Edinburgh,  a  busi-
> ness, at  that  time,  partaking  more  of  the  na-
> ture of  a  banker's  than  of  that  to  which  the
> name  is  now  restricted

<!-- src-eb9e695df0c7 -->

> He  lost  his  father  before  he  had  completed
> his  14th  year,  experiencing  the  disadvantages
> of  emancipation  from  paternal  control  at  an
> early  age.

<!-- src-eb9e695df0c7 -->

- 父亲 William Law 是爱丁堡金匠，书里特意说明这种生意在当时更像银行家而非今日意义的金匠（引文即此）。父亲购得 Firth of Forth 南岸、Cramond 教区约 180 苏格兰英亩的 Lauriston 与 Randleston 地产（书中记 disposition 日期为 1683 年 6 月 14 日、charter 1683 年 7 月 20 日）；1684 年 9 月 25 日 John Law 被立为其父的继承人。但他未满 14 岁便丧父——这是他早年脱离父权的起点。

### ③ 教育、伦敦赌徒期与 1692 年弃产偿债：得号「Beau Law」

> distinguished  by  the  appellation  of  Beau  Law.

<!-- src-eb9e695df0c7 -->

> This  he
> conveyed  to  his  mother,  Jean  Campbell,  by
> disposition  dated  at  London  6th  February,
> 1692.

<!-- src-eb9e695df0c7 -->

- 他在爱丁堡受教育，偏重算术、几何、代数，并自修公私信用、贸易、税收等政治经济学知识。青年时期以外表俊美、擅于牌戏闻名，书中说他以「Jessamy John」「Beau Law」的名号被同伴知晓，以网球与赌博技艺著称。他在伦敦沉迷赌博、欠债深重，1692 年 2 月 6 日（伦敦）立 disposition 把由其继承的 Lauriston 地产让给母亲 Jean Campbell 以偿还债务——母亲替他清偿并保住祖产，这一节点标志他彻底脱离苏格兰的财产根基。

### ④ 1694 年决斗杀人：4 月 9 日 Bloomsbury Square 决斗杀死 Beau Wilson，4 月 18–20 日受审、20 日判死刑

> Bloomsbury
[版口：6  LIFE  OF  JOHN  LAW]
> Square,  9th  April,  1694,  when  Mr.  Wilson
> was  killed  on  the  spot.

<!-- src-eb9e695df0c7 -->

> found  that  Mr.  Law
> was  guilty  of  murder,  and  sentence  of  death
> was  passed  on  him,  20th  April,  1694.

<!-- src-eb9e695df0c7 -->

- 人生第一个断裂点：因 Mrs. Lawrence 之争与 Edward Wilson（人称 Beau Wilson）于 1694 年 4 月 9 日在 Bloomsbury Square 决斗，Wilson 当场被杀。Law 随即被捕，1694 年 4 月 18、19、20 日在 Old Bailey 的 Justice Hall 受审（书里整段引录官方审判记录：两人只交锋一次，Wilson 上腹受两英寸致命伤）。陪审团认定谋杀成立，1694 年 4 月 20 日判死刑。

### ⑤ 1695 年越狱与流亡：London Gazette 悬赏广告，旅欧研习阿姆斯特丹银行

> the  following  advertisement  was  published  in
> the  London  Gazette  of  Monday,  7th  January,
> 1695  : — "  Captain  f  John  Lawe,  a  Scotchman,
> lately  a  prisoner  in  the  King's  Bench  for
> murther,  aged  26

<!-- src-eb9e695df0c7 -->

> making  himself  as  much  as  possible
> acquainted,  upon  the  spot,  with  the  operations
> of  the  mysterious  bank  of  Amsterdam

<!-- src-eb9e695df0c7 -->

- 判决后他获得王室赦免，但因死者之弟提出 appeal 而被扣在 King's Bench 监狱；在此期间越狱。书中引 1695 年 1 月 7 日《London Gazette》的悬赏广告：「Captain John Lawe，苏格兰人，国王监狱杀人犯，26 岁，高个、黑瘦、六英尺余……」，并指出广告把他写成 26 岁其实当时只有 24 岁（OCR 讹形下引文照录 `aged  26`；`Captain` 后的 `f` 是书里脚注记号，脚注说明他并无军职，「Captain」只是旅行时的头衔）。流亡期间他游历欧陆、实地研习各地银行与财政，特别是神秘而繁荣的阿姆斯特丹银行——书中称他曾为英国驻荷代表的秘书，得以就近观察其运作，这是他金融知识的直接来源之一。

### ⑥ 1700–1705 苏格兰改革方案：《Council of Trade》建议书；1705 年《Money and Trade Considered》被议会否决

> his  "  Proposals  and  Reasons  for  constituting
[版口：12  LIFE  OF  JOHN  LAW]
> a  Council  of  Trade/'  being  dated  at  Edin-
> burgh, 31st  December,  1700

<!-- src-eb9e695df0c7 -->

> 1705,  offered  to  Parliament  a  plan  for  remov-
> ing the  difficulties  Scotland  then  lay  under

<!-- src-eb9e695df0c7 -->

> "  that  to  establish  any  kind  of  paper  credit,
> so  as  to  oblige  it  to  pass,  was  an  improper  ex-
> pedient for  the  nation."

<!-- src-eb9e695df0c7 -->

- 十七世纪末回到苏格兰：其《Proposals and Reasons for constituting a Council of Trade》引言落款为爱丁堡 1700 年 12 月 31 日（书中记 1701 年初出版），提议以议会立法设「贸易委员会」，掌握国王全部收入、主教地租、什一税等，用以振兴苏格兰贸易与制造业、修路建桥——但威廉王朝不予支持。1705 年他再向苏格兰议会提出缓解通货短缺、银行停付困境的计划，并先行出版《Money and Trade Considered》；议会否决，决议称「建立任何强迫流通的纸币信用，都是对本民族不当的权宜之计」（OCR 讹形照录：`Trade/'` 应为 Trade, 的引号讹形；`ex-` / `pedient` 为原书行尾断词）。被否后他决定离开苏格兰到国外碰运气。

### ⑦ 流亡欧洲致富，1714 年第三次赴巴黎、攀上摄政王

> in  1714  he
> was  worth  upwards  of  £l  10,000  sterling.

<!-- src-eb9e695df0c7 -->

> Paris  for  the  third  time  in  1714,  not  long
> before  Louis  XIV.  gave  way  to  fate

<!-- src-eb9e695df0c7 -->

> nominated  him  one  of  the  Coun-
> sellors of  State.

<!-- src-eb9e695df0c7 -->

- 被否后他流亡欧陆：先住布鲁塞尔，以赌戏（Pharaoh 为其最爱）与金融投机闻名，号称随身常带不少于 10 万里弗尔金币；游历意大利各城（罗马狂欢节、威尼斯、热那亚），到 1714 年身家逾 £110,000（OCR `£l  10,000`，l=1）。其间他多次向欧洲王公兜售金融方案：向萨伏依的 Victor Amadeus 提银行计划被拒（对方说自己的领地「装不下这么大的设计」，建议他去法国）；1714 年第三次赴巴黎，随后路易十四去世，旧识奥尔良公爵（前 Chartres 公爵）以摄政身份主政，与他亲密无间，并任命他为国务顾问之一（引文中 `Coun-` / `sellors` 为原书行尾断词）。

### ⑧ 1716 年通用银行（Banque Générale）创立

> bearing  date  the  2d  and  20th  of
> May,  1716,  containing  the  following  regula-
> tions.

<!-- src-eb9e695df0c7 -->

> "  The  bank  promises  to  pay  to  the  bearer,
[版口：原书行间空行]
> at  sight,  the  sum  of crowns,  in  coin  of
[版口：原书行间空行]
> the  weight  and  standard  of  this  clay

<!-- src-eb9e695df0c7 -->

> to  pass  current  for  one  per  cent  more  than  the
> coin  itself.

<!-- src-eb9e695df0c7 -->

- 金融生涯的正式起点：1716 年 5 月 2 日与 5 月 20 日的敕书建立私人银行，Law 与其兄弟 William 为主要合伙人，称「Law and Company 通用银行」。股本 1200 股 × 5000 里弗尔（合 30 万英镑）；纸币面文承诺「见票即付、按当日成色足重的铸币支付」（OCR `this  clay` 应为 this day），恰可抵御法国当局任意改铸、改变币制对持币人的盘剥（书中举例：1716 年 6 月 2 日以 40 里弗尔/马克存入的 1000 里弗尔纸币，日后币制改为 50 里弗尔/马克时仍可兑回 25 马克即 1250 里弗尔）。凭此条款与税收收受，通用银行纸币很快声誉鹊起，比铸币升水 1% 流通，汇兑对伦敦、荷兰一度升到 4–5% 于巴黎有利。

### ⑨ 1717 年西方公司（密西西比体系奠基）与后续并购

> by  letters  patent  dated  in
> August  1717,  a  commercial  company  was
> erected,  under  the  name  of  the  Company  of
> the  West

<!-- src-eb9e695df0c7 -->

> 200,000  actions,  or  shares,  were  is-
> sued, rated  at  500  livres  each

<!-- src-eb9e695df0c7 -->

> and  M.  d'Argenson,  keeper  of  the  seals,)  was
> named  director  general.  The  actions  were

<!-- src-eb9e695df0c7 -->

- 密西西比体系奠基：1717 年 8 月敕书成立「西方公司」（Company of the West），获授整个路易斯安那省（由密西西比河灌溉），后因河名而通称「密西西比体系」。发行 20 万股 × 500 里弗尔，以 billets d'etat（贬值的国债票据）认购——当时 500 里弗尔名义面值的这类票据市价仅 150–160 里弗尔，却按全价认购，对持票人是强烈诱饵。公司由此成为国王 1 亿里弗尔的债权人，年息 4%；Law 任总监。此后一路并购：1718 年 9 月 4 日接掌烟草农场（加租 2,020,000 里弗尔）、1718 年 12 月 15 日购入塞内加尔公司；1719 年 5 月获东印度、中国、南海贸易独占权并更名「印度公司」，又于 1719 年 7 月 25 日接掌铸币厂（5 千万里弗尔对价）、8 月 27 日从包税人手里接掌大农场、8 月 31 日获国王其余税收的总收银权——把法国对外贸易、铸币、税收集于一身。

### ⑩ 1718 年皇家银行：纸币性质改变

> by  act  of  council,  bearing  date  4th  December,
> 1718,  that  the  king  had  taken  Mr.  Law's
> bank  into  his  own  hands,  under  the  name  of
> the  Royal  Bank

<!-- src-eb9e695df0c7 -->

> there  were  to  the  amount  of  1000  millions  of
> livres  fabricated  betwixt  the  5th  January  and
> 29th  December  1719.

<!-- src-eb9e695df0c7 -->

- 银行国有化的转折：1718 年 12 月 4 日枢密院敕令宣布国王把 Law 的银行收归己手，更名「皇家银行」（Royal Bank），偿还旧股东股金、承担其约 5900 万里弗尔的在途纸币；Law 任总监。关键改变是纸币面文从「按当日成色足重的铸币支付」改为「银币里弗尔」——从此纸币与硬币同样受当局任意改币的波及，Law 曾尽力阻止而未果（书中明确记载他曾反对这一改动）。此后纸币狂发：1719 年 1 月 5 日至 12 月 29 日间造出 1000 百万里弗尔；1720 年 2 月皇家银行并入印度公司后到 5 月 1 日又造 1,696,400,000 里弗尔，合计 2,696,400,000 里弗尔纸钞。

### ⑪ 1719 顶点：股价破万、改宗天主教、1720 年 1 月 5 日任财政总监

> 1719,  the  price  of  shares  rose,  after  some
> fluctuations,  to  above  10,000  livres  each

<!-- src-eb9e695df0c7 -->

> and  daughter,  a  public  profession  of  the  Ro-
[版口：脚注 * 及页眉 OF  LAURISTON.  69]
> man  Catholic  religion,  which  was  done  with
> great  pomp  in  the  church  of  the  Recollets
> at  Melun,  in  December  1719

<!-- src-eb9e695df0c7 -->

> the  5th  of  January  1720,  declared  Comptrol-
> ler General  of  the  Finances  of  France.

<!-- src-eb9e695df0c7 -->

- 声望与权力的顶点：1719 年 11 月印度公司股价经波动升到每股 1 万里弗尔以上（把 billets d'etat 的贬值算进去，约为原价的 60 倍）；全法国从平民到法官、主教、亲王皆成炒股者，Rue Quinquempoix 挤满经纪人，连摄政王的主治医生 Chirac 都因股价下跌而失态。为扫除晋升障碍，他于 1719 年 12 月携子女在 Melun 的 Recollets 教堂公开改宗罗马天主教，并任 St. Roch 教会荣誉堂董、捐赠 50 万里弗尔；科学院于 1719 年 12 月 2 日选他为名誉院士。1720 年 1 月 5 日他被宣布为法国财政总监（Controleur General des Finances，引文 `Comptrol-` / `ler` 为原书行尾断词），主动放弃全部薪俸与附带收入。同月摄政王母（Palatine 公主）的信与 Richelieu 元帅的记述都描绘了他被贵妇恳求、杜克争相觐见的盛况。

### ⑫ 1720 崩溃：强制收银令、5 月 21 日减值敕令、银行停兑

> edict  of  the  27th  February  1720,  pro-
> hibiting individuals,  and  secular  or  religious
> communities,  (some  privileged  officers  except-
> ed,)  from  having  in  their  possession  more
> than  500  livres  in  specie

<!-- src-eb9e695df0c7 -->

> on  the  21st  of  May  1720,  an
> edict  was  published

<!-- src-eb9e695df0c7 -->

> the  whole  paper  fabric  fell  to  the  ground,  the
> notes  lost  all  credit

<!-- src-eb9e695df0c7 -->

> To  render  matters  worse,  payment
> was  the  same  day  stopped  at  the  bank

<!-- src-eb9e695df0c7 -->

- 体系崩塌：为防硬币外流，1720 年 1–3 月连发敕令——限制小额支付、宣布纸币「恒不变、高于铸币 5%（个别 10%）流通」、强令以纸币纳税；2 月 27 日敕令禁止任何个人或团体持有超过 500 里弗尔铸币（违者重罚并没收，检举人得赏），3 月 11 日更禁止以铸币支付。5 月 21 日敕令把股票从 9000 里弗尔逐月降至 12 月 1 日的 5000 里弗尔、纸币按同比例减半——书中称之为「不义而致命的一步」，据 Law 之侄 Law de Lauriston 说系违背 Law 本人意见、经其呈报而发布；此令一出「整座纸建筑轰然倒塌、纸币尽失信用」。5 月 27 日该令被撤回，但同日银行停兑，时在流通的纸币仍有 2,235,085,590 里弗尔；此后银行门前挤兑惨案频发（7 月 17 日一次 20 人窒息而死），股价崩至 1 路易金币可买一股。

### ⑬ 失势、流亡、归英与逝世：1720–1729

> measure,  he,  on  the  29th  of  May,  went  to  the
> Palais  Royal  to  resign  his  office  of  Comptrol-
> ler into  the  hands  of  the  Regent

<!-- src-eb9e695df0c7 -->

> the  scene  of  his  disgrace,  on  the  10th  Decem-
> ber 1720,  retiring  to  Guermande

<!-- src-eb9e695df0c7 -->

> Mr.  Law  arrived  at  Brussels  in  the  morn-
> ing of  the  22d  December  1720,  passing  under
> the  name  of  M.  du  Jardin

<!-- src-eb9e695df0c7 -->

> He  came  to  Venice  early  in  January  1721,
> still  passing  under  the  name  of  M.  du  Jardin

<!-- src-eb9e695df0c7 -->

> Landing  at  the  Nore,  20th  October
> 1721,  he  proceeded  to  London

<!-- src-eb9e695df0c7 -->

> on  the  28th  of  November  following,  pleaded,
> at  the  bar  of  the  King's  Bench,  his  Majesty's
> pardon  for  the  murder  of  Mr.  Edward  Wilson
> in  1694

<!-- src-eb9e695df0c7 -->

> The  Regent  died  suddenly,
> 2d  December  1723,  which  was  a  fatal  blow

<!-- src-eb9e695df0c7 -->

> finally  quitted  Britain  the  same  year,  1725,
> and  fixed  his  residence  at  Venice

<!-- src-eb9e695df0c7 -->

> dying  there  in  a  state  but
> little  removed  from  indigence,  on  the  21st  of
> March  1729,  in  the  fifty-eighth  year  of  his
> age

<!-- src-eb9e695df0c7 -->

- 1720 年 5 月 29 日他向摄政请辞财政总监（摄政派瑞士卫队「保护」以防民愤）；7 月 17 日银行惨案引发骚乱，他在 Palais Royal 避居数日；8 月 27 日又被任为银行与印度公司总监、枢密院事务报告官，但巴黎人对他恨之入骨（一次他被误认的马车遭石击追打）。12 月 10 日他交出所有职务、离开巴黎退居郊外 Guermande；12 月 22 日化名 M. du Jardin 抵布鲁塞尔，受当地人礼遇。1721 年 1 月初到威尼斯度过狂欢节两月（与西班牙大臣 Alberoni 红衣主教晤谈）；同年返英——10 月 20 日在 Nore 登陆、赴伦敦，由 Sir John Norris 引见乔治一世，11 月 28 日在 King's Bench 当庭领受 1694 年杀死 Edward Wilson 一案的王室赦免（其兄弟与亲友到场）；英法两国财产均被扣押没收，他在伦敦靠摄政继续汇来的 2 万里弗尔年薪与救济度日。摄政 1723 年 12 月 2 日猝逝对他「是致命一击」——复职与追产希望落空、年金停发、债主起诉。1725 年他离英定居威尼斯，期间 Montesquieu 曾登门拜访；1729 年 3 月 21 日卒于威尼斯，享年 58 岁，葬于该城某教堂（书末附墓志铭：Ci git cet Ecossois celebre / Ce calculateur sans egal / Qui par les regles de l'algebre / A mis la France a l'hopital）。

## 这一道给下游的东西

**生平关键节点（可作时间线骨架，均据 Wood 1824）**
- 1671-04（4 月 21 日受洗）：生于爱丁堡；父 William Law 金匠/银行家，1683 年购 Lauriston 地产；未满 14 岁丧父。
- 1692-02-06（伦敦）：把 Lauriston 让给母亲偿债；此前在爱丁堡/伦敦以赌徒与「Beau Law」知名。
- 1694-04-09/20：Bloomsbury Square 决斗杀死 Beau Wilson；4 月 18–20 日受审，20 日判死刑。
- 1695-01-07（London Gazette 广告）前后：越狱流亡欧陆，研习阿姆斯特丹银行等。
- 1700-12-31/1701：《Council of Trade》建议书（落款 1700-12-31、1701 年出版），苏格兰议会不支持。
- 1705：《Money and Trade Considered》出版、向苏格兰议会提纸币计划，被否；此后流亡欧陆以赌戏与投机致富（1714 年值逾 £110,000）。
- 1714：第三次赴巴黎；路易十四死后摄政奥尔良公爵亲信，任国务顾问。
- 1716-05-02/20：成立通用银行（Banque Générale），纸币按「当日成色足重铸币」兑付，一度比铸币升水 1%。
- 1717-08：成立西方公司（Company of the West，密西西比体系），20 万股 × 500 里弗尔；此后并购烟草、塞内加尔、东印度/中国/南海贸易、铸币厂、大农场、税收（至 1719 年）。
- 1718-12-04：银行收归王手更名皇家银行；纸币面文改「银币里弗尔」；1719 年印发 1000 百万里弗尔。
- 1719-11：股价破 1 万里弗尔（约原价 60 倍）；1719-12 改宗天主教；1720-01-05 任法国财政总监。
- 1720-02-27：禁持超 500 里弗尔铸币；03-11 禁铸币支付；05-21 减值敕令（股票 9000→5000、纸币减半）；05-27 撤回但当日停兑（流通纸币 2,235,085,590 里弗尔）。
- 1720-12-10 离巴黎退居 Guermande；12-22 化名 M. du Jardin 抵布鲁塞尔；1721-01 抵威尼斯；1721-10-20 返英、11-28 领受 1694 年杀人赦免；1723-12-02 摄政卒；1725 定居威尼斯；1729-03-21 卒于威尼斯（58 岁）。

**角色转变**
- 商人/赌徒 → 流亡投机家 → 法国银行家（通用银行）→ 特许公司巨头（西方/印度公司）→ 财政总监（1720 年在任）→ 泡沫崩塌后的弃臣/流亡者 → 威尼斯贫病而终的「过气天才」。每次角色更替都由一次具体日期事件触发（决斗、被议会否决、敕书、减值敕令、辞职、越境）。

## 未做完 / 未核

- 本书 1719–1720 的账面细节（纸币/股票各次发行额、按面值与按市值两种口径）在不同引注间有出入（如书中引 Sir James Steuart 与 M. du Verney 对国家债务余额的算法不同），本道只保留与人物年表直接相关的锚点，未逐一核对每笔数字。
- 摄政王母亲（Palatine 公主）与 Richelieu 元帅记述的轶事（贵妇围堵、典当行趣闻等）只作声望顶点的佐证，未逐条核对其转述来源。
- 书末附录为 Henri Storch《Cours d'Economie Politique》的译文（对 Law 体系的批判性经济分析），属经济学评论而非生平年表，本道未将其并入时间线；该内容更适合归入 external 道（但 external 道仅配 Davis 1887，故此处不引）。
- 死亡年份、葬地与墓志铭均以 Wood 记载为准（1729 年 3 月 21 日，58 岁）；未与其他传记交叉验证。
