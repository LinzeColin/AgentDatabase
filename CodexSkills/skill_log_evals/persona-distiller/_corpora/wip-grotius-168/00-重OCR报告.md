# Grotius 拉丁一手件重 OCR —— 结果报告

- 日期：2026-08-11　执行：macOS Vision（Objective-C + clang，`usesLanguageCorrection = NO`）
- **并发恒为 1**（全程串行 urllib/curl）；**未花任何 API 钱**；**未碰付费墙、未绕访问控制、未绕验证码**
- **`~/Documents/Codex/GithubProject/` 未写入任何内容**（只读取了 `vision_ocr.m` 与其 README）
- 产物目录：本目录

---

## 0. 结论先行

**重 OCR 这条路走不通，且原因不是质量问题，是能力上限。**

macOS Vision 的**输出字母表里没有长 s（U+017F `ſ`）**。240 叶重 OCR 共 **459,276 字符，`ſ` 出现 0 次**；
在我自己合成的、干净到不能再干净的印刷图上（三种字体、64pt、无噪声）依然 0 次。
凡是 1800 年前排版的拉丁件，每一个 `ſ` 都只能被输出成 `f`（偶尔 `l`/`t`/`i`）。
**换分辨率、换清晰度、换字体都不改变这一点** —— §2 是控制实验。

同页前后对比（216 叶有旧文本可比）：

| | 长 s 面板：正确形 | 讹形 | **存活率** |
|---|---|---|---|
| 旧（archive.org） | 131 | 924 | **0.1242** |
| 新（Vision 重 OCR） | 186 | 1347 | **0.1213** |

**9 册里 4 册微升、5 册下降，合计基本不动（−0.0029）。没有一册接近可做逐字引文。**

**但这一轮有一个能用的结果**：问题的变量是**版本的排版年代**，不是 OCR。
换成 1800 年后重新排版的拉丁版本，同一套探针立刻到 **0.9958–1.0000**（§4）。
**6 部作品里 3 部已经拿到干净拉丁全文并放在 `REPLACEMENT/`，其中 1 部你语料里本来就有、被标成了 `_en`。**

> ★★ **顺带证伪了本任务的一个前提**：`epistolae_oxenstierna_1829` 被判为「已经够好、不必重做」，
> 依据是 `est` 存活率 0.994。**这个判据在这一册上有盲区，实际它烂得和别人一样**。见 §3。

---

## 1. 做了什么

| 项 | 值 |
|---|---|
| 重 OCR 的册数 | 10（拉丁 9 册 + 1 册正对照） |
| 下载并 OCR 的页图 | **240 叶**（每册 24 叶，在全书 10%–90% 区间等距取样） |
| 页图下载失败 | **0** |
| 页图分辨率 | 已逐册核对 `scandata.xml` 的 `origWidth/origHeight`，**拿到的是原生分辨率**（未用被裁剪的 `n<N>_x1400.jpg`） |
| 旧 OCR 同页文本 | 从各册 `_djvu.xml` 逐叶取出，**同叶对同叶**比较（不是拿采样比全本） |
| 取不到旧同页文本 | **1 册**：`ioannisdelaetant00laet_0` 的 `_djvu.xml` 返回 **HTTP 500**（服务端错误，非权限）。该册只给了新值，表内记 `—` |

### 为什么交的是 `.reocr_sample.txt` 而不是全本 `.reocr.txt`

全 9 册共 4,686 叶。在 §2 证明「每个 `ſ` 必然输出成 `f`」之后，
把 4,686 叶跑完只会得到一份**同样不能做逐字引文**的 460 万字文本，
正好是任务里点名不要的那种「看起来像重 OCR 过的文件」。
所以我停在**足以做判决的样本量**上，把省下的时间用在找可用版本上（§4）。
**如果你要全本重跑，管线在这儿是现成的**：`run_sample.py` 把 `NSAMPLE` 调大即可。
实测 **1078.5 秒 / 240 叶 = 4.49 秒/叶**（含每册一次 `_djvu.xml` 下载；其中 Vision 识别本身只占 0.55 秒/叶，其余是串行下载）。
按此速率全量 4,686 叶约需 **5.85 小时**。

