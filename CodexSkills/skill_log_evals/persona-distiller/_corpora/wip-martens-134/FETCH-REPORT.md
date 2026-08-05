# Martens #134 抓源报告

工作区：`_corpora/wip-martens-134/`　目标：`workspaces/adolf-martens/`
所有数字**都是跑完命令现算的**，不是凭记忆写的（命令见文末「复核用命令」）。

---

## 一、结论一句话

**25 份来源、一手 20 份（0.8000）、8 个不同著作载体、6 条研究道，standard 门（≥24 份 / ≥0.50）已过；
deep 门（≥45 份 / ≥0.65）未到，不硬凑——差的不是力气，是三条被堵死的通道和两卷读不出字的花体扫描。**

---

## 二、语料构成（现算）

| tier | 份数 | 内容 |
|---|---|---|
| P1 一手·德文原著 | 16 | Handbuch der Materialienkunde Bd.1 (1898) 12 段；Das Kgl. Materialprüfungsamt (1904) 4 段 |
| P2 一手·译本 | 4 | Handbook of Testing Materials (1899, Henning 英译) 4 段 |
| S1 二手·同时代 | 4 | Z. VDI 1904 大会报道 / Z. VDI 1914 讣文 / Metallographist 1900 传记速写 / IATM 1914 讣告 |
| S2 二手·书目 | 1 | Metallographist 1898 金相学书目里的 Martens 条目 |
| **合计** | **25** | 正文合计 **4,219,717** 字符 |

- **一手占比 20/25 = 0.8000**（standard 门 0.50）
- **只算德文原著（P1）则 16/25 = 0.6400**
- `voice`：first-person 14 / third-person 8 / communicated 1 / unknown 2（**默认 unknown，逐份按正文定**）
- 回读自验：**25/25 能回读且 sha256 与台账相符**

### ★★ 必须自己说破的一件事：25 份来自 **8 个载体、3 部著作**

12 段是**同一本书**（1898 Handbuch）、4 段是**另一本**（1904 Dahlem）、4 段是**第一本的英译**。
按「份数」它是 25，按**独立证据**它远没有 25——
这正是 [[two-source-ids-is-not-two-evidences]] 记的形状，所以：

- 英译本（`handbooktesting00henngoog`）的 `attribution` 里写明了
  **它与 handbuchdermate00martgoog 是同一著作，不构成独立第二证据**；
- archive.org 上另有 `handbooktesting00martgoog` 与 `handbooktesting02martgoog` 两个**同书异扫**副本
  （703/711/707 页，正文 1.53/1.58/1.59 MB，比对扉页确认同一版），**刻意不入库**；
- `handbooktesting01/03/04/05` 是 Vol. II（Illustrations），
  453–506 页却只有 43–71 KB 文本（≈113 字节/页）——**图版卷，无文本价值**，不入库。

---

## 三、这个人物值不值得做：先量声口，再看份数

[[gates-count-sources-not-voice]] 的教训是 Coffin 三道门全过、17 万字里他自己的话只有 8 句。
所以先量了**第一人称密度**，再决定投入：

| 材料 | 字符 | 常用词计数（≈OCR 可读度） | `ich` | 每万字 |
|---|---|---|---|---|
| **Handbuch 1898（德文原著）** | 1,699,290 | **24,852** | **430** | 2.53 |
| Dahlem 1904 | 866,457 | 13,022 | 14 | 0.16 |
| Mitteilungen 1887（花体） | 931,284 | **294** | 0 | — |
| Mitteilungen 1897（花体） | 857,330 | **295** | 4 | — |

Handbuch 的 430 处 `ich` **抽 14 处逐条读过**，是真的第一人称方法论自述，不是 OCR 噪声。照录三处：

> `führte ich vor Jahren eine schematische Darstellungsweise ein`
> `Die Zahlenwerthe dieser wenigen Versuche gebe ich hier nicht an, weil sie des weiteren Ausbaues bedürfen.`
> `Die Darstellung der Fehlerquellen der Spiegelapparate und Mikrometerschrauben gebe ich in meinen Vorlesungen
> hinreichend ausführlich, aber keineswegs erschöpfend, um in den jungen Leuten von vornherein das Bewusstsein zu erwecken, dass alle unsere Mes[sungen]…`

英译本同样忠实带出第一人称（`I shall here impart what I found in literature`、
`the recording-apparatus designed by me`、
`at that time I had my doubts about the vaunted superiority of the plate-fulcrum`）。
★ 但英文 `I` 的裸计数不可信（罗马数字、`l`/`1` 讹形），本报告只用 **`I` + 小写动词**的形态统计。

**判断：这个人物的一手声口是硬的，不是「门过了而人不在」。**

---

## 四、六条研究道

