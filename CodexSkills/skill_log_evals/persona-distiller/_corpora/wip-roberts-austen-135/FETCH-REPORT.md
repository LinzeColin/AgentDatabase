# Roberts-Austen #135 抓源报告

工作区：`_corpora/wip-roberts-austen-135/`　目标：`workspaces/william-chandler-roberts-austen/`
所有数字**都是跑完命令现算的**（命令见文末）。

---

## 一、结论一句话

**26 份来源、一手 25 份（0.9615）、6 条研究道全覆盖，standard 门（≥24 份 / ≥0.50 / 6 道）三项全过；
deep（≥45 份 / ≥0.65）未到，不硬凑。
但研究门自跑有 22 条 `research.authorship-unproven`——这是本轮最该报的数，成因逐份查清了，见第五节。**

---

## 二、语料构成（现算）

| tier | 份数 | 内容 |
|---|---|---|
| P1 一手 | 24 | Phil. Trans. A 全文 3 篇、Proc. Roy. Soc. 摘要 8 篇、Nature 署名短文与书评 9 篇、Cantor Lectures 1884、Canada's Metals 1898、Introduction to the Study of Metallurgy 1891、亲笔信著录卡 1898 |
| P2 一手·身后编选 | 1 | Roberts-Austen: A Record of His Work（Sydney W. Smith 编，1914） |
| S1 二手·同时代传记 | 1 | DNB 第二补编 vol.3 (1912) pp.222-223，撰稿人 T. E. James |
| **合计** | **26** | 正文合计 **2,872,737** 字节 |

- **一手占比 25/26 = 0.9615**（standard 门 0.50）
- **研究道**：writings 13／expression 7／conversations 3／decisions 1／timeline 1／external 1 —— **6/6 覆盖**
- `voice`：first-person 12／unknown 13／third-person 1。**默认 unknown，只在实测第一人称（`I`+动词、`my`+名词）计数 ≥2 时才写 first-person**
- `tier_reason`：**26/26 都写了**，零空缺
- `derived_from`：**26 份全空——这是正常的**（见第三节）
- 回读自验：**原文 sha256 26/26 相符，归一件 sha256 26/26 相符**

### ★ 必须自己说破：26 份不等于 26 处独立证据

- `philtrans05512448`（Proc. Roy. Soc. 58 摘要）与 `philtrans09730582`（Phil. Trans. A 187 全文）
  是**同一场 1896 年 Bakerian Lecture 的两种印本**；
- `philtrans05894557` 与 `philtrans00706421` 是**同一篇 Osmond 合著论文**的摘要与全文；
- `philtrans01205368`（rspl.1900.0004）与 `philtrans09607756`（rspl.1900.0005）
  **页面范围物理重叠**——前者第 10,389 字起已经是后者的署名行。

三对已在各自 `notes` 里写明。**按「独立著作单位」算，26 份约合 23 件。**

★ 刻意**不入库**的重复件：`cu31924004123323`／`b28080592`／`cihm_11195`（Canada's Metals 的另三个扫本）、
`anintroductiont02robegoog`／`anintroductiont03robegoog`／`cu31924031266418`／`in.ernet.dli.2015.217091`
（Introduction to Metallurgy 的其它版次与异扫）、
`paper-doi-10_1098_rspl_*` 全 8 件（**与 `philtrans*` 是同一 DOI 的同一篇，只是 archive.org 上有两条记录**）。

★ 刻意**不当一手**的：`metallurgygold*`／`metallurgyofiron00turnrich`／`b28083088`——
archive.org 的 creator 字段里有他的名字，但那是 **Griffin 冶金丛书的主编身份**，
书是 T. K. Rose 与 Thomas Turner 写的。**「与他有关 ≠ 他写的」**，本轮一份也没收。

---

## 三、`--derived-from` 一条都没填——因为一本书也没切

本人物的一手主体是**单篇论文与学会报告**，各自带署名；两部专著
（Introduction to Metallurgy 747,625 字、A Record of His Work 1,240,593 字）
是**整册入库、不切段**的，扉页署名就在同一份文件里。

**没有「同一载体切成多段」的情形，因此 `derived_from` 全空是正确状态，不是漏填。**

---

## 四、六条研究道（抓源通道）