---

## 2. 根因：`ſ` 不在 Vision 的输出字母表里（控制实验）

用 `bin/render_text.m` 把同一行字用同一字体、同一字号渲染成干净 PNG，只改字形：

| 渲染进图里的 | Times New Roman | Georgia | Baskerville |
|---|---|---|---|
| `eſt eſſe ſunt ipſe`（真长 s） | `eft elle funt ipfe` ✗ | `eft efle funt iple` ✗ | `eft elle funt ipfe` ✗ |
| `est esse sunt ipse`（现代圆 s） | `est esse sunt ipse` ✓ | `est esse sunt ipse` ✓ | `est esse sunt ipse` ✓ |
| `eft effe funt ipfe`（真 f） | `eft effe funt ipfe` ✓ | `eft effe funt ipfe` ✓ | `eft effe funt ipfe` ✓ |

**第 2、3 行是正对照**：同一张图、同一次调用，圆 s 和真 f 都 100% 读对 —— 管线没问题。
**只有第 1 行错**，而它和第 2 行的唯一差别就是那个字形。

原图也确认过不是扫描质量问题：`evidence/crop_1646_big.png` 是 `djbp_1646` leaf200 放大 4 倍，
`eſſet` / `Scholiaſtes` / `ſenſum` 的长 s 清清楚楚（左侧有小突起、无贯穿横杠），印刷锐利。
**是识别端不产出这个字符，不是输入端看不清。**

本机没有 tesseract / ocrmypdf / pdftotext / Homebrew（已逐个核），**Vision 是唯一可用引擎**。

---

## 3. ★ 判据修正：`est/eft` 单探针有盲区

任务给的判据是 `est 存活率 = est/(est+eft)`。**在 `epistolae_oxenstierna_1829` 上它会给出错误的绿灯**：

| 词对 | 计数 | 存活率 |
|---|---|---|
| `est` / `eft` | **162 / 1** | **0.9939** ← 判据只看这一行 |
| `sunt` / `funt` | 8 / 116 | 0.0645 |
| `se` / `fe` | 1 / 164 | 0.0061 |
| `sit` / `fit` | 0 / 45 | 0.0000 |
| `ipse` / `ipfe` | 0 / 18 | 0.0000 |
| `causa` / `caufa` | 0 / 12 | 0.0000 |
| `suis` / `fuis` | 0 / 14 | 0.0000 |
| `esse` / `esfe` | 0 / 78 | 0.0000 |

原文实景（该册正文）：`Oxenftiernai`、`Parifiorum`、`fcriptae`、`confcriptae`、`univerfali`、`ftudiis`、`esfe`、`cenfuit`、`Clasfis`、`posfent`、`defcriptio`。

**为什么 `est` 独活**：这一册的 `ſt` 是一个**连字**（单个字形），OCR 把它整体读成 `st`；
而**单独的 `ſ` 照样变 `f`**。于是 `est` 全对、其余全错。
**该册的真实面板存活率是 0.2560，不是 0.994。它需要重做，只是重做也救不了（同页 0.2125→0.2739）。**

因此本报告主判据改用 **16 组长 s 词对的面板**（`panel.py`）。
★ 建面板时我自己先踩了一次坑：初版把 `sit/fit`、`satis/fatis` 放了进去，
而 **`fit`（fio 三单）和 `fatis`（fatum 夺格复数）是正经拉丁词**，
会把干净文本误判成有腐蚀（1853 版被压到 0.9828）。**讹形集合里不许放真词**，已剔除。

---

## 4. 可行的路：换排版年代，不是换 OCR

`ſ` 在 1800 年前后退出印刷。**只要换成 1800 年后重新排版（不是影印）的拉丁版本，问题自动消失。**
以下全部**出版年 ≤1930**（PD 依据是出版年）、**`access-restricted-item` 为 None**、可免费取全文，已下载回读：