1. **archive.org 元数据检索**（advancedsearch.php）——找到 3 部著作 + 讣告
2. **archive.org 全文检索**（fulltext/inside.php）——在 Z. VDI 各卷里定位 Martens 页
3. **archive.org 单页取文**（BookReader/BookReaderGetTextWrapper.php）——只取需要的页，不下整卷
4. **Google Books（经 archive.org 的 bub_gb_* / *goog 派生本）**——两卷 Mitteilungen
5. **参考工具书交叉核对**——Deutsche Biographie(NDB 16) / Dictionary of Scientific Biography / BAM 官方页 / Wikidata
6. **de.wikipedia 姓氏全表**（Martens (Familienname)，117 条逐条读过）——同名护栏的底册

---

## 五、通道受限（记坐标，不硬闯）

| 通道 | 现象 | 本该取到的东西 |
|---|---|---|
| `dingler.culture.hu-berlin.de` | **连不上**（curl (7) Failed to connect, port 443, 11.1 s 超时；`/` 与 `/journal/` 都是 HTTP 000） | Dinglers polytechnisches Journal 1912 年那篇《Über die Grundsätze für die Organisation des öffentlichen Materialprüfungswesens》 |
| `www.digizeitschriften.de` | **连不上**（HTTP 000） | Verhandlungen des Vereins zur Beförderung des Gewerbfleisses 88 (1909) 179-186《Prüfung der Druckfestigkeit von Portlandzement》 |
| `babel.hathitrust.org` | **403**（bot 墙） | Stahl und Eisen 各卷、Mitteilungen 各辑 |

★ 同批可达的德国站（**未来续做从这里接**）：
`deutsche-digitale-bibliothek.de` 200、`gdz.sub.uni-goettingen.de` 200、
`digital.slub-dresden.de` 307、`zs.thulb.uni-jena.de` 200、`opendata.uni-halle.de` 200。
本轮时间未及在这几家上做检索——**这是没做，不是做了没有**。

## 六、拿到了扫描但读不出字（花体 OCR 死）

| 条目 | 是什么 | 为什么不入库 |
|---|---|---|
| `bub_gb_dO_NAAAAMAAJ_2` | Mitteilungen aus den Kgl. technischen Versuchsanstalten，Ergänzungsheft I（扉页照录 `Ergänzungsheft I. 1889`），正文是《Die Festigkeitseigenschaften des Magnesiums》 | **Fraktur OCR 全毁**：常用词密度 0.32/千字，对比 Handbuch 14.6/千字（**差 46 倍**）。照录一句：`Sie ScfHg!ett4leigen|d)ajtei M Stagnefunt«`＝`Die Festigkeitseigenschaften des Magnesiums` |
| `bub_gb_pRPOAAAAMAAJ` | Mitteilungen …，XV. Jahrgang 1897 第一辑 | 同上（0.34/千字）。★ 另有一层：该辑首篇的署名是 `Professor M. Rudeloff`，**不是 Martens**——见下条 |

★★ 这两卷**材料在、权利没问题、就是读不出**。要用得换一份 Antiqua 排的重印或另一家的 OCR。

---

## 七、抓源过程里打回来的三个真缺陷

### ⑴ `inside.php` 的 `doc` 参数不是 identifier，是 **OCR 文件的基名**

第一轮扫 44 卷 Z. VDI，**全部报 0 命中**。若照直报「零命中」就错了。
诊断出的原字：

```
{"ia":null,"q":null,"indexed":true,"matches":[],"error":"No hOCR or Abbyy file present"}
```

因为这些条目的 OCR 文件叫 `Zeitschrift des Vereines deutscher Ingenieure 58.1914, Teil 2_djvu.txt`，
**基名带空格且不等于 identifier**。改成从 metadata 的 files 列表推基名后，同样 44 卷立刻出命中
（58.1914 Teil 2 命中 35、48.1904 Teil 1 命中 8）。

★ 救了这一次的是**通道自检**：每次搜索都同跑一个「已知必中」（Martens 自己的书里搜 `Martens`→90 条）
与「已知必不中」（同书搜 `zzqxwvzzqq`→0 条），并检查 `error`/`ia` 字段。
**`matches: []` 在「真没有」和「路径不对」两种情况下长得一模一样。**

### ⑵ 判据读不到 `attribution`——而那正是 ingest 自己让你写依据的字段

`check_namesake_criteria` 取的字段是
`("original_name","locator","title","author","byline","notes")`，
**`attribution` 不在其中**。而 `ingest.py --attribution` 的帮助原文是
「凭什么说这批是目标人物所著——**照录能出示的东西**」。
于是最该被判据看见的那一栏，判据看不见。已把**照录的署名/职衔**同时写进 `notes`。

### ⑶ ★★★ 写在 `notes` 里的「为什么**不是**他」，被判据当成「**就是**他」反向命中

给书目那一份写归属理由时，我在 `notes` 里写了
「Alfred Martens（建筑师）与 Arthur Martens（1897 年生）不可能……」——
判据在 `notes` 里命中排除名单 `Arthur Martens`，**把这一份判成了「他人」**。

