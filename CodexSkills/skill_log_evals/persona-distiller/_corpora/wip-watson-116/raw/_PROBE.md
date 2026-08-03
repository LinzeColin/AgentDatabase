# #116 Jean Watson (1940– ，**在世**) — 语料可得性探测

探测日期：2026-08-04
结论：**deep / standard / quick 三档全部够不着。**
真取到全文的源 = **8 份**，**其中一手 8 份**，**公有领域 0 份**，**六条道只占 2 条**。

---

## 一、结论摘要（数字来自 `check_corpus_ceiling.py --ledger raw/_ids.txt`，不是估的）

```
手上：一手 **8** 份　总计 **8** 份　有材料的道 **2** 条

  quick   （8 份 / 3 道 / 占比 0.40 → 要 4 份一手）　够不着
      · 六条道只占 2 < 3
  standard（24 份 / 6 道 / 占比 0.50 → 要 12 份一手）　够不着
      · 份数 8 < 24 ／ 道 2 < 6 ／ 一手 8 < 12（占比上限 0.3333）
  deep    （45 份 / 6 道 / 占比 0.65 → 要 30 份一手）　够不着
      · 份数 8 < 45 ／ 道 2 < 6 ／ 一手 8 < 30（占比上限 0.1778）
```

| 判据 | deep 门 | 实测 | 差 |
|---|---:|---:|---|
| 总份数 | ≥ 45 | **8** | 差 37 |
| **一手份数**（ceil(45×0.65)） | ≥ 30 | **8** | **差 22** |
| 六条道覆盖 | 6 | **2** | 差 4 |
| **`conversations` 道**（0 即 standard/deep 死） | ≥1 | **0** | — |
| **公有领域份数** | — | **0** | 铁律「只取公有领域」→ 可入库 0 份 |

八份合计 **25,006 词**。

**与 #113 Henderson（2 份）／#114 Peplau（3 份）的差别只在数量级的零头**：
Watson 有一批拉美／日本／葡语的金色 OA 期刊文章，所以份数从 2–3 抬到 8。
**但一份都不是公有领域，而且量级仍然差 5 倍多。**

---

## 二、版权状态查证结果

### 2.0 ★ 先说清楚这一份和前两位不一样在哪

Henderson / Peplau 的问题是「**有没有按时续展**」——需要查 CCE 才知道。
**Watson 不存在这个问句**：她 **1940 年生、在世**，
最早的著作《Nursing: The Philosophy and Science of Caring》出版于 **1979 年**，
落在 **1976 年版权法**（1978-01-01 生效）之下 —— 17 U.S.C. §302(a)：
**保护期 = 作者终身 + 70 年**，**无须续展，也无从「漏续展」**。

**所以「查 CCE 查不到」不是有利证据，而是本来就该查不到。**
下面 §2.1 照做了，但**必须按这个口径读**，不许反推成公有领域。

### 2.1 NYPL `cce-renewals` 全库 grep —— **0 命中，且这是预期结果**

数据源：`https://api.github.com/repos/NYPL/cce-renewals/contents/data`
→ **47 个 TSV 全下**，合计 **445,433 行**。

| grep（不分大小写） | 命中 |
|---|---:|
| `jean watson` | **0** |
| `watson, jean` | **0** |
| `philosophy and science of caring` | **0** |
| `human science and human care` | **0** |
| `watson`（任意） | 446 |
| `watson` **且** 同行含 `nursing`／`nurse`／`caring` | **0** |

→ CCE 覆盖的是 **1922–1963 年出版物在 1950–1992 年登记的续展**。
**她的产出期整段在这个区间之外**，0 命中与「查不到」同义，**不构成任何公有领域推定**。

### 2.2 ★ 硬证据：她本人到 2023 年仍在逐篇持有版权

**这是本次最直接的一条**，取自 Pensar Enfermagem 期刊页面原文：

```
Copyright (c) 2023 Jean Watson
This work is licensed under a Creative Commons Attribution 4.0 International License.
```

（`https://pensarenfermagem.esel.pt/index.php/esel/article/view/296`）

——**版权人写的是她本人的名字**，且她**在世**。
CC-BY 是**她授出的许可**，不是版权失效。**许可可以撤回，公有领域不能。**

