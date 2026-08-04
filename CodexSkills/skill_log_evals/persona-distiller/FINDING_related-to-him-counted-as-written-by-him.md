# 「与他有关的书」被当成「他写的书」——一手占比 0.74 实为 0.52

日期：2026-08-04　人物：Liebig #124　查出者：`research.source-unclaimed` 门

---

## 一、数

抓源交回 62 份，deep 门**四项全过**：

```
来源 62 ≥45 ✓　道 6 ≥6 ✓　一手 46 ≥30 ✓　一手占比 0.7419 ≥0.65 ✓
```

逐份核归属之后（先剔 10 份花体乱码，再改 9 份归属）：

```
来源 52 ≥45 ✓　道 6 ≥6 ✓　一手 **27** ≥30 ✗　一手占比 **0.5192** ≥0.65 ✗
```

**同一批语料，一手占比 0.7419 → 0.5192。两项从「全过」变成「都没过」。**

## 二、被算成「他写的」的 9 份，各是什么

| short | 实际作者 | 这是什么 |
|---|---|---|
| `erklrungveranl00buffuoft` | Buff, Heinrich；Löwig | **针对 Liebig 的论战文** |
| `dashomopathisc00grau` | Grauvogl, Eduard von | **写给他的公开信**（他是收信人） |
| `homoeopathiclawo00grau` | 同上 | 同一封信的**英译本** |
| `culturedemandedb02youm` | Youmans, E. L.（ed.） | **文集**，他是撰稿人之一 |
| `correlationandco00youmrich` | Youmans, E. L.（ed.） | **文集**，同上 |
| `magazinfrpharma14unkngoog` | Geiger, P. L.；Hänle | **期刊** |
| `b2931236x` | Davy, Humphry；Shier | **合集** |
| `bub_gb_hEo0AQAAMAAJ` | Müller, J. H. J. | 他人著作 |
| `anleitungzurqua00liebgoog` | Fresenius, C. Remigius | **Fresenius 所著**，Liebig 只作序 |

**共同点：这九份的题名或著录里都出现了目标人物的名字。**
论战文骂他、公开信写给他、文集收了他一篇、期刊登过他、合集含他一节、别人的书他作序。

**「名字出现在这本书里」与「这本书是他写的」是两件事，而抓源把它们合并了。**

## 三、为什么之前的门都放行

| 门 | 为什么看不见 |
|---|---|
| 来源数 45 | 份数是真的 |
| 道数 6 | 道是真的 |
| **一手占比 0.65** | **分档是抓源自己填的，门只是把它加起来** |
| `check_authorship` | 它查「文中有没有他人署名」——论战文里没有别人的署名行 |
| 判重 | 它们确实是九份不同的书 |

**门校验的是「分档字段的算术」，不是「分档字段对不对」。**

## 四、查出它的是什么

`--subject-origin historical` 触发的 `research.source-unclaimed`：

> 声称 `Justus von Liebig` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**

于是我对 35 份 P1/P2 **逐份在正文前 14k（未中者扩到 60k）搜署名式**，
并逐份拉 archive.org `creator` 原始字段比对。**21 份有署名，扩查后再得 4 份，9 份查出是别人的。**

★ 这道门是为 Galen 建的（前印刷时代、伪托多）。**它在一个印刷时代人物身上抓到了完全不同的一类错**。

## 五、★ 射程：不要据此推断别人也错了

我对另两人做了同一个署名扫描：

```
Osler #110    P1/P2 93 份，前 14k 有署名 70（75%）
Blackwell #118 P1/P2 77 份，前 14k 有署名  7（**9%**）
```

**Blackwell 那个 9% 不构成任何指控。** 她的语料是**从合集里抽出来的单篇正文**，
本来就不含扉页；Liebig 的是 **archive.org 整本扫描件**，扉页在文件里。
**同一把尺子量了两种东西。**

**所以本条只能确证 Liebig 一人。** 别人有没有同样的错，
要比对 **著录 creator 字段**（谁写的），不是比对**正文有没有扉页**。
那是另一次测量，本条不下结论。

## 六、处置：不放宽，去补真的

deep 门要 30 份一手且占比 0.65，现在 27 / 0.5192。

- **不改门槛**（「绝不为凑数放宽判据」）
- **不改 profile**（中途不得改；`standard` 的 24/0.50 他本来能过，但那是另开一局）
- **不把那 9 份塞回去**

**正确结论是「他的著作没取够」而不是「语料不够」**——
他一生著述极多（《Chemische Briefe》各版、《Die Grundsätze der Agricultur-Chemie》、
《Reden und Abhandlungen》、《Annalen》里他署名的论文…），
第一轮把 9 份别人的书算成了他的，于是**看起来够了就没再取**。

已发第二轮补抓，判据改成**三重叠加**（扉页署名 ∧ 规范号 ∧ 出版年 1825–1873），
且明写「单靠著录 creator 不够」——因为 `Judenfrage4/5` 的 creator 串
**与目标人物一字不差**，实为其孙 1921/1928 的政论。

## 七、要带走的一条

**「一手」这个分档是抓源阶段自己填的，而所有一手门都只做它的算术。**
凡是一手占比在门槛附近的人物，**都要逐份问一句「凭什么说这是他写的」**——
答案必须是能出示的东西（扉页那一行、规范号、出版年），不能是「这本书跟他有关」。

参见 `_corpora/wip-liebig-124/_attribution_status.md`（逐份证据）、
`FINDING_source-count-counts-files-not-works.md`（同一批数的另一个虚高）、
[[gate-green-but-pointed-at-wrong-artifact]]。
