# Roberts-Austen #135 抓源报告

工作区：`_corpora/wip-roberts-austen-135/`　目标：`workspaces/william-chandler-roberts-austen/`
所有数字**都是跑完命令现算的**（命令见文末）。

---

## 一、结论一句话

> ⚠ **本节及第二、五、九节的数字已被文末「补记（定向补抓）」更新**：
> Alloys Research Committee 五份报告已于补抓中**全部取得并入库**，
> 语料由 27 份增至 **32 份**（一手 31/32 = 0.9688），
> `authorship-unproven` 由 22 条增至 **27 条**。
> 以下保留本轮原文，**不改写历史数字**——两组数各自成立于各自的时点。

**27 份来源、一手 26 份（0.9630）、6 条研究道全覆盖，standard 门（≥24 份 / ≥0.50 / 6 道）三项全过；
deep（≥45 份 / ≥0.65）未到，不硬凑。
但研究门自跑有 22 条 `research.authorship-unproven`——这是本轮最该报的数，成因逐份查清了，见第五节。**

---

## 二、语料构成（现算）

| tier | 份数 | 内容 |
|---|---|---|
| P1 一手 | 25 | Phil. Trans. A 全文 3 篇、Proc. Roy. Soc. 摘要 8 篇、Nature 署名短文与书评 9 篇、Cantor Lectures 1884、Canada's Metals 1898、Introduction to the Study of Metallurgy 1891、**J. Iron & Steel Inst. 55 (1899) 会长就任致辞**、亲笔信著录卡 1898 |
| P2 一手·身后编选 | 1 | Roberts-Austen: A Record of His Work（Sydney W. Smith 编，1914） |
| S1 二手·同时代传记 | 1 | DNB 第二补编 vol.3 (1912) pp.222-223，撰稿人 T. E. James |
| **合计** | **27** | 正文合计 **2,953,351** 字节 |

- **一手占比 26/27 = 0.9630**（standard 门 0.50）
- **研究道**：writings 13／expression 8／conversations 3／decisions 1／timeline 1／external 1 —— **6/6 覆盖**（★ 分布很不均：三条道各只有 1 份，如实记）
- `voice`：first-person 13／unknown 13／third-person 1。**默认 unknown，只在实测第一人称（`I`+动词、`my`+名词）计数 ≥2 时才写 first-person**
- `tier_reason`：**27/27 都写了**，零空缺
- `derived_from`：**27 份全空——这是正常的**（见第三节）
- 回读自验：**原文 sha256 27/27 相符，归一件 sha256 27/27 相符**

### ★ 必须自己说破：27 份不等于 27 处独立证据

- `philtrans05512448`（Proc. Roy. Soc. 58 摘要）与 `philtrans09730582`（Phil. Trans. A 187 全文）
  是**同一场 1896 年 Bakerian Lecture 的两种印本**；
- `philtrans05894557` 与 `philtrans00706421` 是**同一篇 Osmond 合著论文**的摘要与全文；
- `philtrans01205368`（rspl.1900.0004）与 `philtrans09607756`（rspl.1900.0005）
  **页面范围物理重叠**——前者第 10,389 字起已经是后者的署名行。

三对已在各自 `notes` 里写明。**按「独立著作单位」算，27 份约合 24 件。**

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

**唯一一份从多作者载体里切出来的**是 J. Iron & Steel Inst. 55 (1899) 的会长就任致辞
（原卷 1,193,900 字符的学会年刊，只取第 **[44573:124727] 字符区间**；边界起止串写在该份 `locator` 里，可复现）。
★ 这里差点写错单位：该卷 **1,198,732 字节 / 1,193,900 字符**，**不是纯 ASCII，两个数不等**——
切片是在解码后的字符串上做的，写成「字节区间」别人按字节切会错位 4,832 字。已在台账 `locator` 里改正并注明两个数。
**同一载体没有第二片，`derived_from` 无对象可指**——所以 27 份全空是正确状态，不是漏填。

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
| 来源门 `source.minimum` 24 | **27 ✓** |
| 一手占比门 0.50 | **0.9630 ✓** |
| 研究道覆盖门 6 | **6 ✓** |
| `authorship`：P1 声称为本人所著 | 25 |
| `authorship`：**已证实归属** | **3** |
| **`research.authorship-unproven`** | **22** |
| `research.source-unclaimed` | 17 |
| `research.attribution-basis` | 1（historical 人物未声明 `attribution_basis`） |
| `research.lane-completion` | 1（六条研究道正文尚未写——**那是研究员的活，不是抓源员的**） |
| warning `corpus.unexamined-band` | 1 —— **就是 `letter00robe` 那 1,215 字的著录卡**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何内容判据看过它**。它已在自己的 `notes` 里写明「是著录卡不是信件全文」；`conversations` 道另有 2 份支撑，不是靠它一份撑着。 |