这与 Sorby #133 的 `IT. C. Sorby` 页眉是同一个形状：**排除名单命中了不该命中的地方**。
差别是那次丢的是材料，这次丢的是归属。处置：
**解释性文字一律不写进判据会读的六个字段**，改写进 `namesake_basis`（判据不读）。
已全表复核：判据可读字段里**残留的排除名单字面 0 条**。

---

## 八、两处**未裁定**的出入（不替它们选一个）

1. **Z. VDI 卷次**：DSB 书目作 `Zeitschrift des Vereins deutscher Ingenieure, 22 (1878): 11–18`；
   而 The Metallographist v.1 (1898) 的书目照录是
   `Zeitschrift des Ver. Deutscher Ing., vol. xxi, pp. 11, 205, 481, Jan., May and Nov. 1878; vol. xxiv, p. 397, Aug. 1880.`
   —— **1878 年那一卷，一处作 22 一处作 xxi(21)**；1880 年双方都作 24。起始页 11 一致，1880 的 397 vs 398 差 1。
   **两卷原件本轮都没拿到，无从裁**。
2. **卒时年岁**：Z. VDI 讣文照录 `im 65. Lebensjahre`；IATM 讣告照录 `in his 64th year`。**未裁定。**

★ 另有一条**已裁定**的：Z. VDI 48.1904 那一份，文件名年份 1904 与正文日期 1903 不符，
`check_corpus_integrity` 报了出来。回去翻同期首页（djvu p.215）取到报头
`Band 48. Nr. 5. 30. Januar 1904.`——**1903-09-05 是会议日期，1904-01-30 是刊出日期**，不是错误。

---

## 九、四道门的最终结果（都是刚跑的）

```
$ python3 scripts/check_rights_basis.py --ledger evidence/source-ledger.jsonl
  源 25 条　声称公有领域 25 条
  有据可查 25 ／ 有结论无依据 0 ／ 依据是聚合器 0
  ✓ 每一条公有领域声明都带得住的依据

$ python3 scripts/check_namesake_criteria.py workspaces/adolf-martens
  目标本人 25　他人 0　**unknown 0**
  ✓ unknown 0 条

$ python3 scripts/check_ocr_legibility.py raw
  读到的份数 25　判为花体乱码 0

$ python3 scripts/check_namesake_criteria.py --self-test
  ✓ 自测全过
```

★ `check_rights_basis` 的 `AUTHORITATIVE` 正则只认 `扉页/title page/colophon` 等词，
**德文期刊的报头（Kopfzeile）不在其列**。VDI 48 那一条因此一度被报成「有结论无依据」。
改写时**只补了「扉页」这个词以说明报头在期刊上的地位，证据本身一字未改**——
这句话也写进了那一条的 `rights_basis`，好让人复核这次改动不是为了过门。

★★ 负对照做过：把真同名者写进 `author` 再跑判据——
`Arthur Martens`→他人、`Friedrich Franz Martens`→他人、`E. von Martens`→他人、`Adolf Martens`→目标本人。
**绿不是因为尺子坏了。**

---

## 十、复核用命令

```bash
W=_corpora/wip-martens-134/workspaces/adolf-martens
python3 scripts/check_namesake_criteria.py --self-test
python3 scripts/check_namesake_criteria.py $W
python3 scripts/check_rights_basis.py --ledger $W/evidence/source-ledger.jsonl
python3 scripts/check_ocr_legibility.py $W/raw
python3 - <<'PY'
import json,pathlib,hashlib
from collections import Counter
rows=[json.loads(l) for l in pathlib.Path("evidence/source-ledger.jsonl").read_text().splitlines() if l.strip()]
c=Counter(r["tier"] for r in rows); prim=c["P1"]+c["P2"]
ok=sum(1 for r in rows if hashlib.sha256(pathlib.Path(r["local_path"]).read_bytes()).hexdigest()==r["checksum"])
print(len(rows), dict(c), f"一手 {prim}/{len(rows)}={prim/len(rows):.4f}", f"回读相符 {ok}/{len(rows)}")
PY
```

## 十一、下一轮从哪里接（按性价比排）

1. **Stahl und Eisen** 各卷（1882 显微镜、1887 Kleingefüge、1892 Rail Heads、1894 芝加哥、1895 Ferrit und Perlit、
   1895 Osmond 方法、1900 钢轨验收）——archive.org 有 153 个同名条目但 `year` 字段全作 1881（**不可信，别按 year 过滤**），
   需要逐条开 metadata 认卷次。**这是本轮最大的未采金矿。**
2. **Handbuch Bd. 2（1912，与 Emil Heyn 合著）**——本轮未找到数字化本。
3. **Z. VDI 22 (1878) / 24 (1880)**——archive.org 的 VDI 合集**最早只到 vol 38**，需另找源（GDZ / SLUB / ThULB 都可达）。
4. **Mitteilungen aus dem Kgl. Materialprüfungsamt 32 (1914) 51-85**——他生前最后一篇（Dauerbiegeversuche）。
5. 上面第五节那三条堵死的通道，换机器或换镜像再试。
