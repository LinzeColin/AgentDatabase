# #113 Virginia Henderson (1897-11-30 – 1996-03-19) — 语料可得性探测

探测日期：2026-08-04
结论：**够不着 deep 档的门。** 真取到全文的源 = **2 份**（门要 ≥45 份）。

---

## 一、结论摘要

| 判据 | 门 | 实测 | 结果 |
|---|---|---|---|
| 可用源总数 | ≥ 45 | **2** | 差 43 |
| 一手占比 (P1+P2) | ≥ 65% | 2/2 = 100% | 分母太小，无意义 |
| 六条道覆盖 | 6/6 | **2/6**（writings, expression） | conversations / decisions / timeline / external 全空 |

即使把所有「查到了但取不到」的自由阅读项全算进来（PMC 2 篇 + Wiley 1 篇 = 3 篇，实际都没下到），
天花板也只有 5 份。**与 45 份差一个数量级。**

两份到手的文本还高度同源：1958 年那篇是 1961 年那本书的前身会议论文，
按独立源计更接近 **1.5 份**。

---

## 二、版权状态查证结果

### 2.1 确认「仍受版权保护」——有硬证据

证据源：NYPL `cce-renewals` 数据集（美国版权局 Catalog of Copyright Entries 的机读转录），
`https://raw.githubusercontent.com/NYPL/cce-renewals/master/data/{1967-1,1983-from-db}.tsv`

**(a) Textbook of the Principles and Practice of Nursing, 4th ed. (1939)**
```
HARMER, BERTHA. Textbook of the principles and practices of nursing.
By Bertha Harmer & Virginia Henderson. 4th ed., rev.
© 29Aug39; A131865. Virginia Henderson (A); 14Apr67; R408306.
```
→ **1967 年由 Henderson 本人续展**。1939+95 = **2034 年前受保护**。

**(b) Bertha Harmer's Textbook of the Principles and Practice of Nursing, 5th ed. (1955)**
```
Virginia Henderson. Bertha Harmer's Textbook of the principles and practice of nursing.
A210898  1955-11-22  RE180356  1983-11-04  Virginia Henderson|A
```
→ **1983 年由 Henderson 本人续展**。1955+95 = **2050 年前受保护**。

**(c) Nursing Research: Survey and Assessment (1964, 与 Leo Simmons 合著)**
**(d) The Nature of Nursing (1966)**
→ 1964 年及以后出版，适用 1992 年 Copyright Renewal Act 的**自动续展**，
无需在 CCE 留续展记录即受保护（分别至 2059 / 2061）。已在 1993/1995 续展文件中确认无记录，与自动续展一致。

**(e) Basic Principles of Nursing Care (ICN, Geneva 1960)**
1987/1988 两年的续展记录中 grep `basic principles` 与 `council of nurses` **均为空**。
但这**不能推出公有领域**：该书是**瑞士出版的外国作品**，
1996-01-01 在源国仍受保护（Henderson 1996 年卒，life+70 = 2066），
故经 URAA / 17 U.S.C. §104A **自动恢复美国版权**，无需续展。
旁证：ICN 1997 年重印本在 archive.org 上是 lending-only。
→ **按铁律「不确定的一律当作仍受版权保护」处理。**

### 2.2 查不准（但不影响结论）

- **AJN 期刊论文（1935–1970）**：未逐篇查期刊续展（Class B 记录不在 NYPL 书目数据集内）。
  **但此项为 moot**——见 §3.2，无论版权如何，**没有任何开放全文渠道**。
- **HathiTrust**：catalog 与 Bib API 对本机一律 403，未能取得 rights code。
  鉴于 (a)(b) 的续展已证实，HathiTrust 必然标 `ic` / limited，无实际影响。

### 2.3 确认「开放可取」——但严格说不是公有领域