| 作品 | 交付文件 | 版本 | IA 标识符 | 面板存活 |
|---|---|---|---|---|
| **De Jure Belli ac Pacis**（拉丁全文，3 卷） | `REPLACEMENT/djbp_1853_lat_vol1..3.txt` | 1853 Whewell 版（拉丁正文 + 英文节译对照） | `hugonisgrotiide00/01/02barbgoog` | **0.9958–0.9978** |
| **De Veritate Religionis Christianae** | `REPLACEMENT/de_veritate_1813_lat.txt`（另附 1809 版互校） | 1813 / 1809 | `deveritatereligi0000grot` / `bub_gb_Bf7VskMwYsQC` | **0.9962 / 0.9977** |
| **Mare Liberum** | ★ **你语料里已经有了**：`grotius_raw/mare_liberum_magoffin_1916_en.txt` | 1916 Carnegie 版，**拉丁正文与英译并排**（文件名标 `_en`，但拉丁是干净的） | `freedomofseasorr00grot` | **1.0000** |
| Mare Liberum（另一路） | `REPLACEMENT/de_iure_praedae_1869_lat.txt` | 1869 Hamaker《De Iure Praedae》**含 CAPUT XII 即 Mare Liberum** | `ledroitdeprised02hamagoog` | **0.9983** |

**DJBP 1853 三卷已核过是三个不同卷**，不是重复扫描：vol1 含 `PROLEGOMENA`（书眉 40 次）与 `LIBER PRIMUS`，vol2 `LIBER SECUNDUS`，vol3 `LIBER TERTIUS`。**Prolegomena 在册。**

★ **两点必须写明的限制**：

1. `mare_liberum_magoffin_1916_en.txt` 的拉丁**已实读确认是正文连续拉丁**（`est` 224 处，分布在全文 7.3%–94.0%），不是零星引语。但它与其他文件一样是 **archive.org 的 OCR，不是我这一遍 OCR** —— 下游若引它，出处要写 archive.org 派生件。
2. `de_iure_praedae_1869` 的 cap. XII 是 **De Iure Praedae 手稿本**，与 1609/1618 单行出版的 *Mare Liberum* 是**两个传本**，字句有出入。**要引 1609 版原文，用 Magoffin 1916 那份，不要用它。**

---

## 5. 做不动的（如实记）

以下三部**在 archive.org 上不存在 1800–1930 的拉丁重排本**（已按 title/creator 多轮检索，含异名与体裁词）：

| 作品 | 现状 | 结论 |
|---|---|---|
| **Poemata (1637)** | 仅 1637 / 1639 两个长 ſ 本；1800 后只有 1839 年 *Adamus Exul* 的**英译** | **拉丁逐字引文这条路，判死** |
| **Epistolae quotquot reperiri potuerunt (1687)** | 1715 年本同样长 ſ（存活 0.0000）；无 1800 后重排 | **判死** |
| **Annales et Historiae de Rebus Belgicis (1658)** | 1800–1930 区间检索 **numFound = 0**；1657 年异本存活 0.0029 | **判死** |
| Epistolae ineditae (1806) / ad Oxenstiernam (1829) | 1806、1829 三个扫描件全部长 ſ（另一扫描 `hugonisgrotiiad01oxengoog` 面板存活 0.2594） | **判死** |

对这四类，**能做的只有意译/转述，不能出逐字拉丁引文**。
若必须要逐字，剩下的唯一出路是**装一个认识 `ſ` 的 OCR 引擎**（如 tesseract + 历史字体模型），本机现在没有。

另记一处**未绕的墙**：`ledroitdeprised01hamagoog` 无公开 `_djvu.txt`（遇墙即止，未尝试绕过；同书另有两个可用扫描，不影响结果）。

---

## 附表 A —— 逐份前后对比（同一批叶，24 叶/册，共 240 叶）