1. **archive.org 元数据检索**（`advancedsearch.php`）——按 creator 六种写法穷举（`Roberts-Austen`／`Roberts, W. C.`／`W. CHANDLER ROBERTS`…），得 48 条候选
2. **archive.org 条目元数据**（`metadata/<id>`）——取 DOI 与文件清单；**DOI 是本轮去重的关键**（`rsta.*` 是 Phil. Trans. 全文、`rspl.*` 是 Proc. Roy. Soc. 摘要）
3. **archive.org 全文下载**（`download/<id>/<id>_djvu.txt`）——逐份取正文
4. **Wikisource Page 名空间原文**（`Page:…djvu/222`、`/223` 的 `action=raw`）——DNB 第二补编条目
5. **参考工具书交叉核对**——DNB 1912 补编 / Britannica / Royal Mint Museum / Grace's Guide / Royal Society Science in the Making / Wikipedia
6. **同名者底册检索**——逐人查 Wikipedia／Wikisource Author 页／ANB，建 19 条候选册

★ 通道自检：Wikisource 的 `action=query&prop=extracts` 对 Page 名空间**返回空串**
（`len 0`，HTTP 200）——若照直报「拿不到」就错了；改走 `action=raw` 立刻拿到 5,256/5,358 字节。
**「空结果」在「真没有」与「接口用错」两种情况下长得一模一样。**

---

## 五、★★★ 研究门自跑结果：22 条 `authorship-unproven`

```
python3 scripts/quality_check.py "$TGT" --phase research   → passed: false, exit 1
```

| 项 | 数 |
|---|---|
| 来源门 `source.minimum` 24 | **26 ✓** |
| 一手占比门 0.50 | **0.9615 ✓** |
| 研究道覆盖门 6 | **6 ✓** |
| `authorship`：P1 声称为本人所著 | 24 |
| `authorship`：**已证实归属** | **2** |
| **`research.authorship-unproven`** | **22** |
| `research.source-unclaimed` | 16 |
| `research.attribution-basis` | 1（historical 人物未声明 `attribution_basis`） |
| `research.lane-completion` | 1（六条研究道正文尚未写——**那是研究员的活，不是抓源员的**） |

**只有 2 份过了归属门**：`philtrans00429265`（A-signature-block）与
`paper-doi-10_1038_060173c0`（A-discussion-turn，证据照录 `to the Iron and Steel Institute, Prof. Sir W. Roberts-Austen`）。

### 22 条不是「材料可疑」，是**判据够不到这个人的署名形态**——逐份查清了

| 拦下它的机制 | 份数 | 印本照录（逐字） |
|---|---|---|
| **姓氏 OCR 讹形**（R→K/B/E、连字号后有空格、`W. 0.` 用 0 代 C） | 7 | `By W. Chandler Koberts- Austen, F.RS`／`By W. C. Roberts- Austen, C.B., F.R.S.`／`By Professor Sir W. Boberts-Austen, K.C.B., P.B.S.`／`BY W. 0. KOBERTS-AUSTEN, C.B., F.H.S.` |
| **1885 年前的旧姓**（`W. Chandler Roberts`，而 `SURNAME` 是 `Roberts\-Austen`） | 4 | Nature 15/20/21 三处文末签名 `W. Chandler Roberts`；1884 Cantor 扉页 `BT W. CHANDLER ROBERTS, RR.S.` |
| **Nature 整版扫描的文末签名**：与正文末句同一行（3 份），或独占一行但落在文件 74.7%／70.4% 处且无地址块（2 份） | 5 | `…by traces.” W. C. Roberts-Austen.`／`Illinois Steel Company. W. C. Roberts-Austen.`／独占行 `W. C. Roberts-Austen,` |
| **署名不带教名或首字母** | 2 | `BY PROFESSOR ROBERTS-AUSTEN, C.B., D.C.L., F.R.S.`／`By M. F. Osmond and Professor Roberts- Austen, C.B., F.R.S.` |
| **署名与篇名同一行 / 被换行拆开** | 2 | `" Ot) Surfusion in Metals and Alloys." By W. C. Roberts-Austen, C.B., D.C.L., F.R.S.`（未过 structural）；`…By W. C.`↵`Roberts-Austen, C.B., F.R.S.,`（`name_rx` 用 `[ \t]+`，跨不过换行） |
| **扫描页范围不含署名行** | 1 | `philtrans08066202`：只有版口 `162 Sir W. C. Eoberts-Austen and Dr. T. K. Eose.` |
| **落盘的是馆藏著录卡，本无印本署名** | 1 | `ROBERTS-AUSTEN (Sir William C andler, F.R.S.; metalluy Ist; 1843 -1962) A.L..S:` |
| 合计 | **22** | |

三条**结构性**的（不是这批扫描件的偶然）：

1. **`build_patterns('William Chandler Roberts-Austen')` 生成的 `SURNAME` 是 `Roberts\-Austen`，
   与他 1885 年前的任何一份都匹配不上**。实测：`ocr_byline_evidence` 那条路也一样——
   `'W. CHANDLER ROBERTS' → SURNAME match? False`。**改姓这件事上游判据不知道。**