**只有 3 份过了归属门**：`philtrans00429265`（A-signature-block）、
`paper-doi-10_1038_060173c0`（A-discussion-turn，证据照录 `to the Iron and Steel Institute, Prof. Sir W. Roberts-Austen`）与
`jisi55-1899-presidential-address`（A-byline-standalone，证据照录 `Sir William Roberts-Austen, K.C.B., who was received with loud applause…`）。
★ 第三份是我**切片时特意把致辞前那句就任记录一起收进来**才过的——
若只从 `PRESIDENTIAL ADDRESS.` 那个标题切起，全篇没有一处署名，它也会是第 23 条 unproven。

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

## 六、抓源过程里打回来的四个真缺陷

### ⑴ ★ 我用了不存在的字段名做回读自验，得到「0/26 相符」

第一版核算写的是 `r.get('sha256')`——**本 schema 里那个字段叫 `checksum`**，
`.get` 返回 `None`，当时的 26 份逐一比对全部不等，输出 **`回读自验 sha256 相符 0/26`**。
这个数字看起来严重且可信，差点写进报告。改用正确字段后是 **26/26**（补入第 27 份后为 27/27）。
**空默认值把「没这个字段」读成了「校验失败」**——与 `[[empty-default-swallows-unknown]]` 同形，
只是这次倒向了「看起来有问题」而不是「看起来没问题」，所以我才发现。

### ⑵ 判据里的理由我没跑就写了，写反了

`namesake-criteria.json` 第一版给禁区 `William Roberts` 的理由是
「它会命中 `William Chandler Roberts-Austen`」——**跑出来不会**（中名把两段隔开）。
真正的理由要去语料里找：全 27 份 `William` 紧挨 `Roberts` 只有 3 处、三处都是他自己，
其中一处是**他本人著作目录的标题行**、一处是**那份 1899 年会长致辞唯一的归属证据**。
**结论相同、理由完全不同**，而结论对理由错是最难发现的一种。详见 NAMESAKE-GUARD-实测.md 第五节。

### ⑶ 「抓了没入库」那道判据对本工作区报的是「无从比」，不是「通过」

`check_staged_but_not_ingested.py` 存在的理由正是本轮这种风险（抓到了、却没进工作区）。
跑它，对本人物的输出逐字是：

> `wip-roberts-austen-135：没有外层 raw/：**没走过抓源台账那一步**，无从比`

它找的是 `_corpora/wip-<人>/raw/_ids.txt` 这种布局，而本轮（与 Martens #134 一样）
用的是 `_fetch-staging/raw/`。**判据没被骗，它压根没被问。**
同一句话它对 `wip-sorby-133`、`wip-steinhardt-98` 也说了——**不是我一个工作区的事**。

自己按等价口径比过：**暂存 27 份 `.txt` ↔ 台账 27 条 `original_name`，双向零差**。
另有 4 个非 `.txt` 中间件（`dnb1912.json/.raw`、`dnb_p222/223.raw`，是取 DNB 的中间产物）
与 `_fetch-staging/probe/` 下 3 卷 JISI 原卷（只用于定位切片边界），**刻意不入库**。

### ⑷ `philtrans*` 与 `paper-doi-10_1098_rspl_*` 是同一篇的两条记录

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
| **Alloys Research Committee 五份报告**（Proc. Inst. Mech. Engineers 1891/1893/1895/1897/1899） | ~~**一份也没拿到。**~~ **★ 本条已作废——见文末「补记（定向补抓）」。五份全部拿到并入库。** 本轮的原始结论是：实测 `title:("Proceedings of the Institution of Mechanical Engineers") AND year:[1880 TO 1910]` 在 archive.org 上 **numFound 0**，据此判定「他整个活跃期一卷扫本都没有」。**这个判定是错的，而错在检索式不在馆藏**：这批卷册的 `title` 字段一律只写 `Proceedings`（不含刊名全称），`year` 字段一律写 `1849`——**按刊名全称查、再按年份过滤，两个字段各挡一次，必然 0 命中**。 |
| **Journal of the Society of Arts 的五个 Cantor Lectures 系列**（1884-1890） | 只拿到 1884 年那一系列的抽印合订本。JSA 各卷在 archive.org 上有（`journalofsociety*soci`），但**卷号与年份不对应**（元数据 year 一律写 1852），要逐卷开箱定位，本轮时间未及。**这是没做，不是做了没有。** |
| **Journal of the Iron and Steel Institute** 他的论文（电沉积铁 1887、金刚石渗碳 1890、Le Chatelier 高温计 1891、自记高温计 1892-93、铁中碳扩散 1896、火炮身管 1898） | **取到一件**：vol. 55 (1899) 的会长就任致辞（已入库，80,151 字）。其余仍缺——实测 `title:("Journal of the Iron and Steel Institute") AND year:[1880 TO 1905]` 在 archive.org 上**只有 4 卷**（1883、vol.55/56 于 1899、vol.57 于 1900），**1885-1898 整段没有扫本**。另已开箱查过 vol.56 与 vol.57：里面的 `Presidential Address` 全是**别人引用他**，不是他的第二篇致辞，故未收。 |
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