其余各件的版权声明，逐条照录（全部是我实际取到的页面／PDF 上的原文）：

| 出处 | 原文 |
|---|---|
| J-STAGE（日本看護科学学会誌 2002 / 2004） | `© Japan Academy of Nursing Science` |
| SciELO *Texto & Contexto Enfermagem* 2007 | `This work is licensed under a Creative Commons Attribution-NonCommercial 4.0 International License.` |
| ACC CIETNA 2018 | `© 2018 Universidad Católica Santo Toribio de Mogrovejo – Chiclayo, Perú`（正文每页页眉重复） |
| NSC Nursing / OPI Napoli 2019 | `This work is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License.` |
| Watson Caring Science Institute 官网 | `© 2025 Watson Caring Science Institute.` |

### 2.3 ★★ 一条必须写下来的反例：**聚合器把在版权期内的文章标成了 `public-domain`**

Unpaywall 对 DOI `10.1111/j.1365-2702.2005.01256.x`
（Watson 独著，*Journal of Clinical Nursing* 2005 Guest Editorial）返回：

```
oa_status: hybrid
best_oa_location.license: public-domain
best_oa_location.host_type: publisher
```

**这是错的。** 同一 DOI 的 Crossref 记录写的是：

```
license: [("http://onlinelibrary.wiley.com/termsAndConditions#vor", "vor")]
```

即 **Wiley 标准条款**，与公有领域毫无关系。

→ **不许拿聚合器的 license 字段当版权判据。**
本项目如果照抄这一格，就会把一篇在版权期内的 Wiley 社论当成 PD 入库。
（顺带：这一篇的 PDF 实测 Cloudflare **403，未绕过**，所以并没有真取到；
但判据的教训与取没取到无关。）

### 2.4 未能取得的第二重证据（如实记录）

- **美国版权局 CPRS API**（`api.publicrecords.copyright.gov`）：
  `search_service_external/advance_search/` 先返 400 并吐出合法 `sort_field` 枚举
  （`relevancy / representative_date / source_date / full_title /
  copyright_number_for_display / latest_transaction_date`），
  补齐后仍返 **500**。其余端点 404。**未取得登记记录，未绕过任何限制。**
  （与 #114 Peplau 探测遇到的是同一个故障。）
- **HathiTrust** Bib API 可达，按 OCLC 查无对应记录；全文检索未再尝试。

---

## 三、开放渠道探测（逐条实跑）

### 3.1 OpenAlex —— 她被拆成两个作者 ID，合并后 236 件，独著 110 件

| author id | display | works |
|---|---|---:|
| `A5103268960` | Jean Watson（ORCID 0000-0002-3767-7467） | 101 |
| `A5089314771` | Jean Watson（Texas Tech 误挂） | 136 |

游标全量取回、去重 → **236 件**。剔除同名他人后
（Jean-Paul Watson 的暗物质／液氙、J. Watson 的航空材料与麻风病学等），
**独著 110 件**，其中 `is_oa=true` 的只有 **14 件**，且分散在 2002–2023。

**1976–2001 这 26 年的独著 —— 一件 OA 都没有。**
包括《Nursing's scientific quest》(1981)、《The Lost Art of Nursing》(1981)、
《Nursing on the caring edge》(1987)、《Caring knowledge and informed moral passion》(1990)、
《Postmodernism and Knowledge Development in Nursing》(1995)、
《The Theory of Human Caring: Retrospective and Prospective》(1997) —— **全 closed**。

### 3.2 Unpaywall 全量核验 249 个 DOI —— OA 31，真正能取的 8

DOI 来源 = OpenAlex 236 件 ∪ Crossref 筛出的 219 件，去重后 **249 个**。

```
closed 218 | gold 12 | bronze 8 | green 8 | hybrid 3
```

31 个 OA 里：

- **12 个是同名他人**（postpartum sexual health 的 4 个 preprint 版本、
  1949 年 J. Biol. Chem. 的肌酸合成、1950 年密歇根社会心理学等）；
- **6 个是她的合著**（Wei & Watson 2019/2021、Brewer/Anderson/Watson 2020、
  Christopher/de Tantillo/Watson 2020、Avilés González 等 2019、Koithan 等 2017/2020）
  —— 她是第 2–5 作者，**文体不是她的**，本次不计入一手；