**PAHO / WHO IRIS 的两份**（见 §4）由版权方 PAHO 自己在开放仓储中分发，
非付费墙、非绕过任何访问控制。但**它们不是公有领域**，
是「出版方授权开放（publisher-open）」。本记录如实标注，不冒充 PD。

---

## 三、开放渠道探测

### 3.1 已核实为 lending-only（`access-restricted-item: true` + `inlibrary`）——一律未碰

用 `https://archive.org/metadata/<id>` 公开元数据 API 判定，未尝试任何绕过。

| identifier | 年 | 内容 |
|---|---|---|
| `basicprincipleso0000hend` | 1997 | Basic Principles of Nursing Care (ICN) |
| `natureofnursingd0000hend` | 1966 | The Nature of Nursing |
| `bwb_Y0-BDO-729` | 1966 | The Nature of Nursing（另一扫描） |
| `principlespracti0000hend` | 1978 | Principles and Practice of Nursing, 6th ed. |
| `textbookofprinci1939harm` | 1939 | Textbook…4th ed.（Harmer & Henderson） |
| `textbookofprincie4harm` | 1939 | 同上，另一扫描 |
| `virginiahenderso0000hend` | 1995 | A Virginia Henderson Reader |
| `contemporaryamer00safi` | 1977 | Safier, *Contemporary American Leaders in Nursing: An Oral History*（含 Henderson 章）|

最后一条是本次最可惜的一项——它是唯一已知的、成规模的 Henderson **口述史**（conversations 道），
被 lending 锁住。

### 3.2 American Journal of Nursing —— 开放刊期止于 1930，她的文章全在门外

`archive.org` `sim_american-journal-of-nursing*` 集合共 **807 件，全部非 inlibrary（开放）**，
但按年分布决定性地说明问题：

```
1900–1930：每年 21–26 件（= 全部刊期）
1931–1939：每年 2 件（仅 index 卷，正文刊期已撤下）
1955：      仅 2 件 index
```

Henderson 最早的 AJN 文章是 **1935 年**（"Medical and Surgical Asepsis"，经 Crossref 核实），
正好落在开放区之外。她的 AJN 文章（1935, 1936, 1937, 1938, 1941, 1955, 1963, 1964, 1969, 1970）
**没有一篇能取到全文**。

### 3.3 OpenAlex 全量 OA 扫描 —— 87 条中 OA 仅 5 条，真能用的 0 条

`https://api.openalex.org/works?filter=raw_author_name.search:Virginia Henderson,publication_year:<1997`
→ total 87。其中 `is_oa=true` 仅 5 条：
- 2 条是同名他人（AAPG Bulletin，地质学 barrier island）——**不是她**
- 1 条 `revistas.unal.edu.co` 1989 —— 是征文比赛结果公告，**不是她署名作品**
- 1 条 J Adv Nurs 1987 "The Nursing Process in Perspective" —— Wiley 标 free access，
  实测 `pdfdirect` 返回 Cloudflare `Just a moment...` 挑战（403）。**未绕过，未取到。**
- 1 条 PMC198649（见下）

**其余 73 条全部 `is_oa=false`**，含她全部核心论文
（J Adv Nurs 1978 "The concept of nursing"、AJN 1964 "The Nature of Nursing"、
Nurs Res 1957 "An Overview of Nursing Research" 等）。

### 3.4 PMC —— 2 篇 Bull Med Libr Assoc，免费可读但取不到文本

| PMCID | 年 | 篇名 |
|---|---|---|
| PMC197540 | 1971 | Implications for Nursing in the Library Activities of the Regional Medical Programs |
| PMC198649 | 1972 | Dictionary for Nurses（书评） |

- efetch XML 返回 `The publisher of this article does not allow downloading of the full text in XML form.`（仅元数据）
- 网页版为**扫描图像**，无 OCR 文本层（HTML 抽取仅 3,578 字符，全是站点导航）
- PDF 直链 `https://pmc.ncbi.nlm.nih.gov/articles/instance/197540/pdf/mlab00154-0073.pdf`
  返回 HTML 拦截页（bot protection）。**未绕过，未取到。**