---

# 补记（定向补抓）：Alloys Research Committee 五份报告，**五份全部拿到**

本节推翻第九节表格首行的原结论。所有数字都是跑完命令现算的。

## 一句话

**1891/1893/1895/1897/1899 五份报告全部找到、全部入库**，共 384,122 字节，
占语料总量（3,337,473 字节）的 11.5%。语料由 27 份增至 **32 份**，
一手 31/32 = **0.9688**，`decisions` 道由 1 份增至 **3 份**。
**没有遇到付费墙，也没有遇到 bot 墙**——全程 archive.org HTTP 200。

## 上一轮为什么报 numFound 0——不是馆藏没有，是检索式自己把它挡光了

上一轮用的是 `title:("Proceedings of the Institution of Mechanical Engineers") AND year:[1880 TO 1910]`。
这一条**两个字段各挡一次**，必然 0 命中：

| 字段 | 印本上的样子 | archive.org 上的样子 | 后果 |
|---|---|---|---|
| `title` | Proceedings of the Institution of Mechanical Engineers | 一律只写 **`Proceedings`** | 按刊名全称查 → 0 |
| `year` | 1891 / 1893 / 1895 / 1897 / 1899 | 1891 卷写 1891，**其余四卷一律写 `1849`** | 按年过滤 → 再删掉 4/5 |

**换成按 `creator` 查就一次到手**：`creator:("Institution of Mechanical Engineers")` → **numFound 118**，
其中 identifier 里嵌着年份的一共 22 条，五个目标年份**一个不缺**。
真正认卷的字段是 **`volume`**（五卷分别写 1891/1893/1895/1897/1899），**不是 `year`**——
`year` 在其中 4 卷上是错的，与上一轮 JSA 各卷一律写 1852 是同一个毛病。

★ 教训不是「archive.org 的 year 不可信」（这条上一轮已经写过了），
而是**上一轮写过这条，却仍然在同一天用 `year` 区间做了过滤**。
判据写在纸上，检索式里没照做。

## 五份的落点

| 报告 | 卷次页码 | 卷 identifier | source_id | 道 | 字节 |
|---|---|---|---|---|---|
| First Report | Proc. IMechE **1891, pp. 543-566** | `proceedings1891inst` | `src-d690d5a293a8` | writings | 63,762 |
| Second Report | **1893, pp. 102-138** | `proceedings189300inst` | `src-391ca73471aa` | writings | 95,652 |
| Third Report | **1895, pp. 238-254** | `proceedings189500inst` | `src-dfa437e17e2d` | decisions | 40,711 |
| Fourth Report | **1897, pp. 31-69** | `proceedings1897inst` | `src-5bf1098b8d50` | decisions | 101,125 |
| Fifth Report: Steel | **1899, pp. 35-68** | `proceedings189900inst` | `src-269db01c421a` | writings | 82,872 |

起始页码不是我推的，是**第五份报告自己的脚注给的**，照录：

> `* For the First, Second, Third, and Fourth Reports, see Proceedings
> 1891, page 5i3 ; 1893, page 102 ; 1895, page 238 ; and 1897, page 31.`

（`5i3` 是 `543` 的 OCR 讹字。）这一条同时**证实了上一轮从他自己论文脚注里抄到的坐标**
（`Third Report … 1895, p. 240` 指的是篇中某页，不是起始页；起始页是 238）。

## 署名情况：五份**全是单人署名**，但第三份带着一个真陷阱

五份扉页署名逐字照录（连续空白折成单空格，字形标点含讹字未改）：