2. **`name_rx` 要求「名 + 姓」，而英式印本大量署 `By Professor <姓>`——教名与首字母一个都没有。**
   这与 Carver #127 的「名可以是缩写」是同一类，只是再进一步：**名可以完全没有**。
3. **`BYLINE` 的 `structural` 要求署名在行首，而 Proc. Roy. Soc. 的定式是
   `" 篇名。" By 作者` 排在同一行。**

**我没有去改判据让它变绿**（那是为了过门放宽判据）。
三条都写在这里，判据要不要长出 `A-byline-ocr` 的姓氏容错、
`A-byline-no-forename`、以及「改姓人物的第二姓氏」声明位，是待裁定的事。

### 我可以选、但没选的那条退路

`quality_check.run_authorship_gate` 对 `subject_origin == historical` 且
`meta['attribution_basis']` 为 dict 的目标**不报 error，只记 metrics**。
本人物确实是 historical（已按实定），但我**没有为了让这 22 条消失去声明 `attribution_basis`**——
声明一下，报告里就只剩一行「22 条已按已声明的归属依据放行」，数字被藏进 metrics。
**任务要的是把这个数报上来。**

---

## 六、抓源过程里打回来的三个真缺陷

### ⑴ ★ 我用了不存在的字段名做回读自验，得到「0/26 相符」

第一版核算写的是 `r.get('sha256')`——**本 schema 里那个字段叫 `checksum`**，
`.get` 返回 `None`，26 份逐一比对全部不等，输出 **`回读自验 sha256 相符 0/26`**。
这个数字看起来严重且可信，差点写进报告。改用正确字段后是 **26/26**。
**空默认值把「没这个字段」读成了「校验失败」**——与 `[[empty-default-swallows-unknown]]` 同形，
只是这次倒向了「看起来有问题」而不是「看起来没问题」，所以我才发现。

### ⑵ 判据里的理由我没跑就写了，写反了

`namesake-criteria.json` 第一版给禁区 `William Roberts` 的理由是
「它会命中 `William Chandler Roberts-Austen`」——**跑出来不会**（中名把两段隔开）。
真正的理由要去语料里找：全 26 份 `William` 紧挨 `Roberts` 只有 2 处、两处都是他自己、
其中一处是**他本人著作目录的标题行**。
**结论相同、理由完全不同**，而结论对理由错是最难发现的一种。详见 NAMESAKE-GUARD-实测.md 第五节。

### ⑶ `philtrans*` 与 `paper-doi-10_1098_rspl_*` 是同一篇的两条记录

archive.org 上这两族条目**共用同一个 DOI**（例：`philtrans00429265` 与
`paper-doi-10_1098_rspl_1890_0102` 都是 `10.1098/rspl.1890.0102`）。
按标题或按 creator 检索会得到 8 对看起来独立的条目。
**是 `metadata/<id>` 里的 `external-identifier` 字段把它们钉死为同一篇的**——
若不查 DOI，本轮语料会凭空多出 8 份「独立来源」，占总数近三成。

---

## 七、版面溢出：这批扫描件几乎每一份都跨到了相邻文章

archive.org 的 `philtrans*` 与 `paper-doi-10_1038_*` 是**按页面范围切的**，
不是按文章切的。实测举例：

- `philtrans05512448`（Bakerian 摘要）前 928 字是同期学会**赠书清单**；
- `philtrans08066202`（金银合金）前 2,491 字是一篇**重氮盐化学论文**；
- `philtrans01205368`（金在铅中扩散）开头是**海胆幼体致死温度**的生物学段落；
- `paper-doi-10_1038_054055c0` 首段是**鸽种繁育的读者来信**；
- `paper-doi-10_1038_060173c0` 首段是**指南针与镍壳**的读者来信。

**我没有裁剪它们**：裁剪要动正文，而动正文这件事一旦开头就很难说清动了多少。
逐份在 `notes` 里写明「本件含版面溢出」，把它交给下游按需处理。
**唯一裁过的是 DNB 那一份**——原页面同时含前一条目 `Roberts, Robert Davies`
（**另一位真实同名者**）与后一条目 `ROBERTSON, DOUGLAS MORAY`，
按条目首行 `ROBERTS-AUSTEN, WILLIAM CHANDLER` 与 `ROBERTSON, DOUGLAS MORAY` 裁切，
裁切依据已写进该份 `locator` 与 `notes`。

---

## 八、公有领域依据（给依据，不给结论）

