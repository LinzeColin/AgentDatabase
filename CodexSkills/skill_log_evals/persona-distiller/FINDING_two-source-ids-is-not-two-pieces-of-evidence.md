# 「两个 source_id」不等于「两处证据」——11 人里 7 人有塌缩

日期：2026-08-04　发现方式：**给 #118 写断言前，发现两份「不同的源」句子逐字相同**

---

## 一、怎么发现的

给 Elizabeth Blackwell #118 的非事实断言找跨源证据时，取到两段：

```
[src-439bd46a6e3b] sp-1260-why-hygienic-congresses-fail
   「, that it is to sanitation that we must look, not only for the prevention of disease,
     but largely also for its cure.」
[src-40dc1c83b4fc] essays-medical-sociology-v2-1902
   「, that it is to sanitation that we must look, not only for the prevention of disease,
     but largely also for its cure.」
```

**逐字相同。** LoC 的讲稿手稿是后来收进《Essays in Medical Sociology》的那些文章的**底稿**。

全量量了一遍：**33 份 LoC 讲稿手稿里 18 份是印本的草稿**，重叠 51–90%：

```
essays-medical-sociology-v2-1902 ← sp-1235(89%) sp-1238(87%) sp-1242(85%) sp-1248(90%)
                                   sp-1250(59%) sp-1253(82%) sp-1257(84%) sp-1258(68%) sp-1260(81%)
essays-medical-sociology-v1-1902 ← sp-1244(73%) sp-1252(70%) sp-1254(64%) sp-1255(51%) sp-1256(64%)
wrong-right-methods-1883         ← sp-1261(60%) sp-1262(76%)
medical-education-women-1864     ← sp-1236(76%)
counsel-to-parents-1878          ← sp-1240(52%)
```

**引手稿＋引它的印本，字面上是两个 `source_id`，实质上是一处证据。**

★ 中途我的度量脚本报「0 份重叠」，**而我手上有直接反证**（刚看到逐字相同的两段）——
一查是 glob 写错了：工作区里目录名是 `src-<hash>`，不是短名，`raw/sp-*` 一条都没匹配上。
**报 0 之前先怀疑工具，这次靠反证当场发现。**

## 二、既有判据一件都拦不住

| 判据 | 它管什么 | 为什么拦不住这个 |
|---|---|---|
| `check_claim_anchors` | 断言有没有挂上源 | 挂上了，两个 id 都真实存在 |
| `check_evidence_is_per_claim` | 这个字段有没有区分度 | **有区分度**——两个 id 确实不同 |
| `check_holdout_overlap` | train/holdout 之间有没有泄漏 | 这两份都在 train 侧 |

**没有一件在问：这两份源是不是同一部作品。**

## 三、落成 `check_claim_source_independence.py`

对每条有 ≥2 个 `source_ids` 的断言，两两算 8 词片重叠率，
**以较短的一侧为分母**（草稿常常只是印本的一节；拿印本当分母会把 90% 的重复算成 5%
——这一条已固化为反向对照 ⑤：同一组数据长侧分母 29.6%、短侧 100.0%）。
重叠 ≥30% 判为同一部作品；一条断言的全部来源塌缩成 1 部作品即报出。

9 项自测全过，其中 6 组反向对照（引两部真不同的书不许报、只引一个源不归本门管、
`fact` 类不归本门管、`superseded` 不判、分母方向、引了语料里没有的 id 不算独立证据）。

## 四、落成后全量回扫：**11 人里 7 人有塌缩**

| 人物 | 多源断言 | **塌缩** | 来源数 → 作品组数 |
|---|---:|---:|---|
| robert-koch | 17 | **17** | 121 → 93 |
| joseph-lister | 17 | **17** | 61 → 26 |
| rudolf-virchow | 17 | **8** | 227 → 133 |
| william-osler | 17 | **5** | 104 → 36 |
| louis-pasteur | 17 | **5** | 60 → 28 |
| ws-jenner | 16 | **3** | 53 → 33 |
| florence-nightingale | 12 | **2** | 117 → 50 |
| clara-barton | 12 | 0 | 214 → 149 |
| alexander-fleming | 15 | 0 | 69 → 67 |
| seth-godin | 20 | 0 | 196 → 196 |
| michael-steinhardt | 22 | 0 | 55 → 52 |

**合计 57 条断言的「多份来源」实为一处证据。**
（semmelweis 的 `claims.jsonl` 为空，报「未核验（不是通过）」。）

**Koch 那 17/17 正是此前手工发现的那件**（46 条断言的 `source_ids` 全是同一对）
——**现在机器抓得住了**。**Lister 17/17 是新发现。**

## 五、它说的不是什么

- **不说这些断言是编的。** 它只说**支持它的证据比看上去少**：
  出问题时回不到两处独立的地方去核。
- **不判引得对不对。** 两份真独立的源也可能都不支持那条断言——那是人的活。
- **阈值 30% 是按 #118 实测形状定的**（真重复 51–90%，真独立 <10%，中间是空的）。
  **没有实测支持把它设在别处，也没有实测说它跨人物成立。**

## 六、只写 metrics，不拦

已入库的人从没按这条回扫过，**硬拦会把整个名册一起拦下**——
与 `NO-SELFTEST`、新鲜度门、引文层门同一条纪律。

**这 57 条属于「已入库产物的技术债」那一项**（任务 #15，待用户定做不做）。

参见 [[gate-green-but-pointed-at-wrong-artifact]]、[[judge-critique-becomes-a-checker]]。