- **5 个是 Wiley bronze/hybrid 独著** → 实测全部 **403，未绕过**（见 §5）；
- **8 个真取到**（§4）。

### 3.3 各渠道逐条结果

| 渠道 | 查法 | 结果 |
|---|---|---|
| **DOAJ** | `bibjson.author.name:"Jean Watson"` | total **10**，其中她署名 10（4 篇独著）。另全文检索 `"Jean Watson"` total 92，作者含她的仍是那 10 条 |
| **SciELO** 检索门户 | `search.scielo.org` | **403**（`bunny-shield` 「Establishing a secure connection」）。**未绕过。** 但 `scielo.br` 的**单篇文章直链可取**，本次两篇经此取得 |
| **Redalyc** | `redalyc.org/pdf/714/*` | 可取。取到的是 SciELO 同一篇的镜像（含葡文全文），**按同源不另计份数** |
| **Europe PMC** | `AUTH:"Watson J" AND "caring"` | hitCount **146**；`OPEN_ACCESS:y` 子集 **43**，逐条核对**只有 6 条是她**，且**全是合著** |
| **PAHO IRIS** | `/server/api/discover/...` 与 `/rest/discover/...` | 两条路径均 **HTTP 403**（Apache Forbidden），换浏览器 UA 仍 403。**未绕过。**（#113/#114 时这条路可用，本次不可用；且她的产出期 1979– 也在 PAHO 科学出版物译介期之外） |
| **WHO IRIS** | `query="Jean Watson"` | total **1**，是一本麻风病自助手册，**不是她** |
| **govinfo** | `DEMO_KEY` POST search，`"Jean Watson" AND nursing` | count **11**：2 条 USCOURTS、3 条 CRECB 1965/1993、1 条 SERIALSET 1994、2 条 Federal Register 1970/1971 等，**无一条是她署名**。→ **没有联邦政府出版物这条 PD 路** |
| **CORE** | `api.core.ac.uk/v3` | 301 重定向未取到内容 |
| **BASE** | `api.base-search.net` | `{"error":"Access denied for IP address ..."}`，**未绕过** |
| **LA Referencia** | vufind 检索 | 页面可达但检索结果为空壳（4,414 字节） |
| **CiNii Research** | `cir.nii.ac.jp/opensearch` | `items 0` |
| **J-STAGE** | 检索 API `service=3&text=Watson caring` | 30 条中她署名 2 条 —— **正是 §4 取到的那两篇** |
| **archive.org** 全文检索 | — | 未使用（书扫描全部闭架，见 §3.4） |

### 3.4 archive.org —— 她的 9 个书扫描，**全部闭架，一律未碰**

`creator:("Watson, Jean")` → **28 件**。按生年剔除同名他人：
`Watson, Jean, 1936-`（英国基督教儿童读物作者，占 15 件）、
`Watson, Jean L., d. 1885`（*The Songstresses of Scotland*）。
剩下 **`Watson, Jean, 1940-` 的 9 件**，用 `archive.org/metadata/<id>` 公开元数据逐条判定：

| identifier | 书 | `access-restricted-item` | collection |
|---|---|---|---|
| `nursingphilosoph0000wats` | Nursing: The Philosophy and Science of Caring (1985) | **true** | internetarchivebooks, printdisabled |
| `nursinghumanscie0000wats` | Nursing: Human Science and Human Care (1985) | **true** | internetarchivebooks, printdisabled |
| `nursinghumanscie0000wats_p3t2` | 同上（1999 重印） | **true** | internetarchivebooks, printdisabled |
| `ethicsofcareth00wats` | The Ethics of Care and the Ethics of Cure (1988) | **true** | **inlibrary** |
| `caringimperative00inge` | The Caring Imperative in Education (1990) | **true** | **inlibrary** |
| `postmodernnursin0000wats` | Postmodern Nursing and Beyond (1999) | **true** | **inlibrary** |
| `assessingmeasuri0000wats_m8m4` | Assessing and Measuring Caring (2002) | **true** | internetarchivebooks, printdisabled |
| `assessingmeasuri0000wats` | 同上（2009） | **true** | trent_university, printdisabled |
| `humancaringscien0000wats` | Human Caring Science: A Theory of Nursing (2012) | **true** | internetarchivebooks, printdisabled |

