# #104 Edward Jenner —— 可续检查点

日期：2026-08-02　｜　蒸馏版本 `v0.0.0.32`　｜　状态：**工作区已建，待抓源**

---

## 一、已完成（全部实跑）

| 步 | 命令 | 结果 |
|---|---|---|
| 配重选人 | `next_person.py` | NEXT = Edward Jenner，`mode: counterweight`，`slot: 0`，挤掉材料建工师（已 15 人） |
| 同名门 | `namesake_gate.py --name "Edward Jenner"` | `resolution: single`、`status: ready`、`selected_subject_uid: edward-jenner-1749` |
| 建工作区 | `init_target.py --profile deep --subject-origin historical --language en --time-scope 1749-1823` | `status: draft`，落在 `ws-jenner/ws-jenner` |

同名门实搜结论：**Wikipedia 无 `Edward Jenner (disambiguation)` 页**——本族四人里同名风险最低的一位。
干扰只有两类：机构名（Jenner Institute／Edward Jenner Museum）与**家族内重名（其子 Edward Jenner Jr.）**，后者靠年代分辨。

---

## 二、★ 为什么选他不只是配重的结果

**本周反复出错的那一类，在他身上从源头上不成立。**

Livermore／Vesalius／Harvey 三人共六轮盲判，同一条错每次都被席 E 抓出：
**把译者的英文（或第三人称传记句）当成本人原话。** v0.0.0.32 的 `check_quote_layer.py`
就是为它落成的。

而 **Jenner 本人用英文写作**。《An Inquiry into the Causes and Effects of the Variolae
Vaccinae》(1798) 是英文原著，`archive.org/details/b24759247` 有全本。
**逐字引文即原文，无译文层。** 这不是运气，是**选人时可以主动利用的结构条件**——
应写进选人口径。

---

## 三、★★ 三次失败留下的判据，必须照着做

| 人物 | 人物事实 : 账本事实 | 三轮真 delta | 失败形态 |
|---|---:|---|---|
| Galen #101 | 10 : 5 | −0.1944 / −0.1259 / −0.1456 | **补的是我的账本，不是他的知识** |
| Vesalius #102 | 23 : 0 | −0.0292 / **+0.0077** / **+0.0156** | 密度对了，**但 +0.0156 < quick 门 0.03** |
| Harvey #103 | 24 : 0 | −0.0411 / −0.0300 / −0.0383 | **密度最高却仍为负——因为我编了对手的立场** |

结论**已被三次实测钉死**：

1. **账本事实（多少词、多少部、占比多少）一条都不要。** 用户拿不走。
2. **密度是必要不充分。** Harvey 24 条人物事实仍是负的。
   `check_fact_density.py` **数的是形态**，这写在它自己的 docstring 里，
   **它挡不住「我把内容编出来了」**。
3. **Vesalius 是唯一一个把 delta 做正的**，差的只是从 +0.0156 到 0.03。
   **方向已经证明是对的，缺的是量。**

### 因此 Jenner 的硬约束（写在开工前，不许中途放宽）

- **每条「对手主张 X」必须指到对手的书与页。** 这是 Harvey 那次最严重的错
  （我编了 Riolan 的立场，还用「先证据后动机」的架子把它包装得格外像话），
  **`check_quote_layer.py` 完全挡不住它**——只能靠这条纪律。
- 目标不是「凑够 N 条事实」，是**每条都能回原文 grep 到**。
  Jenner 是英文原著，这一条比前三位都容易验，**因此没有借口**。
- 一手源以《Inquiry》(1798)、《Further Observations》(1799)、
  《A Continuation of Facts and Observations》(1800) 与书信集为主。
  **`_verified` 与 `_not_verified` 分开记**（候选文件里已开了这个格式）。

---

## 四、下一步（按顺序）

```bash
# 1. 抓源：一手为主，逐条实测 HTTP 200 并记 tier / split
#    deep 档要求：min_sources 45、min_primary_ratio 0.65、min_lanes 6
# 2. python3 scripts/ingest.py <ws> INPUT...
# 3. python3 scripts/quality_check.py <ws> --phase research --strict
# 4. 断言层：人物事实优先，账本事实一条不写
# 5. 32 用例盲测（A/B 由 sha256(case_id)%2 定，评委不给判据）
# 6. 两席独立子代理判分，**上限 3 轮**
# 7. python3 scripts/quality_check.py <ws> --phase release --strict
```

## 五、待核（本轮未核，抓源阶段必须核）

1. **1788 年因杜鹃雏鸟研究入皇家学会**——生平叙述里常见，**我未单独核**。
2. **其子 Edward Jenner Jr. 的生卒年**——同名门靠年代分辨，这个数必须坐实。
3. **皇家学会退稿一说**——广泛流传，**须找到一手依据或降级为 hypothesis**。

---

# 续记 · 2026-08-02（研究门 + 断言层全绿）

## 已完成

| 步 | 结果 |
|---|---|
| 抓源 | **53 份真语料**（原 47 份里 4 份是 HTML 错误页，已由 v0.0.0.33 入口硬拦剔除；另补取 8 份） |
| ingest | 53 成功 / 0 失败，1 份 holdout |
| `attribution_basis` | 四字段齐，`disputed_works: []` 且写明为何为空 |
| 归属 | 30 条 P1 源逐条挂 attribution |
| 研究六路 | **六路全 complete**，`errors 0` |
| 断言层 | **29 条，其中 fact 16 条全部是人物事实、账本事实 0 条**（要求 11） |
| `corpus_integrity` | 已扫 53，不是语料 0，可疑 0 |

## ★ 断言层里最硬的三条（都可回语料 grep）

1. **1798 初版里没有「Phipps」**——第 XVII 例原文只写 `a healthy boy, about eight years old`。
   实测初版 0 次、1800 三版 3 次。**名字是后来版次加的。**
2. **「Blossom」三个版次一处都没有**（实测各 0 次）。而 Sarah Nelmes 在初版里有 2 处并配图版。
   **他给了那个女人名字，没给那个男孩名字。**
3. **扉页印着 `PRINTED, FOR THE AUTHOR`**，题词是卢克莱修
   `QUID NOBIS CERTIUS IPSIS SENSIBUS ESSE POTEST, QUO VERA AC FALSA NOTEMUS`。
   **自费出版是扉页上的字，不是转述。**

## 下一步（按顺序）

```bash
# 1. 合成阶段文档（docs/*.md）+ quality_check --phase synthesis --strict
# 2. 32 个评测用例（16 套组 × 2），A/B 由 sha256(case_id)%2 定
# 3. 生成候选答案与裸模型基线
# 4. 两席独立子代理盲判，**上限 3 轮**（judge_prompts v1 按人物冻结）
# 5. quality_check --phase release --strict
```

## 三条硬约束（跑答案时不许破）

1. **账本事实一条不写。**（Galen 10:5 → −0.15）
2. **每条「对手主张 X」必须指到对手的书。**（Harvey 编造 Riolan 立场 → −0.038）
   Moseley／Birch／Lipscomb 的书目已在 `04-external.md` 列全。
   **Woodville 是复现者不是反对者**，不许混为一谈。
3. **凡引 Baron 转录的书信须写「据 Baron 转录」。**
   凡引 1798 原文须注明长 s 已还原（`check_quote_layer.py` 管这一条；
   **他写英文，无译文层，这是本人物的结构性优势**）。