`est 存活` = est/(est+eft)。**`面板存活`是主判据**（16 组长 s 词对，见 §3）。

| # | 文件 | 叶 | est/eft 旧全本 | est/eft 旧·同页 | est/eft 新·同页 | est存活旧→新 | **面板存活 旧→新** | esse 旧→新 | ego/cgo 旧全本 | **ego/cgo 旧·同页→新·同页** | ≤2字母 旧→新 | 字符/页 旧→新 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `djbp_1646_lat.txt` | 24 | 14/3171 | 0/86 | 7/80 | 0.0000→0.0805 | **0.1408→0.1561** | 0/10→0/10 | 65/0 | 0/0→0/0 | 0.2185→0.1765 | 3137→2742 |
| 2 | `mare_liberum_1618_lat.txt` | 24 | 0/105 | 0/25 | 2/37 | 0.0000→0.0513 | **0.0600→0.0625** | 0/0→0/11 | 2/0 | 0/0→0/0 | 0.2145→0.1351 | 973→956 |
| 3 | `poemata_1637_lat.txt` | 24 | 2/137 | 0/4 | 0/14 | 0.0000→0.0000 | **0.2432→0.1528** | 0/1→0/7 | 83/0 | 4/0→3/0 | 0.2003→0.0880 | 1070→1034 |
| 4 | `epistolae_1687_lat.txt` | 24 | 4/1192 | 0/26 | 1/98 | 0.0000→0.0101 | **0.0903→0.1064** | 0/0→0/14 | 677/431 | 12/14→37/2 | 0.1725→0.1423 | 6699→6816 |
| 5 | `de_veritate_1640_lat.txt` | 24 | 2/389 | 0/15 | 0/20 | 0.0000→0.0000 | **0.0727→0.0395** | 0/2→0/5 | 11/0 | 0/0→0/0 | 0.2381→0.1888 | 911→887 |
| 6 | `annales_1658_lat.txt` | 24 | 0/398 | 0/11 | 0/12 | 0.0000→0.0000 | **0.1744→0.1667** | 0/3→0/8 | 14/0 | 1/0→1/0 | 0.2051→0.1194 | 1628→1526 |
| 7 | `epistolae_ineditae_1806_lat.txt` | 24 | 1/425 | 1/36 | 0/45 | 0.0270→0.0000 | **0.0368→0.0272** | 0/16→0/15 | 41/0 | 4/0→4/0 | 0.1999→0.1566 | 1396→1251 |
| 8 | `EXT_delaet_notae_1643_lat.txt` | 24 | 2/176 | — | 1/25 | —→0.0385 | **—→0.1011** | —→0/6 | 5/0 | —→1/0 | —→0.1495 | —→1147 |
| 9 | `EXT_delaet_responsio_1644_lat.txt` | 24 | 0/85 | 0/19 | 2/33 | 0.0000→0.0571 | **0.0964→0.0515** | 0/6→0/10 | 30/0 | 6/0→7/0 | 0.2108→0.1767 | 1225→1135 |
| 10 | `epistolae_oxenstierna_1829_lat.txt` | 24 | 162/1 | 26/0 | 36/0 | 1.0000→1.0000 | **0.2125→0.2739** | 0/19→0/14 | 11/0 | 4/0→0/0 | 0.1826→0.1448 | 1371→1303 |

## 附表 B —— 干净替换件（不是我重 OCR 的，是换了排版年代的版本）

