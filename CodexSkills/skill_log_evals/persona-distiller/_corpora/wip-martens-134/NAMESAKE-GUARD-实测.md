# Martens #134：同名护栏实测——**抓源之前必读**

目标：**Adolf Karl Gottfried Martens**，1850-03-06 Bakendorf bei Hagenow – 1914-07-24 Groß-Lichterfelde。
柏林 Mechanisch-Technische Versuchsanstalt（1884-1903）→ Königliches Materialprüfungsamt（1904-1914）主任。

---

## 一、现有护栏 `check_authorship.ocr_byline_evidence` 实跑（first="Adolf", last="Martens"）

**拿他真实的同名者打的，不是假例子。**

| 署名行 | 是谁 | 期望 | **实际** |
|---|---|---|---|
| `By Adolf Martens.` | 目标本人 | 放行 | 判为本人 ✓ |
| `ADOLF MARTENS.` | 目标本人 | 放行 | 判为本人 ✓ |
| **`Von Adolf Martens.`** | **目标本人（德文署名）** | **放行** | **★★★ 不认为是本人** |
| **`Von A. Martens, Berlin.`** | **目标最常见的印本署名** | **放行** | **★★★ 不认为是本人** |
| **`VON A. MARTENS.`** | **目标（全大写版口）** | **放行** | **★★★ 不认为是本人** |
| `By A. Martens.` | 目标（英译本） | 放行 | 不认为是本人 |
| `By Arthur Martens.` | 滑翔机工程师 1897-1937 | 应拦 | 不认为是本人 ✓ |
| `Von Alfred Martens, Architekt.` | 建筑师 1881-1920 | 应拦 | 不认为是本人 ✓ |
| `EDUARD VON MARTENS.` | 动物学家 1831-1904 | 应拦 | 不认为是本人 ✓ |
| `By E. von Martens.` | 同上 | 应拦 | 不认为是本人 ✓ |
| `By F. F. Martens.` | 物理学家 1873-1939 | 应拦 | 不认为是本人 ✓ |
| `By G. F. von Martens.` | 法学家 1756-1821 | 应拦 | 不认为是本人 ✓ |
| `By Martin Martens.` | 比利时植物化学家 | 应拦 | 不认为是本人 ✓ |
| `By Friderich Martens.` | 1675 斯匹次卑尔根 | 应拦 | 不认为是本人 ✓ |

### 结论与 Sorby #133 **形状不同**

Sorby 那次的病是**误收**（父亲的署名被放行）。本人物没有这个病：
实跑 `_edits_within(x, "adolf", 2)`，全部同名者的名都够不着 ——
`alfred`✗ `arthur`✗ `eduard`✗ `martin`✗ `georg`✗ `friedrich`✗ `conrad`✗ `theodor`✗ `wilhelm`✗
（够得着的只有 `adolph` ✓ `adolfo` ✓ `adele` ✓，前两个就是他本人的拼写变体）。

**本人物的病是漏收，而且是系统性的**：

> `ocr_byline_evidence` 的「像不像署名行」那一关只认两种形状——
> `^By\s+…` 或整行全大写。**德文署名是 `Von …`**，
> 它连那一行都不会读，直接 `continue`。

于是对一个**全部作品都是德文**的人物，这个函数的产出接近恒为 `None`。
★★★ 而 `None` 在下游会被读成「没有署名证据」＝「没问题」——
这正是 [[empty-default-swallows-unknown]] 记的那个形状：**空值倒向了「没问题」而不是「可能有问题」**。

**处置**：本人物的归属不依赖 `ocr_byline_evidence`，改用下面这份 `namesake-criteria.json`；
入库时逐份人工核印本署名行，并把**照录的署名**写进台账 `author` 字段。
（把 `Von` 加进那个正则是对的改法，但那要动 `check_authorship.py`——
**不在抓源这一步改判据代码**，先记在这里。）

---

## 二、`namesake-criteria.json` 实测：31 组，全部符合预期

命令：`check_namesake_criteria.classify(text, CRIT, year)`，
判定三档 `目标本人 / 他人 / unknown`，**先排除、后区分符、说不准单列**。

### ① 12 个真同名者，全部判为「他人」

Eduard von Martens（动物学家）/ Friedrich Franz Martens（物理学家）/ Arthur Martens（滑翔工程师）/
Alfred Martens（建筑师）/ John Martens（建筑陶瓷）/ Rudolf Martens（Marinebaurat）/
Georg Friedrich von Martens（法学家）/ Friedrich Fromhold Martens（俄国法学家）/
Martin Martens（比利时化学家）/ Friderich Martens（1675）/ Conrad Martens（画家）—— 12/12 ✓

### ② 5 组目标本人的署名形态，全部判为「目标本人」

全名 / `Materialprüfungsamt` 机构署名 / `technische Versuchsanstalt` 旧机构 /
`Materialienkunde` 著作 / OCR 掉变音的 `Materialprufungsamt` —— 5/5 ✓

### ③ 「说不准」必须单列（3 组 ✓）

- 裸 `Von A. Martens. Stahl und Eisen 20 (1900) 802.` → **unknown，不是「目标本人」**
  （因为 Alfred Martens 1881-1920 与 Arthur Martens 1897-1937 署名形态完全相同）
- `Martens, Nouveau Recueil, Göttingen 1817` → 他人（1817 < 1878）
- 无年份的裸 `Martens.` → **unknown，不许假设它早于分界**

---

## 三、★★★ 实测打回来的三个真缺陷（都是**我自己第一版判据的错**）

### ⑴ 排除名单三条禁区——写进去会把目标自己的材料删掉

