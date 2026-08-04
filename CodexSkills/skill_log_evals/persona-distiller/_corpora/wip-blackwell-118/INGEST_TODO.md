# 入库时必须逐条核的（**不要提前填 meta.json**）

工作区已建（deep 档、historical、1821–1910）。研究门基线 **5 条错误**，全是语料相关：

```
✗ source.minimum          usable train sources 0 < 45
✗ source.primary-ratio    0.0% < 65%
✗ source.lane-coverage    0 lanes < 6
✗ research.attribution-basis   historical 人物未声明 attribution_basis
✗ research.lane-completion     0 lanes < 6
```

---

## ★ `attribution_basis` 现在**故意空着**

它是人物属性、看上去现在就能填。**但 Barton #117 那份填的是实测到的原文**
（`Copyright,   1898,  by   Clara    Barton`，rc-peace-war-1899 三处）。

我现在手上**没有任何一份 Blackwell 的原文**，能写的只有推断
（「十九世纪美国刊行物应当有扉页与版权页」）。
**把推断写成依据、然后让门变绿，正是「装饰性引用能过质检门」那个坑。**

**入库之后照下面三条实测，再填。**

### 要核的三层

| 层 | 该有什么证据 | 核法 |
|---|---|---|
| **刊行物** | 扉页署名／版权页 | `grep -i 'blackwell'` 找扉页行，**照录原文**，记 source_id 与出现次数 |
| **档案手稿** | LoC 藏品编目（日记、讲稿、书信） | 记藏品全称与编号；**日记与草稿不署名，归属依据在档案层不在文本层**——与 Barton 同型 |
| **他人来信** | 收信人是她 ≠ 她写的 | **一般通信是「寄给她的」，属二手**，不许当一手计入 `primary_ratio` |

---

## ★★ 同名判别：每一份都要过（见 `DISAMBIGUATION.md`）

另有 **Elizabeth Blackwell（1707–1758）**，苏格兰植物图谱画家，
《A Curious Herbal》**高度数字化且在公有领域**，按名字检索必然大量返回她。

1. **1758 年以前的东西一律不是**（本人 1821 年才生）
2. 题名出现 *Herbal*／植物图版 → 弃
3. 正文自证：Geneva Medical College／New York Infirmary／Emily Blackwell／
   Nightingale／M.D. 之一；**找不到就标 U，不要猜**

---

## 出答案时（别等到判分才想起来）

1. **按裸模型的默认体裁写：散文，不加粗体、不加反引号、不分条。**
   四人实测 116/128 = 91% 的题可被一条正则指认候选侧——Barton 是 32/32。
   **逐字引文继续用「」**（判据靠它认引文，去掉等于把三道引文判据弄瞎）。
2. **写每题前先把题面写死的约束列出来，逐条对着答。**
   Barton 三处失分：称号自我介绍答成履历、已写「不用管史实」仍拒写、无视「三天后才能进场」。
3. 用共享件，不要再各写各的：

```bash
python3 scripts/build_blind_payload.py --workspace <target> --round-dir round1 \
  --candidate eb_candidate.json --baseline eb_baseline.json --prefix eb
python3 scripts/assemble_judge_results.py --workspace <target> --round-dir round1 \
  --seat seat-D-score-v1:eb_judge_D.json --seat seat-E-strict-v1:eb_judge_E.json
```

`build_blind_payload` **生成时就跑表面特征泄题门，未过退出 1、不许派发**。

---

## 已完成（2026-08-04）

- 语料 95 份入库，研究门 **101 → 1 条**（只剩 `lane-completion`，属合成阶段）
- 归属逐源实测：56 份靠 A-* 署名、18 份逐份点名照录原文、**0 份未认领**
- holdout 6 份，**硬失败 0 / 待人工核 0**
- `attribution_basis` 四字段齐全，引的是实测原文

## 下一步：断言层

候选事实已抽好并落盘：

| 文件 | 内容 |
|---|---|
| `_facts_raw.txt` | 814 条，全 train 侧 P1 |
| `_facts_good.txt` | 398 条，滤掉印刷页与广告 |
| `_facts_subst.txt` | **603 条，只取 49 份实质性一手**（排除日记与家庭通信） |

**日记不适合做事实断言**——逐日流水（天气、家用账、访客名单），
它们的价值在 `expression` 与 `timeline`，不在 `fact`。

### 污染的边界已量清（★ 我第一版把它说大了）

第一版我写「污染不止那两处」，**下得太快**。全 95 份按「分类广告 + 货币栏」密度扫过，
再逐条核实际命中之后：

| 处 | 实况 |
|---|---|
| `contaminated-1247` / `contaminated-1265` | 整版报纸剪贴簿，**已标 U** |
| 16 册日记里的 `£` | **绝大多数是印刷的邮资/汇兑费率表**（`2d. under 10s 5d. under £4.`）——即已量过的那 4.1% 印刷页；而 `20 £100 for Indian work from [Mme de N.?]` 是她自己的条目 |
| `sp-1268`（英国慈善演讲笔记） | `£3000 from Magdalen`、`£500 a year` 是**演讲内容本身**，干净 |
| `sp-1261` | **末尾接了一张剪报**：第 1797–1811 行、约 284 词 = **1.7%**，一整栏「SITUATIONS WANTED」求职广告，从她的句子中断处突起（`…would be justified.SITUATIONS WANTED`） |

**`sp-1261` 那一段是她剪贴作论据、还是众包转写了无关剪报，从文本本身判不了**
——但后果相同：**那 15 行不许当她的话引**。已写进该源的 `attribution`。

★ 同一份里另有 3 处 `apply to` 是她自己的行文
（`may apply to the police`、`This term should apply to both sexes`）——
**按密度筛会把它们一起冤枉**。密度是线索，不是判决。

### 已回原文核过的生平锚点（可直接做 fact 断言）

- `Geneva: October 20, 1847.`（Geneva Medical College 录取的时间锚）
- `Geneva University to acknowledge receipt of yours of 3rd inst.`
- `La Maternité, a world-famous institution, and remain until I have succeeded in my first object—viz.`
- `Blockley Almshouse, a large room on the third floor had been appropriated to my use.`
- `In 1849, with a population of 314,000, and an inert public opinion, there were 211 brothels, with 538 inmates.`（*Wrong and Right Methods*，带三个可核数字）
- `lecture was prepared by Drs. Elizabeth and Emily Blackwell`（1860 年那篇是姐妹合备）

### 出答案时照 v0.0.0.81 的两条（母版里也有）

1. **散文体裁**，不加粗体/反引号/分条；逐字引文用「」
2. **写每题前先列题面写死的约束，逐条对着答**