**9/9 全部 lending-only。一律未碰。**
→ **她的全部专著，一本都取不到。** 而她的理论主干（10 Caritas Processes、
transpersonal caring relationship、carative factors 十项）**正是写在这些书里的**。

### 3.5 ★ `conversations` 道：**访谈是有的，一篇都不开放**

这一条是 `min_lanes 6` 的死结（#115 Slavyanov 就栽在这里），所以**单独查了一遍**。

已确认存在、**全部 `is_oa=false`** 的访谈／对谈：

| 年 | 篇名 | 出处 | 状态 |
|---|---|---|---|
| 2002 | Aesthetics, postmodern nursing, complementary therapies and more: an Internet dialogue | *Complementary Therapies in Nursing and Midwifery*，`10.1054/ctnm.2001.0585` | closed（Elsevier） |
| 2005 | Caring for our future: an interview with Jean Watson. Interview by Carla Mariano | PMID 16018300 | closed |
| 2007 | The Power of Wholeness, Consciousness, and Caring: A Dialogue on Nursing Science | *Int J Human Caring*，`10.20467/1091-5710.11.3.52` | closed |
| 2008 | 同上（*Advances in Nursing Science* 版），`10.1097/01.ans.0000311535.11683.d1` | LWW | closed；DigitalGeorgetown handle `10822/959183` 实测 **404** |
| 2009 | From Theory to Practice（Clarke, Watson, Brewer） | *Advances in Nursing Science* | closed |
| 2010 | An interview with Jean Watson, HNY 2010. Interview by Lynne Nemeth | PMID 21162385 | closed |
| 2021 | **Nursing Is the Light in Institutional Darkness: A Dialogue With Dr. Jean Watson** | *Nursing Science Quarterly*，`10.1177/08943184211051349` | closed（Sage） |

**→ `conversations` = 0。** 不是没找到，是**找到了七件、七件全在墙后**。

### 3.6 三件「看着能取、实际取不到」的（如实记）

| 材料 | 索引怎么说 | 实测 |
|---|---|---|
| **RECIEN 2020**《El liderazgo de enfermería durante el COVID-19》/《Nursing Leadership during COVID19》（西英两版，她独著） | OpenAlex：`green`，LA Referencia 收录，`cc-by-nc-sa` | `revista.cep.org.pe/.../article/view/15`、`/16` 与 `/download/15/13`、`/download/16/14` **全部 404**。期刊改版，链接已死 |
| **Aquila (Univ. of Southern Mississippi)** `cadenhead_lectureship/1`《Caring Science as Sacred Science》2021-03-09 | 机构库有条目 | 落地页原文：`Document Type: Video` ／ `This document is currently not available here.` —— **只有影像，无转录本，无可下载件** |
| **日本赤十字広島看護大学 2000 年開学特別記念講演**《Re-considering Transpersonal Caring Theory and Practice》 | CiNii 有条目 `jairo.nii.ac.jp/0080/00000277` | JAIRO 已停服（**HTTP 000**），`cir.nii.ac.jp` 对应 crid **404** |

---

## 四、真取到的 8 份（全部她独著，全部 P1，**全部不是公有领域**）