24 份自著件两条依据并列：
① **美国 pre-1931 出版**——出版年 1876-1902，2026 年的分界是 1931（出版年 +95，次年元旦入 PD）；
② **英国／欧盟 70 年 p.m.a.**——作者卒 1902-11-22（DNB 1912 补编原文 `He died at the Royal Mint on 22 Nov. 1902`），1902+70=1972 已届满。

两份第三方件**只有①成立，②如实记为未核**：
- 1914 年《A Record of His Work》：正文主体是他本人文字（1972 已届满），
  但**编者 Sydney W. Smith 的卒年本轮未查得**，其传略／按语／书目的英国侧权利期未核；
- 1912 年 DNB 条目：**撰稿人 T. E. James 的卒年本轮未查得**，英国侧未核。

★ archive.org 的 `licenseurl = creativecommons.org/publicdomain/mark/1.0` 与
`possible-copyright-status = NOT_IN_COPYRIGHT` **只作记录、不作依据**——
聚合器的 license 字段不是权利声明。

---

## 九、没做到的与卡住的

| 项 | 状况 |
|---|---|
| **Alloys Research Committee 五份报告**（Proc. Inst. Mech. Engineers 1891/1893/1895/1897/1899） | **一份也没拿到。** archive.org 上 *Proceedings of the Institution of Mechanical Engineers* 只有 1851/1853/1870 三卷 + 1974 年以后，**1889-1902 整段缺**。这是他最重要的工程文献，本轮语料里只能从他自己论文的脚注里看到（照录：`* " Second Eeport, Alloys Eesearch Committee," 'Meeli. Eng./ 1893, Plate 32.`、`Third Report to the Alloys Research Committee, 'Proc.Inst. Mech. Engineers,' 1895, p. 240.`）。**材料存在、是 PD、坐标已定位到卷次页码，只是本机通道上没有扫本。** |
| **Journal of the Society of Arts 的五个 Cantor Lectures 系列**（1884-1890） | 只拿到 1884 年那一系列的抽印合订本。JSA 各卷在 archive.org 上有（`journalofsociety*soci`），但**卷号与年份不对应**（元数据 year 一律写 1852），要逐卷开箱定位，本轮时间未及。**这是没做，不是做了没有。** |
| **Journal of the Iron and Steel Institute** 他的论文（电沉积铁 1887、金刚石渗碳 1890、Le Chatelier 高温计 1891、自记高温计 1892-93、铁中碳扩散 1896、火炮身管 1898） | 未取。archive.org 的 JISI 只有 1871/1883 与 1899/1900 三卷 + 1911 年以后，**1885-1898 整段缺**。 |
| **Nature 1902 年 T. E. Thorpe 的讣文**（`paper-doi-10_1038_067105a0`） | 条目在、**只有元数据没有正文**（文件清单里只有 `.torrent`／`files.xml`／`meta.sqlite`／`meta.xml`，无 `_djvu.txt`，直接下载 **HTTP 404**）。二手材料因此只落了 DNB 一份。 |
| **Proc. Roy. Soc. / ICE / IMechE 的讣文** | 未取（Grace's Guide 列出了出处：1902 IMechE、1902 ISI、*The Engineer* 1902-11-28、1903 ICE），本轮未逐一找扫本。 |
| **本轮零 bot 墙、零付费墙** | archive.org 与 Wikisource 全程 HTTP 200，没有遇到需要绕过的访问控制，因此**没有「通道受限」条目**。 |

---

## 复核用命令

```bash
WS=…/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-roberts-austen-135
TGT=$WS/workspaces/william-chandler-roberts-austen
cd …/CodexSkills/registry/codex/persona-distiller

# 语料统计（tier / 一手占比 / 研究道 / 回读自验）——注意字段名是 checksum 不是 sha256
python3 - <<'PY'
import json,pathlib,hashlib,collections
TGT=pathlib.Path("…/workspaces/william-chandler-roberts-austen")
rows=[json.loads(l) for l in (TGT/'evidence/source-ledger.jsonl').read_text().splitlines() if l.strip()]
print(collections.Counter(r['tier'] for r in rows))
prim=[r for r in rows if r['tier'] in ('P1','P2')]
print(f"一手 {len(prim)}/{len(rows)} = {len(prim)/len(rows):.4f}")
print(collections.Counter(d for r in rows for d in r.get('dimensions',[])))
ok=sum(hashlib.sha256((TGT/r['local_path']).read_bytes()).hexdigest()==r['checksum'] for r in rows)
print(f"回读自验 {ok}/{len(rows)}")
PY

# 同名护栏
python3 scripts/check_namesake_criteria.py --self-test
python3 scripts/check_namesake_criteria.py "$TGT"

# 研究门（本报告第五节的全部数字出自这一条）
python3 scripts/quality_check.py "$TGT" --phase research
```
