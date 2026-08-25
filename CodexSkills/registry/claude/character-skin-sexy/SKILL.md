---
name: character-skin-sexy
description: 角色皮肤的**非公开**高色情度产线（私域/付费/测试用途）。Use when 需要 L3-L5 色情度拉满的角色素材（吊袜带/深V/高衩/pin-up 全强度），或 character-skin-pipeline 阶梯降级到 L2 仍不够时。**边界铁律（不可协商）**：本 skill 产物**绝不进公开抖音**（G 轴 L3/L4 = 限流 30 天实测），公开发布一律走 character-skin-pipeline（安全版）。覆盖：L3-L5 档位 prompt、pin-up 全强度措辞、阶梯降级重试、产物隔离标记、非公开登记。
version: 0.2.1
metadata:
  category: pipeline
  scope: 非公开（私域/付费/测试）
  source_project: character-skin-pipeline 拆分（2026-08-23）
---


## 参考

- `references/16-hosiery.md` —— 丝袜类型选择（三层：幼态豁免 → 用户覆写 → 配色推断）

## 与 pipeline 的分工（2026-08-23 用户定）

**默认不是本 skill。** 所有产物默认走 `character-skin-pipeline`（安全版），
本 skill 必须由用户显式指定才启用。

| | pipeline（默认） | **sexy（本 skill）** |
|---|---|---|
| 性暗示 | 不要求 | **必须** |
| 露肤度 | ②③ 满足其一 | **必须** |
| 丝袜/肉感/巨乳 | ②③ 满足其一 | **必须** |
| 偏离基准人物特征 | 严格禁止 | **尽量不偏离**（脸和发型仍要能认出是谁） |

**三个维度全部满足才算过**，缺一个就退回重做，不许拿档位低当理由。

## 产物一律私有

本 skill 的产物全部写进 `~/.harness-ui/private_only.json`，
目录项 `public:false`。**绝不进抖音等公开平台**——
2026-08 艾莉西亚那条因性暗示过强被限流，一条影响整个号的自然流量。

# 角色皮肤产线 · sexy（非公开高色情度）

从 character-skin-pipeline 拆出的**非公开**档位。与 pipeline 严格隔离。

## ★ 边界铁律（不可协商）

1. **绝不进公开抖音**：G 轴 L3/L4 = 限流 30 天（拉电线怪人/夜莺与玫实测）；本 skill 产物只供私域/付费/测试。
2. **产物隔离**：输出目录与登记表标注 `sexy` 标记，与 `pipeline` 公开产物分离；可发公开队列只认 pipeline 标记。
3. **用途透明**：每次任务包写明用途（私域/付费/测试），不自作主张公开分发。

## 色情度档位（沿用 pipeline 的 L1-L5 体系，全强度）

| 档 | 保留 |
|---|---|
| **L5** | 吊袜带·露腰·深V·高衩剪影·含胸挺腰·暗示性姿态（pin-up 全强度） |
| **L4** | 去掉暗示性姿态 → elegant and poised |
| **L3** | 再删含胸挺腰（保留吊袜带/露腰/深V/高衩） |
| **L2** | 泳装 + 正常站姿（作为降级兜底，若还需更低走 pipeline） |

- 起点 L4，L4→L3→L2 阶梯降级重试（安全系统有随机性，非固定阈值，见 pipeline 13-erotic-levels.md 实测）
- **L2 最低可接受**；L2 都出不来 → 标记重做，不自动降 L1 交差
- **PHYSIQUE 严格体型条款照用**（腿/腰/胯照锚图纤细，防「腿太胖」）
- **儿童体型角色不适用**（可莉/七七/菲林类），保持原设服装——不可配置

## Prompt 骨架（L5 全强度，示例）

```text
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
PHYSIQUE (strict): the figure's body proportions follow the reference character's
actual slender build exactly — narrow hips, slim waist, long slim thighs and calves;
legs and hips are never thickened, widened or exaggerated; limbs and frame stay
natural, undistorted and in proportion.
```

- 降档替换（L4/L3）同 pipeline 13-erotic-levels.md 表
- 儿童体型角色不套用此档位（保持原设服装）

## 参考

- `references/16-hosiery.md` —— 丝袜类型选择（三层：幼态豁免 → 用户覆写 → 配色推断）

## 与 pipeline 的分工（铁律）

- pipeline = 公开（软色情 + 全遮挡 + G 轴 L0-L2）
- sexy = 非公开（色情度拉满 L3-L5）
- **两套 prompt/任务包/产物/登记 完全隔离**，防 pipeline 被 sexy 污染、sexy 产物误发公开
- 产物落登记时标 `sexy`，公开队列只认 `pipeline` 标记

## A–I 九轴（与 pipeline 共用，2026-08-24）

轴表唯一真源同为 `04_DouyinOps/00_治理与登记/05_素材维度/`，编译器同为 `02_通用资产/axes.py`，
用 `--line private` 调用。与公开线的差别只有闸门：

| | pipeline（公开） | **sexy（本 skill）** |
|---|---|---|
| H 轴 | 59/65 条 | **65 条全取**（含 4 条低机位仰拍 + 2 条胸腰臀主导） |
| G 轴 | ≤L2 | L3–L4 |
| I 轴质地 | 不含 `torn` | 全开 |
| 负向词 | 硬钉 `low angle, from below` | 不钉 |

**闸 5（R5 幼态角色锁 canonical、禁用诱惑/支配/服从权力轴）在两条线都生效，不可协商。**

**本 skill 唯一的护城河是权力轴构图，不是「更露」。** 公开线人人都能做平视对等的
20 多条；能做低机位支配、跪伏服从的只有非公开线。定价逻辑建在这上面。
详见 `character-skin-pipeline/references/17-axes.md`。

## 尺度上限：本线接受全裸（2026-08-24 用户裁决）

| | pipeline（公开） | **sexy（本 skill）** |
|---|---|---|
| 隐私部位 | **一律遮挡**，负向硬钉 `nude/topless/nipples/exposed genitalia` | **允许全裸**，不钉负向 |
| 判据来源 | 抖音公开发布红线 | 私域/付费，用户明确授权 |

实现上这一条已经在 `02_通用资产/axes.py` 里：裸体负向词只在 `--line public` 时拼进去，
`--line private` 不拼。配方里可显式加 `NUDE=1` 让编译器额外补正向措辞。

**边界仍然不可协商**：
1. 本 skill 产物**绝不进公开抖音队列**。判据是产物登记里的 `line` 字段，不是人的记性。
2. **R5 幼态角色在两条线都锁 canonical、禁用诱惑/支配/服从权力轴** —— 这条与尺度无关，
   是角色红线，`axes.py` 闸 5 在两条线都执行。
3. 全裸产物落 `private_only.json`，`catalog.json` 出 `public:false`。