| # | 文件 | 词数 | 年 | 载体 | 道 | 许可／版权 |
|---|---|---:|---:|---|---|---|
| 1 | `jstage-holistic-2002` | 2,992 | 2002 | J. Jpn. Acad. Nurs. Sci. 22(1):69-74，第4回国際看護学術集会**基調講演I** | expression | `© Japan Academy of Nursing Science` |
| 2 | `jstage-caritas-communitas-2004` | 3,831 | 2004 | J. Jpn. Acad. Nurs. Sci. 24(1):66-71，第23回日本看護科学学会**教育講演** | expression | `© Japan Academy of Nursing Science` |
| 3 | `tce-theory-human-caring-2007` | 4,427 | 2007 | *Texto & Contexto Enferm* 16(1):129-35，`10.1590/S0104-07072007000100016` | writings | CC BY-NC 4.0 |
| 4 | `mundosaude-cuidar-essencia-2009` | 4,629 | 2009 | *O Mundo da Saúde* 33(2):143-149，`10.15343/0104-7809.200933.2.2` | writings | 期刊持有（葡/英/西三语并排） |
| 5 | `tce-editorial-disciplina-2017` | 941 | 2017 | *Texto & Contexto Enferm* 26(4) 社论，`10.1590/0104-07072017002017editorial4` | writings | SciELO CC |
| 6 | `cietna-ciencia-cuidado-2018` | 2,198 | 2018 | *ACC CIETNA* 1(1):1-6，`10.35383/cietna.v1i1.169` | writings | `© 2018 Universidad Católica Santo Toribio de Mogrovejo`；Crossref 记 CC BY-NC-ND 2.5 PE |
| 7 | `opin-unitary-caring-2019` | 3,408 | 2019 | *NSC Nursing*（OPI Napoli），`10.32549/OPI-NSC-22` | writings | CC BY-NC-ND 4.0 |
| 8 | `pensarenf-unitary-caritas-2023` | 2,580 | 2023 | *Pensar Enfermagem* 27(1):e00296，`10.56732/pensarenf.v27i1.296` | writings | **`Copyright (c) 2023 Jean Watson`** + CC BY 4.0 |

**合计 25,006 词。**

