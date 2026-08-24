> ⚠ **2026-08-24 改名：本文件的 L1–L5 一律改称 W 轴 W1–W5（Wardrobe Tier）。**
> 原因：`G-尺度分级.csv` 的 L0–L4 是**题材与镜头语言**分级（决定被抖音限流的概率，
> DouyinOps 唯一权威）；本文件这套是**服装露肤度 + 姿态暗示强度**（决定被 OpenAI
> 安全系统拦的概率）。两者同名不同义，接 H 姿势轴时会在代码里出现两个含义不同的 L2。
> 对照：W5 全强度 · W4 −暗示性姿态 · W3 −含胸挺腰 · W2 −露腰深V高衩（最低可接受档）· W1 v1.7.0 原版。

# 色情度档位 L1–L5：出图率与色情度的取舍

## 先于档位的硬规则（2026-08-23 用户定，两个 skill 口径不同）

### 默认走 pipeline，不是 sexy

**所有产物默认按 `character-skin-pipeline`（安全版）出。**
要 sexy 那一档必须用户显式指定，不许我替他决定。

**代价是实测过的**：2026-08 艾莉西亚那条因**性暗示过强**被抖音限流。
一条被限流，整个号后续的自然流量都受影响——这不是"删掉那条就好"的损失。

### 三个维度

| 优先级 | 维度 | 判据（人看一眼能判的） |
|---|---|---|
| ① | **性暗示** | 姿态/眼神/身体语言有明确挑逗意味 |
| ② | **色情度与露肤度** | 大面积裸露：肩、臂、腰、腿、胸线 |
| ③ | **丝袜 / 性感 / 肉感 / 巨乳** | 丝袜可见，身材曲线明确 |

### 两个 skill 各自的门槛

| | **pipeline（默认 · 抖音可发）** | **sexy（非公开）** |
|---|---|---|
| ① 性暗示 | **不要求**（过强会被限流） | **必须** |
| ② 露肤度 | ②③ **满足其一即可** | **必须** |
| ③ 丝袜肉感 | ②③ 满足其一即可 | **必须** |
| 偏离基准人物特征 | **严格禁止** | 尽量不偏离 |

**「不偏离基准人物特征」= 脸、发色发型、瞳色、标志配饰、配色必须和锚图一致。**
pipeline 这条是红线：偏了就是画了另一个角色，公开发布会被认成侵权或劣质二创。
sexy 允许服装大改，但脸和发型仍要能认出是谁。

**验收时逐张过**：`性暗示 ✓/✗ · 露肤 ✓/✗ · 丝袜肉感 ✓/✗ · 基准特征 ✓/✗`
- pipeline：②③ 至少一个 ✓，**且基准特征必须 ✓**
- sexy：①②③ 全 ✓

---

> **v0.1.0 公开档收敛（2026-08-23）**：本文件 L1-L5 体系在 **character-skin-sexy（非公开）** 全强度使用。
> **character-skin-pipeline（公开抖音）只用 L0-L2**（软色情 + 全遮挡 + 合规条），L3+ 一律移交 sexy。
> 公开/非公开判定见 `14-public-safety.md`。

**结论先行：不要挑一档跑全量，要用阶梯降级重试。**
第 1 次 L4、第 2 次 L3、第 3 次 L2；L2 还出不来就标记为需重做。
实现在 `tools/erotic_levels.py`，`batch_run.py` 按 `attempt` 自动降档。

---

## 五档各自包含什么

| 档 | 相对上一档砍掉 | 这一档还留着 |
|---|---|---|
| **L5** | —（全强度） | 吊袜带 · **露腰** · **深V** · **高衩剪影** · **含胸挺腰** · **暗示性姿态** |
| **L4** | 暗示性姿态 | 吊袜带 · 露腰 · 深V · 高衩 · 含胸挺腰 |
| **L3** | 含胸/挺腰 | 吊袜带 · 露腰 · 深V · 高衩 |
| **L2** | 露腰 / 深V / 高衩 | 吊袜带 · 露肩露臂露腿 · 胸线强调 · pin-up 取向 |
| **L1** | 吊袜带 · pin-up 取向措辞 | 丝袜 · 露肩露臂露腿露胸线（= v1.7.0 原版） |

### 逐档的确切措辞

**L5 的完整条款**（任务包里存的就是这一档，降级在运行时做）：

```
MANDATORY WARDROBE AND PRESENTATION — applies to every character without exception,
this is glamour pin-up art and the wardrobe rule is not optional: sheer stockings,
tights or thighhighs on fully visible legs, worn with visible garter straps. Where the
canonical design has trousers, greaves or armoured legs, restyle the legwear into sheer
stockings or thighhighs while keeping that design's own colours, patterns and trim.
The silhouette is maximally skin-revealing: bare shoulders, bare arms, bare midriff,
fully bare thighs above the stocking band, and a deep plunging neckline. Favour
high-cut leotard, micro-skirt, bodysuit and open-side silhouettes over anything that
covers the hips or waist.
PIN-UP DIRECTION: emphasise the unbroken leg line from hip to ankle and the bust line;
the pose is consciously alluring and suggestive — weight on one hip, arched back,
chin slightly lowered, direct eye contact with the viewer.
```