Sorby #133 的教训是 `IT. C. Sorby` 页眉把目标本人排掉，**而少了的东西不会报错**。
本人物有三条同形的坑，**都已实测**：

| 禁止入排除名单的字面 | 为什么它会命中目标本人 | 实测 |
|---|---|---|
| **`Dr. Martens`** | 他 1905 年获 TH Dresden 荣誉博士。德文文献称他 `Dr. Martens`／`Geh. Reg.-Rat Prof. Dr. Martens` 是常态。为了挡鞋类商标而排掉它 ⇒ 删掉他晚期几乎所有被引用的场合 | `Geh. Reg.-Rat Prof. Dr. Martens, Materialprüfungsamt.` → **目标本人** ✓ |
| **`von Martens`**（裸） | **德语 `von` 是介词「由……」**。`Die von Martens angegebene Methode` ＝「Martens 给出的方法」 | `Die von Martens angegebene Methode der Materialprüfung.` → **unknown（不是他人）** ✓ |
| **`Friedrich Martens`**（裸） | **他父亲就叫 Friedrich Martens**（NDB：Gutspächter）。每篇写家世的传记都有「Sohn des Gutspächters Friedrich Martens」 | `Adolf Martens, Sohn des Gutspächters Friedrich Martens.` → **目标本人** ✓ |

只许用带名或带首字母的完整消歧形式：`E. von Martens`／`G. F. von Martens`／
`Friedrich Fromhold Martens`／`Friedrich Franz Martens`／`Friderich Martens`。

### ⑵ 合著者与同题人物**不是同名者**，第一版误放进排除名单

第一版把 `Emil Heyn` / `Johann Bauschinger` / `Floris Osmond` 写进了 `excluded_names`。**已撤掉。**

- **Emil Heyn** 与目标**合著 Handbuch der Materialienkunde 第 2 卷（1912）**——排除他等于把目标最重要的著作之一判成他人。
- **Floris Osmond**：目标写过一篇专讲他的方法的论文，
  《F. Osmonds Methode für die mikrographische Analyse des gekohlten Eisens》Stahl und Eisen 15 (1895) 954-957。
  ★ 实测写全名 `Floris Osmond` 恰好不命中 `F. Osmonds Methode`——**但这是侥幸，不是理由**。
- **Johann Bauschinger**：目标与 H. Sollner 合编的 1893 维也纳会议录发表在
  **Bauschinger 主编的慕尼黑刊物**第 23 号（1895）。

合著关系由台账 `author` / `attribution` 字段承担，交给 `check_sole_authorship_overreach` 复核。
**本判据只回答「是哪一个 Martens」。**

### ⑶ `Mechanisch-technisch` 这个词根两城同形，第一版当区分符用了

| | 柏林（目标） | 慕尼黑（Bauschinger） |
|---|---|---|
| 机构 | Mechanisch-**Technische Versuchsanstalt** | Mechanisch-technisches **Laboratorium** |
| 刊物 | Mitteilungen aus den Königlichen technischen Versuchsanstalten zu Berlin | Mitteilungen aus dem Mechanisch-technischen Laboratorium … München |

**词根同形、机构不同城**，而目标 1893 年那份会议录**恰恰发在慕尼黑那份刊物上**——两边字面会绞在一起。
已把区分符从 `Mechanisch-technisch` 收紧为必须带 **`Versuchsanstalt`**（慕尼黑那家叫 Laboratorium）。

实测：`A. Martens u. H. Sollner, Mitteilungen aus dem Mechanisch-technischen Laboratorium Muenchen Nr. 23, 1895.`
→ **unknown**（收紧前会误判成「目标本人」）✓

---

## 四、判据里**刻意不用**的东西

- **首字母**。目标署 `A. Martens`；Alfred Martens（建筑师 1881-1920）、Arthur Martens
  （机械工程师 1897-1937）**署名形态完全相同**。首字母在本人物上是歧义源，不是区分符。
- **刊名里有 `Materialprüfungsamt`**。★★★ *Mitteilungen aus dem Königlichen Materialprüfungsamt*
  是**机构连续出版物**，作者是全所各人（Emil Heyn 等）。**刊名 ≠ 著者**，必须逐篇看印本署名行。
- **题材是马氏体/金相**。那是**关于他**，不是**他写的**。题材词只能定 tier，不能定 authorship。
- **地名 Berlin / Charlottenburg**。F. F. Martens 也在柏林。已刻意不列入 `any_of_markers`。

## 五、裸 `A. Martens` 的人工裁定规则（判据只会报 unknown）

| 情形 | 归属 |
|---|---|
| 1878-1914 + 机械/冶金/材料试验类德文刊物 | 目标本人 |
| **≥1919** | **一律不是目标**（他 1914 卒）：机械/航空→Arthur，建筑→Alfred |
| 建筑与营造类行业刊物 | 先按 Alfred / John / Gustav Ludolf Martens 处置 |
| 造船类刊物 | 先查 Rudolf Martens（Marinebaurat 1868-1911） |
| 物理/光学/高频类刊物 | 先查 Friedrich Franz Martens（1873-1939） |
| < 1878 | 判据已自动判为他人 |

---

## 六、跑判据本身

```
$ python3 scripts/check_namesake_criteria.py --self-test
✓ 自测全过

$ python3 scripts/check_namesake_criteria.py <workspace>
  wip-martens-134：还没有 source-ledger.jsonl，**只做自检不判源**
✓ unknown 0 条
```

★★★ **那个「unknown 0 条」不是绿灯，是「还没有台账」**——
同一句话在有台账和没台账时长得一模一样。这正是 [[empty-default-swallows-unknown]]。
**入库后必须重跑一遍，以那一次的数为准。**
