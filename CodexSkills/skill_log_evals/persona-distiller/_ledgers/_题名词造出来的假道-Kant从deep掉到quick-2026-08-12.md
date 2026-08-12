# 题名词造出来的假道 —— Kant #179 的 6 条道有 3 条不存在

2026-08-12。写第 1 批研究道时发现的。**结论是档位级的**：
Kant 原判 `deep`，而 deep 要求 `min_lanes 6`——**他那 6 条道里有 3 条是题名词误配出来的**。
修正后 3 条，档位落到 `quick`。

## 三条假道，三种误法

| 假道 | 命中的词 | 那本书实际是什么 |
|---|---|---|
| `timeline` ×3 | `chronolog` ⊂ `in **chronolog**ischer Reihenfolge` | 《全集》**按年代编次**——那是**版本的编排方式**，不是生平年表 |
| `decisions` ×1 | `judgment` ⊂ `Critique of **judgment**` | 《判断力批判》是**著作**，不是判断/判决的记录 |
| `expression` ×3 | `oration` ⊂ `comme**moration**` | 《纯粹理性批判》英译本的副题「百年纪念版」——**纯子串误配** |

第三条与 [[regex-must-clear-the-corpus-language]] 记的 `lister` ⊂ `callister`、
`A.L.S` 匹配德语 `als` 是同一类。前两条不是子串问题，是**语义**问题：
词对了，而它在题名里说的是**版本**或**书名**，不是体裁。

## 第二发现：`discourse` 这个词分不出讲辞和专著

`expression` 的定义是**对外的短篇表达**。而实测：

| 人 | 该道份数 | 其中是专著的 |
|---|---:|---|
| Rousseau #178 | 9 | **8**（《Discours sur l'origine … de l'inégalité》） |
| Machiavelli #177 | 10 | **9**（《论李维》Discorsi / Discourses on the first decade） |

17–18 世纪 discourse／discours／discorsi 指的就是「论」。
**同一个词在林肯那里才指演说。** 已从 `expression` 的题名表里整个移除；
移除后它们落进 residual ⇒ writings，**道数不虚增**。

## 审计口径：142 → 3

先按「匹配是否落在词边界内」扫全批 676 份，得 **142 条**。
**逐条读完只有 3 条成立**——其余是
`decision`→`decisions`、`rede`→`reden`、`letter`→`letters`、`autobiograph`→`autobiography`
这类词形变化，以及 `Bismarck**briefe**`／`Bismarck**reden**` 这类德语合成词（分对了）。

⇒ 收紧成「**匹配前面还有字母**」后剩 9 条，其中 6 条是德语合成词，3 条是 Kant 的 `commemoration`。
**报率之前先读命中**（[[read-the-hits-before-reporting-the-rate]]）。

## 档位重定（这是要交出去的数）

| 档 | 修正前 | 修正后 |
|---|---|---|
| deep | 6：Marshall / Lincoln / Jefferson / Bismarck / Pestalozzi / **Kant** | **5**（Kant 掉出） |
| quick | 3：Machiavelli / Rousseau / Fröbel | **4**（+Kant） |
| 记延后 | Comenius #182（通道受限） | 同 |

实测值（`份数 / 道数 / 一手占比`，门 `deep 45 / 6 / 0.65`）：

    marshall-173      95  6  0.7684  deep
    lincoln-174       70  6  0.9714  deep
    jefferson-175     73  6  0.9178  deep
    bismarck-176      70  6  0.9000  deep
    pestalozzi-180    70  6  0.9857  deep
    machiavelli-177   79  4  0.8481  quick
    rousseau-178     103  4  0.8835  quick
    frobel-181        51  5  0.9804  quick
    kant-179          65  3  0.9692  quick   ← 原 6 道

## 为什么门不会自己发现

`check_corpus_ceiling` 数的是 `dimensions` 字段里有几种取值，**它不问那个取值对不对**。
与 [[gates-count-sources-not-voice]]（门数的是来源，不问那些第一人称属于谁）
和 [[related-to-him-is-not-written-by-him]]（门只做分档字段的算术，不问分档对不对）
是同一族：**门算的是我填进去的字段，字段错了门就跟着错。**

★ 而这一次它的方向特别坏：**误配只会让道数变多，不会让它变少**——
一份本该进 writings 的书被放进空着的 timeline，`lanes` 就 +1。
`writings` 在任何有语料的人身上都非空，residual 落进去只可能让计数不变。
⇒ **题名词误配是单向的，永远朝「更够得着高档」漂。**

## 落成了什么

- `assign_lanes.py`：`oration` 加词边界；新增 `WORKS_OVERRIDE` 三条
  （版本编排词 / critique·kritik / discorsi·discourses 论某部史书）；
  `discourse` 系整个从 `expression` 移除。
- 正负对照：4 条专著必须归 writings、6 条真讲辞与书信不能被误伤，**全过**；
  第一版的 `discours?e?s?` 只写了英语那一支，正对照当场抓到
  `Discorsi sopra la prima deca` 没被覆盖（意大利语无 u）。

相关：[[categoryid-taxonomy-must-be-proven]]（映射要 grep 不要推导）、
[[counts-need-their-cutoff-stated]]、[[two-errors-cancelled-so-the-gate-stayed-green]]。