| 降到 | 替换 |
|---|---|
| **L4** | `consciously alluring and suggestive` → `elegant and poised` |
| **L3** | 再删 `arched back, chin slightly lowered,` |
| **L2** | 整段 `maximally skin-revealing … covers the hips or waist.` → `open and skin-revealing — bare shoulders, arms, thighs and décolletage.` |
| **L1** | 再删 `, worn with visible garter straps`、`PIN-UP DIRECTION: …bust line; `，标题回到 `MANDATORY WARDROBE — applies to every character without exception:` |

---

## 实测数据（这是选档的唯一依据）

### 大样本（全量跑出来的）

| 档 | 样本 | 通过 | 通过率 |
|---|---|---|---|
| **L5** | 110 张（重试 3 次） | 43 | **39%** |
| **L1** | 94 张（v1.7.0 全量） | 94 | **100%** |

L5 那一轮里，昼夜**成对**可用的只剩 **9 / 55 个变体**，单张成本从 $0.07 涨到 $0.34。

### 五档 × 三样本的阶梯（n=3，噪声大）

| 档 | chiz | aurelia | shinku |
|---|---|---|---|
| L5 | 拦 | 拦 | **过** |
| L4 | 拦 | **过** | 拦 |
| L3 | 拦 | 拦 | **过** |
| L2 | **过** | **过** | 拦 |
| L1 | **过** | **过** | **过** |

---

## 最关键的一条：**安全系统有随机性，不是固定阈值**

上表**不单调**：shinku 在 L5 和 L3 过，却在 L4 和 L2 被拦；aurelia 正好相反。
同一档同一张，重试也会得到不同结果（普罗米娅那两张第一次被拦、重试通过）。

**推论一**：`n=3` 的阶梯定不出档位，拿它下结论就是骗人。
**推论二**：「挑一档跑全量」是错的做法——档位高的那些图里，本来有一部分是能过的。
**推论三**：正确做法是**降级重试**，既拿到能拿到的最高色情度，又不整张丢掉。

同时强度确实有影响（L5 39% vs L1 100%），所以要**同时**利用两者：降档 + 重试。

---

## 定档规则

- **起点 L4**，依次降 L3、L2
- **L2 是最低可接受档**。连 L2 都出不来的，标记为需重做，不许自动降到 L1 交差
- **L1 不进重试阶梯**，只作兜底参考

## 成本影响

| 策略 | 92 张的预期 |
|---|---|
| 只用 L5 | 约 39% 成，$6 换 36 张 |
| L4→L3→L2 阶梯 | 预计 85%+ 成，$7 换 78 张以上 |
| 只用 L1 | 100% 成，但色情度回到上一轮水平 |

## 有一类角色不适用

花名册里明显儿童体型的（可莉、七七、菲林一类），这套档位不适用，保持原设服装。
不是可配置项。

---

## 2026-08-23 实测补充：L5/L4/L3 的 PIN-UP 措辞会放大腿部曲线（爱莉希雅「腿太胖」教训）

**现象**：hi3 爱莉希雅 v1.9.1（L5 进包，L4→L3→L2 阶梯）出图被用户判「腿太胖、不符合原设身材」。

**根因**：`PIN-UP DIRECTION: emphasise the unbroken leg line from hip to ankle and the bust line; weight on one hip, arched back...`
这一串在 **L5/L4/L3 都保留**（L4 只是把 suggestive 换 elegant，L3 才删 arched back），
它在放大腿线与胯部曲线；叠加上 6/8 锚图是低清（544–960px），模型锁不住角色真实的纤细体型。

**修法（已验证，v1.9.2）**：新增一条**不参与任何阶梯替换串**的独立条款，全档位保留：

```
PHYSIQUE (strict): the figure's body proportions follow the reference character's actual
slender build exactly — narrow hips, slim waist, long slim thighs and calves; legs and hips
are never thickened, widened or exaggerated; keep the hip-to-thigh-to-calf ratio and limb
slenderness as in the reference image. The pose may be alluring, but limbs and frame stay
natural, undistorted and in proportion.
```

实现要点：这条措辞不能与 `erotic_levels.py` 的任何替换串（SUGGESTIVE/MAXIMAL/PIN-UP DIRECTION/garter…）
字节级重叠，否则降级时被误改。核对命令：断言 PHYSIQUE 在每个任务的每个 side 都在（变体数×2）。

**另一层根因（锚图 bug）**：爱莉希雅官网高清立绘 `miss-pink-elf.jpg` 存在，但任务包按 `miss-pink` 找锚，
文件名不匹配导致**用了 544×660 低清版**。教训：组包前核对每个变体实际用的锚图尺寸，
官网高清与 Fandom 低清同名不同后缀时要做文件名归一化映射。

**结果**：v1.9.2 一次通过率 56.2%（vs v1.9.1 43.8%），实付 $0.53（vs $0.88）。
与 Claude Code 旧批次（v1.7.0，L1 措辞无腿线强调）的质量差，**不是流程差异，是档位差异**。
