# #114 Hildegard E. Peplau (1909-09-01 – 1999-03-17) — 语料可得性探测

探测日期：2026-08-04
结论：**够不着 deep 档的门。** 真取到全文的源 = **3 份**（门要 ≥45 份）。
**公有领域源 = 0 份**——三份全部是 publisher-open / 开放许可，不是 PD。

---

## 一、结论摘要

| 判据 | 门 | 实测 | 结果 |
|---|---|---|---|
| 可用源总数 | ≥ 45 | **3** | 差 42 |
| 一手占比 (P1+P2) | ≥ 65% | 3/3 = 100% | 分母太小，无意义 |
| 六条道覆盖 | 6/6 | **4/6**（writings, expression, conversations, timeline 部分） | decisions 薄、external 空 |
| 公有领域占比 | —— | **0/3** | 三份均为出版方授权开放，非 PD |

三份合计 **30,347 词**。其中两份是同一批 PAHO 西班牙文译本，
第三份仅 1,139 词（含 339 词是译者写的介绍，非她本人）。

**与 Henderson (#113) 的区别**：Henderson 只有 1.5 份且全是纲领性论述；
Peplau 这三份里有一份是**真正的工作坊逐字问答记录**（69 问 / 72 答），
质地明显好，但**数量仍差一个数量级**。

---

## 二、版权状态查证结果

### 2.1 《Interpersonal Relations in Nursing》(1952) —— **已续展，硬证据**

证据源：NYPL `cce-renewals` 数据集（美国版权局记录的机读转录），
文件 `https://raw.githubusercontent.com/NYPL/cce-renewals/master/data/1980-from-db.tsv`
（47 个年度文件全下、全 grep，`peplau` 全库**仅此 1 条**命中）：

```
auth  : Hildegard E. Peplau, foreword by R. Louise McManus.
titl  : Interpersonal relations in nursing.
oreg  : A62979      odat: 1952-01-14
id    : RE66969     dreg: 1980-09-29
claimants: Productions Corporation|PWH
```

- 原注册 **A62979 / 1952-01-14**，续展 **RE66969 / 1980-09-29**。
- 续展窗口核对：依 17 U.S.C. §305「著作权期均延至该年年底」，
  1952 年作品的第一期至 **1980 年底**届满，续展年即 1980 年 →
  **1980-09-29 在窗口内，续展有效**。
- 期限：出版后 95 年 → **2047 年底前受保护，2048-01-01 才进入公有领域**。
- 备注：claimant 字段 `Productions Corporation|PWH` 疑似 NYPL 解析截断，
  但 auth / titl / oreg / id 四项无歧义，不影响判定。

### 2.2 《Basic Principles of Patient Counseling》(1964) —— **自动续展，受保护**

- 1964 年由 **Smith Kline & French Laboratories**（Philadelphia）出版并持有版权
  （由 PAHO 译本扉页的版权声明直接证实，见 §4.1）。
- 落在 **1992 年 Copyright Renewal Act 的 1964–1977 自动续展区间**，
  无须在 CCE 留续展记录即受保护 → **2059 年底前受保护**。
- 交叉验证：47 个 CCE 文件全库 grep `patient counseling` = **0 命中**，
  与「自动续展、无需申报」一致，**不能反推为公有领域**。

### 2.3 其余产出（1947–1999）—— 全在版权期内且全在付费墙后

- Crossref 全量：`query.author=Peplau` 取回 286 条，按 given name 过滤出
  **Hildegard 署名 113 条**。逐条查 Unpaywall：**`is_oa=true` 仅 2 条**（见 §3.4）。
- 113 条中 30 条带 license 字段，**全部是 Wiley / Sage / Elsevier / Springer 的 TDM 许可**
  （`onlinelibrary.wiley.com/termsAndConditions`、`journals.sagepub.com/page/policies/text-and-data-mining-license`、
  `elsevier.com/tdm/userlicense`、`springer.com/tdm`）——**没有一条 CC 许可**。

### 2.4 未能取得的第二重证据（如实记录）

- **美国版权局 CPRS API**（`api.publicrecords.copyright.gov`）：端点可达，
  `advance_search/` 返回 400 并吐出合法 `sort_field` 枚举，
  但补齐后仍 500。**未取得记录，未绕过任何限制。**
- **Stanford Copyright Renewal DB**：按 #113 的经验为 CAPTCHA，本次未再尝试。
- **HathiTrust**：`babel.hathitrust.org` 全文检索 **403**；Bib API 可达但无对应 OCLC 记录。

---

## 三、开放渠道探测

### 3.1 American Journal of Nursing —— 开放刊期止于 1930，她的文章**全在门外**

`archive.org` `identifier:sim_american-journal-of-nursing*` 共 **807 件**，按年分布：

```
1900–1930：每年 5–26 件（= 全部刊期）
1931–1979：每年 1–3 件（仅 index 卷）
```

她最早的 AJN 文章是 **1947 年**（"Panel Discussion"，经 OpenAlex/Crossref 核实），
整段 1947–2000 的 AJN 产出（Loneliness 1955、Talking with Patients 1960、
Interpersonal Techniques 1962、The Impact of an Image 1964、Mid-Life Crises 1975 等）
**一篇也取不到全文**。此项与 #113 Henderson 的结论完全一致。

### 3.2 archive.org 的三个扫描本 —— **全是 lending-only，一律未碰**

用 `https://archive.org/metadata/<id>` 公开元数据 API 判定：

| identifier | 内容 | `access-restricted-item` | collection |
|---|---|---|---|
| `interpersonalrel00pepl` | Interpersonal Relations in Nursing (1952 初版) | **true** | internetarchivebooks, americana, printdisabled |
| `interpersonalrel0000pepl` | 同上（1988 重印） | **true** | internetarchivebooks, printdisabled |
| `interpersonalthe0000unse` | Interpersonal Theory in Nursing Practice: Selected Works (1989) | **true** | internetarchivebooks, **inlibrary**, printdisabled |

`title:("patient counseling")` 搜索 8 件命中，**无一件是她的书**（全是药学患者教育材料）。
→ 《Basic Principles of Patient Counseling》**英文原本无任何开放扫描**。

注：archive.org 搜 `Peplau` 共 95 件，绝大多数是**同名他人**——
社会心理学家 **Letitia Anne Peplau**（UCLA 孤独感量表作者，占了 60+ 件）
与 **Günter Emil Franz Peplau**（1940 年药学论文）。已全部按作者剔除。

### 3.3 OpenAlex —— 115 条，OA 仅 2 条

`https://api.openalex.org/works?filter=raw_author_name.search:Hildegard Peplau` → total **115**。
`is_oa=true` 只有 2 条，即 §3.4 的两条。其余 113 条含她全部核心论文
（Nursing Science Quarterly 1988/1992/1994/1997、Perspectives in Psychiatric Care 1963/1968/1980、
Nursing Forum 1964/1966/1969、J Psychosoc Nurs 1982/1985/1989、Arch Psychiatr Nurs 1996 等）
**全部 `is_oa=false`**。

### 3.4 Unpaywall 全量核验 113 个 DOI —— OA 2 条，可取 1 条

| DOI | 年 | 篇名 | oa_status | 实测 |
|---|---|---|---|---|
| `10.1097/00000446-197005000-00013` | 1970 | PRESENT EXECUTIVE DIRECTOR RESPONDS TO MRS. WHITAKER (AJN) | bronze | **取不到**：`pdfs.journals.lww.com` 直链返回 Cloudflare `Just a moment...`（HTTP 403）。**未绕过。** |
| `10.17533/udea.iee.16928` | 1998 | Palabras de aceptación del premio Christiane Reimann | gold, CC-BY-NC-SA | **取到**（见 §4.3） |

### 3.5 PAHO IRIS —— 本次唯一有实际产出的渠道

DSpace 公开 REST API，无登录、无付费墙。全库 `query=Peplau` → **total 11**，
逐条核对作者与全文后，**她本人有内容的只有 2 条**（见 §4.1、§4.2）。
另外用 `"Peplau, Hildegard"` 作者式检索 → total **1**；
`Hildegard` → total 9；`enfermería psiquiátrica` → total 212（逐条核对无新增她署名项）。
→ **PAHO 这条路已经挖到底，就是 2 份。**

### 3.6 其余渠道 —— 逐一探过，全空或全挡

| 渠道 | 结果 |
|---|---|
| **DOAJ** | `bibjson.author.name:"Peplau"` → total **4**，**无一条是她**（土壤学 T. Peplau、蛋白工程 E. Peplau、护理学 G. P. Kauling 等） |
| **Europe PMC** | `AUTH:"Peplau HE"` → hitCount **63**，`isOpenAccess=Y` / `inEPMC=Y` / `hasPDF=Y` = **0 条** |
| **ERIC**（api.ies.ed.gov） | `author:"Peplau, Hildegard"` → **0**；泛搜 `Peplau` → 24 条，**无一条她署名** |
| **OpenAIRE** | 泛搜 total 297，过滤出 Hildegard 署名 **12 条**，`bestaccessright` 全为 `unspecified` 或 `Closed Access`，**无一条有 OA 全文** |
| **WHO IRIS** | `query=Peplau` → total **17**，**无一条她署名**（详见 §5 的旁证发现） |
| **CORE**（api.core.ac.uk） | Cloudflare **403**，**未绕过** |
| **SciELO**（search.scielo.org） | **403** bot 防护，**未绕过** |
| **BVS / LILACS**（pesquisa.bvsalud.org） | **403** bot 防护，**未绕过** |
| **HathiTrust** 全文检索 | **403** |
| **archive.org** 全文检索 API（ia-fts） | 连接失败（HTTP 000） |
| **govinfo**（美国政府出版物，PD） | `query=Peplau` → **43** 条，逐条核对：4 条 USCOURTS 是 Letitia Anne Peplau 专家证词；15 条 SERIALSET 是《U.S. Army Register》退役名册；CRECB 1971/1980/1988 与 GOVPUB 数条为提及。**无一条是她署名的可用文本。** |
| **Rutgers Oral History Archives** | 站内搜 **404** |
| **AAHN**（aahn.org/peplau） | **404** |
| **NLM Digital Collections API** | 返回 **HTTP 202 + 0 字节**（异步任务），始终未拿到结果 |

### 3.7 档案：两处大馆藏，**都没有数字化**

| 馆藏 | 内容 | 状态 |
|---|---|---|
| **Penn / Barbara Bates Center**，*Hildegard E. Peplau papers, 1949–1987*，call number **MC 59** | 含 **Box 1 Folder 2「Oral history, psychiatric nursing career, conducted by Patricia D'Antonio, PhD., 1985」**，以及 Rutgers / Columbia Teachers College 的教学与行政档案 | finding aid 原文：材料「**physically available in their reading room, and not digitally available through the web**」。Access Restrictions 写「This collection is unrestricted」，但 Use Restrictions 写「Copyright restrictions may apply」。**实体闭架，无在线全文。** |
| **Schlesinger Library (Radcliffe/Harvard)**，*Papers of Hildegard E. Peplau, 1923–1984*；*Audiotape collection, 1984–1998*；*Additional papers, 1922–2010* | 她 1984 年亲自捐赠，另有影音件 T-165 / Vt-41 | HOLLIS finding aid 三个 URL 本机均 **404**，未能取回 finding aid 正文。**无任何证据表明有公开转录本。** |

**这是本次最可惜的一项**：D'Antonio 1985 年那份口述史是已知唯一成规模的 Peplau 访谈转录，
被锁在费城的阅览室里。conversations 道本来能靠它撑起来。

---

## 四、真取到的源（3 份）

### 4.1 `raw/paho-orientacion-paciente-1968/paho-orientacion-paciente-1968.txt`

- **21,176 词 / 65 页**
- *Principios básicos para la orientación del paciente —— Extractos de la transcripción de
  dos grupos de trabajo en enfermería clínica en hospitales psiquiátricos*
- **PAHO Publicación Científica No. 167，1968 年 11 月**
- 署名：`por Hildegard E. Peplau — Enfermera Diplomada y Doctora en Educación,
  Profesora de Enfermería y Directora del Programa para Graduados en Enfermería
  Psiquiátrica Superior, Rutgers, Universidad Estatal, Newark, New Jersey, E.U.A.`
- 即《**Basic Principles of Patient Counseling**》(2a edición, 3a impresión) 的**西班牙文全译本**
- IRIS handle `10665.2/1212`，bitstream `d6d941e1-e6cf-4978-9049-acf2d5333c67`
- **版权标注（扉页原文，不冒充 PD）**：
  `Reprinted with permission of Smith Kline & French Laboratories / Copyright © 1964
  Smith Kline & French Laboratories, Philadelphia, Pennsylvania, U.S.A.`
  → **publisher-open（PAHO 获授权分发），NOT 公有领域。**
- **本次质地最高的一份**：正文是**工作坊逐字问答**，
  `Enfermera:` 提问 **69 次**、`Profesora:`（= Peplau 本人）作答 **72 次**。
  含她第一人称的分歧自述，例如
  「Debo reconocer que muchas enfermeras están en desacuerdo conmigo acerca de la utilidad de esas actitudes.」
  （我得承认，很多护士在这些做法有没有用上跟我意见不同。）
- 档级：**P1**（她亲笔署名 + 逐字口述转录）

### 4.2 `raw/paho-vinadelmar-salud-mental-1970/paho-vinadelmar-salud-mental-1970.txt`

- **8,032 词**
- 篇名：*Preparación y funciones del personal de los equipos de salud mental comunitaria*
- 署名：`Dra. Hildegard E. Peplau`
- 载于 PAHO *Grupo de Trabajo sobre la Administración de Servicios Psiquiátricos y de
  Salud Mental, Viña del Mar, Chile, 14-19 de abril de 1969*（1970 年出版）
- IRIS handle `10665.2/1259`，TEXT bitstream `a45054e7-46bf-4586-a977-6709e4eee23c`
  （另一条重复记录 `10665.2/48017` 无 TEXT bundle）
- 脚注自述来源：`Tomado del Community Mental Health Journal` → **英文原文在 CMHJ（今属 Springer，付费墙）**
- 开篇即第一人称立场自述：
  「Sería presuntuoso por mi parte ofrecer sugerencias concretas para su aplicación en la América Latina…
  en este trabajo me limitaré a presentar mis observaciones personales y experiencias…」
- **publisher-open（PAHO 分发），NOT 公有领域。**
- 档级：**P1**
- 提取方式：整卷 58,598 词的 PAHO TEXT bitstream，按章节标题定位她那一章的起止
  （`PREPARACION Y FUNCIONES DEL PERSONAL` → 下一章 `Dr. Leonardo García Buñuel...`），只切出她的部分。

### 4.3 `raw/iee-premio-reimann-1998/iee-premio-reimann-1998.txt`

- **1,139 词**（其中 **792 词是她的致辞**，末 **339 词是译者写的《Presentación》——S2，非她本人**）
- *Palabras de aceptación del premio Christiane Reimann*
  ——**国际护士会（CIE/ICN）第 21 届四年一度大会，加拿大温哥华，1997 年 6 月 15 日**的领奖致辞
- 载 *Investigación y Educación en Enfermería*（安蒂奥基亚大学）**16(1)，1998 年 3 月，pp.105–107**
- DOI `10.17533/udea.iee.16928`；**gold OA，CC-BY-NC-SA**
- 西译者：Carmen de la Cuesta Benjumea（安蒂奥基亚大学国家公共卫生学院副教授）
- **PDF 是纯扫描图像、无文本层**（PyMuPDF 提取 3 页共 2 字符）。
  已用 **macOS Vision 框架（osascript JXA 桥）以 300 dpi 渲染后 OCR**，识别质量良好。
- 内容是她本人的生涯回顾（20 世纪护理三段变迁、她自己在医院附设护校受训的起点、
  以及她对 21 世纪的判断「本世纪的主导问题是『护士做什么』，下个世纪的关键问题将是
  『护士知道什么、以及怎样用这些知识造福他人』」）——**timeline 道唯一的一手材料。**
- 期刊页面自陈版权归 IEE 所有 → **开放许可（CC-BY-NC-SA），NOT 公有领域。**
- 档级：**P1**（她本人致辞部分）

---

## 五、探到但**不计入**份数的旁证（如实记录，不凑数）

**WHO 执行委员会正式记录中的护理专家咨询团名册**——她本人不是作者，
是名册上的一行，**当作 timeline 旁证记录，不算一份「源」**：

| WHO IRIS handle | 文件 | 年份 | 命中 |
|---|---|---|---|
| `10665/128069` | Appointments to expert advisory panels and committees | 1951 | `Miss H. E. PEPLAU`，列于 United States of America 项下 |
| `10665/134133` | Inscriptions aux tableaux d'experts et nominations aux comités d'experts | 1955 | `Miss H.E. PEPLAU` |
| `10665/130932` | Appointments to expert advisory panels and committees | 1956 | `Miss H. E. PEPLAU` |

→ 可据以确认「1951 年起即在 WHO 护理专家咨询团名册上」。
（同一批文件里另有一条脚注「Attended Expert Committee on Psychiatric Nursing」，
但 OCR 的星号标记无法可靠归属到她名下，**不作断言**。）

---

## 六、缺口定位

| 道 | 状态 | 说明 |
|---|---|---|
| writings | **2** | 两份 PAHO 西译（1968 书 + 1970 章），无一是英文原文 |
| expression | **1** | 由 §4.1 的逐字转录承载，是她真实的口头语体 |
| conversations | **1** | 只有 §4.1 的 69 问 / 72 答；D'Antonio 1985 口述史锁在 Penn 实体档案 |
| decisions | **0.5** | §4.1 里有案例判断与分歧自述，但没有独立的决策叙事文本 |
| timeline | **1** | §4.3 的 1997 生涯回顾 + §5 的 WHO 名册三条 |
| external | **0** | 悼词/评论/研究文献量大（Perspectives in Psychiatric Care 1978 专辑、Haber 2000 等），但全是 S2/S3，取多少都只会把 P1 占比往下拉 |

**根因，与 #113 同类但不同因**：
她的产出期是 **1947–1999**，整段落在美国版权保护区内；
旗舰著作 **1952 年那本被人在 1980 年按时续展**（RE66969），
第二本 **1964 年出版直接吃到 1992 年法案的自动续展**——
**两条路都堵死，不存在「漏续展而落入公有领域」的侥幸。**

与 Henderson 的差别只在**运气**：Peplau 有一本被 PAHO 完整西译并放进开放仓储，
而且恰好是逐字转录体，所以三份里有一份质地极好。**但这改变不了量级。**

---

## 七、失败清单（探过、取不到、原因）

| 材料 | 原因 |
|---|---|
| Interpersonal Relations in Nursing 1952（`interpersonalrel00pepl`） | archive.org lending-only；且 1980 年已续展 |
| Interpersonal Relations in Nursing 1988 重印（`interpersonalrel0000pepl`） | lending-only |
| Interpersonal Theory in Nursing Practice 1989（`interpersonalthe0000unse`） | lending-only（`inlibrary`） |
| Basic Principles of Patient Counseling 1964 **英文原本** | 无任何开放扫描；1964 年出版，自动续展保护中 |
| Peplau papers MC 59（Penn）含 D'Antonio 1985 口述史 | 实体阅览室，明确「not digitally available through the web」 |
| Schlesinger Library 三个 Peplau 全宗 + 录音带 T-165 / Vt-41 | HOLLIS finding aid 本机 404；无公开转录证据 |
| AJN 1947–2000 全部文章 | archive.org 开放刊期止于 1930；LWW 付费墙 |
| AJN 1970 那篇（唯一 bronze OA） | `pdfs.journals.lww.com` 返回 Cloudflare 挑战 403。**未绕过。** |
| Nursing Science Quarterly 1988/1992/1994/1997 | Sage 付费墙 |
| Perspectives in Psychiatric Care 1963/1968/1980/1999 | Wiley 付费墙 |
| Nursing Forum 1964/1966/1969/1999 | Wiley 付费墙 |
| J Psychosoc Nurs Ment Health Serv 1982/1983/1985/1989/1994/1995 | SLACK 付费墙 |
| Arch Psychiatr Nurs 1996 / Geriatr Nurs 1986 / Nurs Outlook 1999 | Elsevier 付费墙 |
| J Am Psychiatr Nurses Assoc 1995/1997 | Sage 付费墙 |
| Image/J Nurs Scholarsh 1971/1974/1997 | Wiley 付费墙 |
| Community Mental Health Journal 原文（§4.2 西译的英文底本） | Springer 付费墙 |
| CORE / SciELO / BVS-LILACS | Cloudflare / bot 挑战 403，**未绕过** |
| HathiTrust 全文检索 | 403 |
| archive.org 全文检索 API | HTTP 000（连接失败） |
| NLM Digital Collections API | HTTP 202 + 0 字节，异步任务始终无结果 |
| Rutgers Oral History Archives / AAHN | 404 |
| 美国版权局 CPRS API | 端点可达但 body 格式未摸对（400 → 500）；已用 NYPL 数据集取得等效证据 |
| Stanford Copyright Renewal DB | 按 #113 经验为 CAPTCHA，本次未尝试 |

---

## 八、建议

1. **不要按 deep 档推进 #114。** 差 42 份，不是补几次抓取能填的缺口。
2. 若要保留 Peplau，唯一诚实的形态是 **shallow / 存疑档**：
   语料就是那 30,347 词，而且集中在「患者会谈技术」这一个题域，
   她的护理理论主干（interpersonal relations 六阶段、四个护士角色）**一手文本全取不到**。
   产品里必须明写「本人物仅 3 份源、0 份公有领域、核心著作全部无法取得」。
3. 她与 Henderson 一起坐实了 **20 世纪人物的系统性障碍**：
   **产出期整段落在版权区 + 旗舰著作被按时续展或吃到自动续展**。
   建议把 **「卒于 1930 年后 → 先跑本探测再排期」** 固化成排期表的硬前置，
   而不是每次到了才发现。
4. **一条可复用的经验**：PAHO IRIS（`iris.paho.org` DSpace REST API）
   对 1950–1970 年代美国护理学家是一条稳定的开放渠道——
   Henderson 2 份、Peplau 2 份都出自这里。
   但它同时也是**上限**：PAHO 只译了各人一两本，挖到底就是个位数。
5. **OCR 能力已具备（可复用）**：本机**无 tesseract**，`swiftc` 因
   CommandLineTools 与 SDK 版本不匹配（`redefinition of module 'SwiftBridging'`）不可用。
   可行路径是 **`osascript -l JavaScript` 桥接 macOS Vision 框架**：
   先用 PyMuPDF 以 300 dpi 把页面渲染成 PNG，再调 `VNRecognizeTextRequest`
   （`recognitionLevel = 0` 即 accurate，`recognitionLanguages = ['es-ES','en-US']`），
   逐 observation 取 `topCandidates(1).string`。本次对 3 页西班牙文扫描件识别质量良好。
