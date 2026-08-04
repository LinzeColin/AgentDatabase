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