- 另：BMLA 由 Medical Library Association 持有版权，**并非公有领域**。

### 3.5 其余渠道——逐一探过，全空

| 渠道 | 结果 |
|---|---|
| WHO IRIS | 搜 "Virginia Henderson"：6 条，**无一条她署名**（全是 WHO 护理报告） |
| DOAJ | `author:"Henderson, Virginia"` → **total 0** |
| Wellcome Collection | 7 条命中，`availabilities: []` —— **纯纸本闭架，无数字化** |
| ICN 官网 icn.ch | 站内搜 Henderson + basic principles → 结果页**无 Henderson 提及**，无开放 PDF |
| Sigma / Henderson Repository | 以她**命名**，但收录的是**其他护士**的作品；非她本人文本 |
| AAHN aahn.org/henderson | 传记页，**只列书名不给全文链接**；唯一外链是 NHR 期刊订阅页 |
| Yale 在线展览 item/7814 | **仅一张照片**，无全文 |
| Yale ArchivesSpace | 命中 "School of Nursing, Yale University, Historical Collection"（repositories/12/resources/4129）——**实体档案，未数字化** |
| UVU freebooks nursing_history | 学生编写的传记章节 → **S3 三手**，不可作 P1 |
| SciELO | `search.scielo.org` 返回 403（bot 防护），**未绕过**；经 DOAJ/OpenAlex 交叉验证无她署名 OA 项 |
| BVS / LILACS | `pesquisa.bvsalud.org` 返回 Bunny Shield 挑战页 403，**未绕过** |
| Stanford Copyright Renewal DB | 返回 CAPTCHA，**未绕过**；改用 NYPL cce-renewals 数据集取得同等证据（见 §2.1） |
| HathiTrust | catalog / Bib API 均 403 |

---

## 四、真取到的源（2 份）

均来自 **PAHO IRIS**（`iris.paho.org`），走 DSpace 公开 REST API，无登录、无付费墙。

### 1. `raw/paho-principios-basicos-1961/paho-principios-basicos-1961.txt`
- **18,222 词 / 114,906 bytes**
- *Principios básicos de los cuidados de enfermería*，PAHO **Publicaciones Científicas No. 57**，1961-12
- 即 ICN *Basic Principles of Nursing Care* 的**西班牙文全本**
- 扉页明载：`El presente libro fue preparado por VIRGINIA HENDERSON, R.N., M.A.,
  Investigadora Asociada, Escuela de Enfermería de la Universidad de Yale`
  以及 `publicación con permiso del Consejo Internacional de Enfermeras`
- IRIS handle `10665.2/1340`，bitstream `58fc2ad4-770f-4a9b-bc83-12f2655669b1`
- 档级：**P1**（她亲笔署名专著）

### 2. `raw/paho-principios-fundamentales-1958/paho-principios-fundamentales-1958.txt`
- **15,557 词 / 99,120 bytes**
- *Principios fundamentales de los cuidados de enfermería*，
  **Bol Of Sanit Panam 1958;44(3):217**（= PubMed PMID 13510330）
- 署名 `VIRGINIA HENDERSON, R.N., Departamento de Sociología, Universidad de Yale`
- 脚注自述为提交国际会议的 **preliminary paper**（即 1960 年 ICN 那本书的前身）
- IRIS handle `10665.2/14985`，bitstream `85230f99-c7de-4366-95b3-11e53882d503`
- 档级：**P1**（她亲笔署名论文）

**同源性检查**：两文 8-gram 重合率仅 1.0%（160 / 15,530）——
词面重合低是因为**两次独立西译**，但**论点内容高度同源**，
按「独立源」计不应算作 2 份足额。

---

## 五、缺口定位

**不是「某几条道缺」，是「一手源在开放渠道里近乎为零」。**