| 年 | 扉页署名 |
|---|---|
| 1891 | `By Professor W. C. II < )i:i:i:i--Al"> Ti;\. « l;. li;>`　**整行被 OCR 打毁** |
| 1893 | `By Professor ^V. C. ROBEKTS-AUSTEN, C.B., F.R.S.` |
| 1895 | `By Professor W. C. EOBERTS-AUSTEN, C.B., F.R.S.` |
| 1897 | `By Pbofessob W. C. ROBERTS-AUSTEN, C.B., F.R.S.` |
| 1899 | `By Sir Williaji C. EOBERTS-AUSTEN, K.C.B., D.C.L., F.R.S., HoxoRARY Life Member.` |

**没有一份是委员会集体具名**——五份都是 “Report **to** the Committee”，
他一个人写、报给委员会。所以不存在共同著作权人。

### ★★ 但 1895 年那份，题目底下实际有三个作者

第三份报告后面紧跟两份**另有署名**的附录，逐字照录：

- `APPENDIX 1 TO THIRD PtEPOPtT TO THE ALLOYS EESEARCH COMMITTEE … Cv 3Ir. ALLAN GIBB, Associate of tee Royal School of Mines`（`Cv 3Ir.` ＝ `By Mr.`）
- `APPENDIX 2 TO THIED EEPORT TO THE ALLOYS EESEARCH COMAIITTEE … By Mr. ALFRED STANSFIELD, Associate of the Eoyal School of Mixes`

**这两份不是他写的，一个字都没收。** 他自己在正文里把关系说清楚了，照录：

> `The researches conducted by Mr. Stansfield and by Mr. Allan Gibb were in each case
> undertaken on my suggestion as a thesis for the " Honours " Associateship in Metallurgy
> of the Eoyal School of Mines.`

**「出题的人」不等于「写的人」**——这正是 `[[related-to-him-is-not-written-by-him]]` 那一类。
若按「第三份报告」整体收，语料里会凭空多出两个人的 45,000 余字。

同理刻意未收的还有：1893 年同次会议连读的 William Dean 的论文（第 139 页起，
`By Mr. WILLIAM DEAN, Member of Council`），以及**五份报告各自后面的讨论段落**——
讨论里绝大多数字是别的会员说的。

## 版面溢出：**零**

上一轮 `philtrans*` 与 `paper-doi-10_1038_*` 几乎每一份都跨到了相邻文章（第七节）。
本轮五份**一处都没有**，因为切法不同：上一轮是拿 archive.org 按页面范围切好的条目，
本轮是**自己按版口切的整卷**。自检口径与结果：

- 五份切片内的**全部 89 处版口刊头**，逐条认过，**全是 `ALLOYS RESEARCH` 的 OCR 变体**，
  没有一处是别的文章的刊头；
- 邻文标题词（`TENSILE TESTS`／`WILLIAM DEAN`／`PROPELLERS`／`BARCROFT`／`POWRIE`／
  `ALLAN GIBB`／`STANSFIELD, Associate`／`MEMOIRS`）在五份里**命中 0 次**；
- 唯二的疑似命中已逐条看过原文，都是**他自己正文里的交叉引用**
  （1893 谈机车铜火箱、1895 提到两份附录的页码），不是溢出。

## 切片坐标：**按字符，不是按字节**

★ 差点写反的一处：起草台账时我写了「本卷 djvu.txt 为纯 ASCII，字节数＝字符数」。
**跑了一遍，五卷没有一卷是纯 ASCII**：

| 卷 | 字符 | 字节 | 差 |
|---|---|---|---|
| 1891 | 1,873,108 | 1,879,465 | 6,357 |
| 1893 | 1,582,852 | 1,585,778 | 2,926 |
| 1895 | 2,096,020 | 2,102,162 | 6,142 |
| 1897 | 1,696,404 | 1,699,969 | 3,565 |
| 1899 | 2,001,368 | 2,004,750 | 3,382 |

照字节切会错位数千字。五卷均可**严格 UTF-8 解码、零替换字符**，
故字符偏移可精确复现（读的时候别用 `errors='replace'`）。
起止串与字符区间都写在各自的 `locator` 里。

## 研究门：`authorship-unproven` 由 22 条增至 **27 条**——五份新料一份也没过归属门

**我没有去改判据让它变绿。** 逐份把「到底是哪个 token 挡住的」用**单 token 替换法**隔离出来了：

| 年 | 挡住它的 token（实测隔离） |
|---|---|
| 1891 | 署名行整行被打毁。**判据判对了**——这一行本身确实证不了归属 |
| 1893 | 名 `^V.`（`W.` 讹）+ 姓 `ROBEKTS`（R→K 讹），两处 |
| 1895 | **只有姓 `EOBERTS`（R→E 讹）**——只把这一处改回 `ROBERTS` 即命中 |
| 1897 | **姓 `ROBERTS-AUSTEN` 完全正确。挡住它的是被打坏的敬称 `Pbofessob`**——敬称改对或删掉，两种都命中 |
| 1899 | 名 `Williaji` + 姓 `EOBERTS`，两处（实测：只改名仍不中） |