八份的**署名与身份**都在正文里核过，例如 #1 扉页：
`Jean Watson, R.N., Ph.D., HNC, FAAN — Distinguished Professor of Nursing,
Endowed Chair in Caring Science, University of Colorado Health Sciences Center`；
#4 脚注：`Distinguished Professor Nursing. University of Colorado Denver.
Founder/Director Watson Caring Science Institute.`
—— **不是同名他人。**

### ★ 没有计入份数的重复件（**不缩不涨分母**）

- `redalyc.org/pdf/714/71416116.pdf` = #3 的 Redalyc 镜像（含葡文全文，8 页 4,524 词）
- `redalyc.org/pdf/714/71453540018.pdf` = #5 的 Redalyc 镜像（3 页 1,171 词）

两件都**真取到了**，但与 #3 / #5 **同源**，
按「独立源」计**不另算份数**。留在探测记录里，不留在 `raw/`。

---

## 五、失败清单（探过、取不到、原因；403 一律注明未绕过）

| 材料 | 原因 |
|---|---|
| 她的 **9 部专著全部** archive.org 扫描 | `access-restricted-item: true`，lending-only。**一律未碰** |
| JCN 2005 Guest Editorial（`10.1111/j.1365-2702.2005.01256.x`，独著） | `onlinelibrary.wiley.com` Cloudflare **403，未绕过** |
| JCN 2005 Commentary on Shattell（`10.1111/j.1365-2702.2004.01057.x`，独著） | 同上 **403，未绕过** |
| JAN 2006 Can an ethic of caring be maintained?（`10.1111/j.1365-2648.2006.03848_2.x`，独著） | 同上 **403，未绕过** |
| JAN 2018 Nursing's global covenant with humanity（`10.1111/jan.13934`，独著） | 同上 **403，未绕过** |
| JCN 2003 The Attending Nurse Caring Model（`10.1046/j.1365-2702.2003.00774.x`，Watson & Foster） | 同上 **403，未绕过** |
| RFIRI 2017 La place du caring en soins infirmiers（`10.1016/j.refiri.2017.05.001`，独著，Unpaywall 标 hybrid cc-by-nc-sa） | `doi.org` 跳 `articleSelectSinglePerm` 权限闸；直取 `sciencedirect.com/.../S2352802817300339` 返 **403，未绕过** |
| 7 件访谈／对谈（§3.5） | 全部 `is_oa=false`；Elsevier / LWW / Sage / IJHC 付费墙 |
| RECIEN 2020 西英两版 COVID 领导力社论 | 期刊改版，view/download 链接**全 404** |
| Aquila 2021 Cadenhead 讲座 | **Video only**，`This document is currently not available here` |
| 日赤広島 2000 開学特別記念講演 | JAIRO 停服 **HTTP 000**；CiNii crid **404** |
| 1976–2001 全部独著（含 1981 *The Lost Art of Nursing*、1990 *Caring knowledge and informed moral passion*、1995 *Postmodernism and Knowledge Development*、1997 *Retrospective and Prospective* 等） | OpenAlex 全部 `closed`；AJN/Nursing Forum/ANS/NSQ 付费墙 |
| University of Colorado Press eBooks 章节（2008 / 2018，共 6 章） | `closed` |
| Springer *Unitary Caring Science* 书章（Crossref 24 条） | 付费墙 |
| **PAHO IRIS** | `/server/api/` 与 `/rest/` 均 **403，未绕过** |
| **SciELO 检索门户** | bunny-shield **403，未绕过**（单篇直链可取） |
| **BASE** | IP 级 Access denied，**未绕过** |
| **CORE** | 301 重定向未取到内容 |
| **美国版权局 CPRS API** | 400 → 补齐 `sort_field` 后 **500**。**未取得记录** |
| **DigitalGeorgetown** `10822/959183`（2008 ANS 对谈） | **404** |

---

## 六、缺口定位

| 道 | 实测 | 说明 |
|---|---:|---|
| writings | **6** | 全是 2007–2023 的短篇理论文与社论，941–4,629 词。**她的理论主干在书里，书全部闭架** |
| expression | **2** | 两篇日本学会大会讲演稿（基調講演／教育講演）。**但要按实测读**：它们是讲演之后整理成的论文，不是逐字转录——`I want to` / `Let me` 各 **0** 次，`I am` 0／2 次，`we` 45／64 次。算 expression 是因为讲台文体与听众指向，**不是因为有口语转录** |
| conversations | **0** | **七件访谈／对谈全部在墙后**（§3.5）。这一条单项即令 standard/deep 死 |
| decisions | **0** | 无任何决策叙事文本 |
| timeline | **0** | 无生涯自述、无年表性一手材料。（Aquila 2021 讲座只有影像） |
| external | **0** | 二手评述极多（Pardede 2020、Ajesh & Chandran 2017、各国护理教科书章节等），**但全是 S2/S3，取多少都只会把一手占比往下拉**——按「不许缩／涨分母凑数」的规矩，一件不取 |

**根因**：她 **1940 年生、在世**，产出期 **1976–2025 整段落在 1976 年版权法之下**，
保护期 = **终身 + 70 年**。这不是「续展与否」的问题，
**是根本不存在通往公有领域的路径**——最早也要到她身后 70 年。

她的开放材料之所以比 Henderson / Peplau 多，**只因为她赶上了金色 OA 时代**，
拉美（巴西 SciELO、秘鲁 USAT／CEP）、南欧（葡萄牙 ESEL、意大利 OPI）
与日本的护理期刊愿意开放分发。**但开放分发是许可，不是版权失效。**

---

## 七、建议

1. **不按 deep 推进 #116**，也**不按 standard、不按 quick**——
   三档全部够不着，且 `conversations` 道为 0 是**结构性**的，不是抓得不够勤。
2. **一件都不许入库。** 8 份全部不是公有领域，见 `_DO_NOT_INGEST.md`。
   与 #113/#114 不同的是：那两位是「保护期还有二三十年」，
   **这一位是「保护期最早也要到 22 世纪」**。
3. **延后成因应记为新的一类，不要并进第三类。**
   第三类（Henderson/Peplau）是「产出期在版权内 + 被按时／自动续展」——
   **有确定的到期日**（2034–2066）。
   本件是「**作者在世，终身 +70**」——**没有到期日可写**。
   建议记为 **第五类：作者在世**。
4. **排期规则再收紧一格**：
   > 卒于 1930 年后 → 先跑可得性探测（#113/#114 已定）
   > **在世者 → 直接不排期，连探测都不必跑**（本件新增）
   本次探测的实际价值不在结论（结论如预期），而在 §2.3 那条反例
   与 §3.5 那张访谈清单——**它们是可复用的判据素材，不是本人物的语料**。
5. **★ §2.3 值得单独固化成一条检查**：
   **不许把聚合器（Unpaywall/OpenAlex）的 `license` 字段当版权判据。**
   实测 Unpaywall 把一篇 Wiley 在版权期内的社论标成了 `public-domain`，
   而同 DOI 的 Crossref 记录写的是 `onlinelibrary.wiley.com/termsAndConditions#vor`。
   照抄这一格 = 把受保护作品当 PD 入库。**这是一个已发生的、可复现的误判。**