| 道 | 状态 | 说明 |
|---|---|---|
| writings | **1.5** | 仅 PAHO 两份，且同源 |
| expression | **1.5** | 同上（同一批文本承载） |
| conversations | **0** | 全部访谈（Nurs Times / Nurs Mirror / Nurs Standard / Public Health Nurs 1984 / Trevor Clay 1988 两篇）**全付费墙**；唯一口述史 Safier 1977 是 lending-only |
| decisions | **0** | 无任何第一人称决策自述可取 |
| timeline | **0** | 无一手年表材料；Yale 档案未数字化 |
| external | **0（可得但不该要）** | 悼词/评论/研究文献量大，但全是 S2/S3，取多少都只会把 P1 占比往下拉 |

**根因**：她的产出期是 **1935–1994**，整段落在美国版权保护区内，
且两部主要教科书由**她本人亲自续展**——不存在「未续展而进入公有领域」的侥幸。
她不像 Nightingale / Lister / Virchow 那样有 19 世纪的公有领域主体。

---

## 六、失败清单（探过、取不到、原因）

| 材料 | 原因 |
|---|---|
| Textbook…4th ed. 1939（两个扫描） | archive.org lending-only；且 1967 已续展 |
| Textbook…5th ed. 1955 | 无开放扫描；1983 已续展 |
| Principles and Practice of Nursing 6th ed. 1978 | lending-only |
| The Nature of Nursing 1966（两个扫描） | lending-only；自动续展保护中 |
| Basic Principles of Nursing Care（ICN 英文原版） | lending-only；URAA 恢复版权 |
| A Virginia Henderson Reader 1995 | lending-only |
| Safier, *Contemporary American Leaders in Nursing* 1977（口述史） | lending-only |
| Nursing Research: Survey and Assessment 1964 | 无开放扫描 |
| Nursing Studies Index 全 4 卷 | Lippincott，无开放扫描 |
| AJN 1935/1936/1937/1938/1941/1955/1963/1964/1969/1970 各篇 | archive.org 开放刊期止于 1930；JSTOR / LWW 付费墙 |
| J Adv Nurs 1978/1980/1982/1987 各篇 | Wiley 付费墙；1987 那篇标 free access 但 Cloudflare 挑战，未绕过 |
| Nurs Res 1957 / 1977 | LWW 付费墙 |
| Int Nurs Rev 1965 / 1968 三篇 | Wiley 付费墙 |
| Nurs Outlook 1973 / 1989 | Elsevier 付费墙 |
| Holist Nurs Pract 1987、Nurs Adm Q 1985 | LWW 付费墙 |
| 全部访谈（Nurs Standard 1988×2、Nurs Times 1985、Nurs Mirror 1985、Public Health Nurs 1984 等） | 付费墙 |
| Bull Med Libr Assoc 1971 / 1972（PMC197540 / PMC198649） | 免费可读但**无文本层 + PDF 直链被 bot 拦截**；且非 PD |
| Yale School of Nursing Historical Collection | 实体档案，未数字化 |
| Stanford Copyright Renewal DB | CAPTCHA（未绕过；已用 NYPL 数据集替代） |
| HathiTrust catalog / Bib API | 403 |
| SciELO search / BVS pesquisa | 403 bot 挑战（未绕过） |

---

## 七、建议

1. **不要按 deep 档推进 #113。** 差 43 份，不是补几次抓取能填的缺口。
2. 若坚持保留 Henderson，唯一诚实的形态是 **shallow / 存疑档**，
   并在产品里明写「本人物仅有 1.5 份独立一手源，claim 覆盖不可能达标」。
3. 她属于已记录过的 **「延后新类别：归属不成立」** 之外的**新类别**：
   **「一手源确实是她的，但整段产出期落在版权保护内 + 本人亲自续展」**。
   建议在排期表里对 **20 世纪人物先跑本探测再排期**——
   Henderson 是 1996 年卒，本批 #100–#113 里凡卒于 1930 年后的都应先探。