| 文件 | 年 | 字符 | est/eft | esse/讹 | sunt/funt | **面板存活** | ≤2字母 |
|---|---|---|---|---|---|---|---|
| `de_iure_praedae_1869_lat.txt` | 1869 | 776,925 | 1520/0 | 481/0 | 421/0 | **0.9983** | 0.2233 |
| `de_veritate_1809_lat.txt` | 1809 | 684,541 | 828/0 | 406/0 | 378/0 | **0.9977** | 0.1797 |
| `de_veritate_1813_lat.txt` | 1813 | 853,797 | 863/0 | 426/0 | 386/0 | **0.9962** | 0.1851 |
| `djbp_1853_lat_vol1.txt` | 1853 | 1,293,209 | 1509/0 | 433/0 | 476/0 | **0.9978** | 0.1925 |
| `djbp_1853_lat_vol2.txt` | 1853 | 1,245,753 | 1552/0 | 420/0 | 436/0 | **0.9975** | 0.2014 |
| `djbp_1853_lat_vol3.txt` | 1853 | 1,232,530 | 1136/0 | 279/0 | 382/0 | **0.9958** | 0.2213 |
| `(已在语料)mare_liberum_magoffin_1916_en.txt` | 1916 | 324,242 | 228/0 | 107/0 | 61/0 | **1.0000** | 0.2185 |
---

## 6. 附表 A 怎么读

- **`面板存活` 是主判据**，`est 存活` 只作参考（§3 说明了它的盲区）。
- `esse` 一列：**旧新两侧的正确形全部为 0**，讹形数各册 5–15。重做没有恢复出任何一个 `esse`。
- `ego/cgo` 一列有一个**真实的改善**：`epistolae_1687` 同页 **12/14（53.8% 读坏）→ 37/2（5.1% 读坏）**。
  这是 `e→c` 的**字形混淆**，不是长 s 问题 —— **Vision 确实修好了这一类**。
  但它救不了逐字引文，因为同一份文件的长 s 面板只从 0.0903 动到 0.1064。
- `≤2 字母词占比`：按要求**只报数、不据此判好坏**（该带子只对英文成立）。
  新值普遍低于旧值（如 0.2185→0.1765），主因是 Vision 对连字符断词的处理不同，与质量无关。
- `字符/页`：新旧同量级（最大差 −12.6%，`djbp_1646` 3137→2742），**没有丢页**。

---

## 7. 复现

```bash
clang -fobjc-arc -O2 -o bin/vision_ocr bin/vision_ocr.m \
  -framework Foundation -framework Vision -framework ImageIO -framework CoreGraphics
clang -fobjc-arc -O2 -o bin/render_text bin/render_text.m \
  -framework Foundation -framework CoreText -framework CoreGraphics \
  -framework ImageIO -framework UniformTypeIdentifiers

NSAMPLE=24 python3 run_sample.py      # 串行下载 + 重 OCR，写 out/
python3 analyze.py                    # 写 final_metrics.json，打印前后对比
python3 mkreport.py                   # 由 json 现算生成本报告的附表
bin/render_text "Times New Roman" evidence/synth.png "eſt eſſe ſunt ipſe" "est esse sunt ipse"
bin/vision_ocr evidence/synth.png     # §2 的控制实验
```

## 8. 目录

```
OCR_REPORT.md              本报告（附表由 mkreport.py 现算生成）
panel.py                   长 s 探针面板（主判据）
metrics.py analyze.py mkreport.py run_sample.py
bin/vision_ocr.m           取自仓内 persona-distiller（未改动逻辑）
bin/render_text.m          §2 控制实验用的合成图渲染器（本轮新写）
out/*.reocr_sample.txt     ×10  Vision 重 OCR，每册 24 叶
out/*.oldsample.txt        ×10  archive.org 同叶旧 OCR（1 册因 HTTP 500 为空）
REPLACEMENT/*.txt          ×6   1800 年后重排的干净拉丁版本
evidence/synth_*.png       §2 合成图与 Vision 的读法
evidence/crop_1646_big.png 1646 原件 4 倍放大（肉眼可见长 s 清晰）
evidence/pilot_djbp1646.txt  首轮 6 叶试跑；evidence/posctl_1829.txt 1829 册正对照
_tables.md logs/            附表中间产物、采样运行日志
final_metrics.json  replacement_metrics.json  baseline_metrics.json  sample_run.json
pages/                     240 叶原始页图（192MB，可删）
```