### 两条结构性缺陷，都是新的，都做了负对照

**⑴ `ocr_byline_evidence`（`A-byline-ocr` 那条 OCR 容错路）对复姓一律不认。**

它的分词是 `re.split(r"[^A-Za-z]+", body)`，把 `ROBERTS-AUSTEN` **拆成 `ROBERTS` 和 `AUSTEN` 两个 token**，
而两者与 `roberts-austen` 的编辑距离分别是 7 和 8，都过不了 ≤2。
负对照（**只改「姓里有没有连字号」，其余全同**）：

| 输入 | last 参数 | 结果 |
|---|---|---|
| `By William C. ROBERTS-AUSTEN, C.B.` | `Roberts-Austen` | **不中** |
| `By William C. EOBERTS-AUSTEN, C.B.` | `Roberts-Austen` | **不中** |
| `By William C. AUSTEN, C.B.` | `Austen` | 命中 |
| `By William C. AUSTEX, C.B.`（姓也打坏） | `Austen` | **仍命中** |

**拼写完全正确的复姓过不了，而打坏了的单姓过得了。**
射程不止本人物：**任何复姓人物的 OCR 容错路都是死的**，
而这条路正是为「名字被 OCR 打坏」而建的——Roberts-Austen 恰好两样都占。

**⑵ 被 OCR 打坏的敬称会把整行废掉。**

敬称剥离用的是字面表 `(?:Sir|Dame|Prof(?:essor)?|Dr|Mr|Mrs|Ms|Rev|Lord|Lady)\.?`，
**没有 OCR 容错**。`Pbofessob` 剥不掉，就占住了「名」那个位置，于是名字校验失败。
负对照（**姓统一换成单姓以排除⑴的干扰**）：

| 输入 | 结果 |
|---|---|
| `By Professor William C. AUSTEN, C.B.` | 命中 |
| `By Pbofessob William C. AUSTEN, C.B.` | **不中** |
| `By William C. AUSTEN, C.B.`（无敬称） | 命中 |

主 `BYLINE` 正则那条路同病：1897 那份**姓拼得完全正确**，
只因敬称是 `Pbofessob` 而整条不中；把敬称改成 `Professor` 或直接删掉，两种都立刻命中。

★ 上一轮第五节列了 7 种拦截机制，**这两条都不在里面**。
判据要不要长出「复姓不拆分」与「敬称容错」，是待裁定的事——**我没有动它**。

## 同名护栏：重测过，并发现一个新的同名者

- `check_namesake_criteria.py --self-test` → **全过**；
- 对本工作区 → `目标本人 32　他人 0　unknown 0`。

★ 但护栏比的是台账 `author` 字段，**不看正文里的人名**。
1895 那份正文里有一个**上一轮 19 条候选册里没有的真同名者**，照录：

> `Mr. Eeginald Roberts, who was appointed as an assistant early last yeai", has also done good work.`

即 **Reginald Roberts**，皇家矿业学院助手，1894 年初到任。
按判据自己写的规则「≥1885 而只署裸 `Roberts`（无 Austen）→ **不许默认是他**」，
这一位该进 `excluded_names`。**今天加不加都不改变任何结果**（他从未作为 `author` 出现），
所以我没有动 `namesake-criteria.json`，只把他报上来。

## 通道与合规

- **并发恒为 1**，全程顺序请求；
- **零付费墙、零 bot 墙、零验证码**：archive.org `advancedsearch.php`／`metadata/<id>`／
  `download/<id>/<id>_djvu.txt` 全程 HTTP 200，没有任何需要绕过的访问控制，
  因此**本轮没有「通道受限」条目**；
- HathiTrust／Google Books／BHL／Grace's Guide **没有用上**——第一条路就通了，不必再开；
- PD 依据两条并列（出版 1891-1899，美国 pre-1931；作者卒 1902-11-22，英/欧 70 年 p.m.a. 1972 已届满），
  archive.org 的 `licenseurl` 只作记录、不作依据。

## 回读自验

全库 **32/32** 原文 sha256 与台账 `checksum` 相符；新增五份原文与归一件 **5/5、5/5** 相符。
`tier_reason` 空缺 **0**；`derived_from` 五份全空——**这是正确状态**：
五份各出自**五个不同的卷**，同一载体里没有第二片，无对象可指。
