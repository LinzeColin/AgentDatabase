# 任务包与 prompt 版本治理

## 结构

```
taskpack/
  manifest.json              # 全部任务 + 每张的 prompt 原文
  anchors/<game>/<char>/<variant>.jpg
  docs/SPEC.md  docs/ACCEPTANCE.md
  output/<game>/<char>/<variant>/{light,dark}.png
```

`manifest.json` 每个任务：
```json
{"id":"genshin/amber/default", "game":"genshin", "game_zh":"原神",
 "character":"amber", "character_name":"Amber", "variant":"default",
 "anchor":"anchors/genshin/amber/default.jpg",
 "outputs":{"light":{"file":"output/…/light.png","prompt":"…"},
            "dark":{"file":"output/…/dark.png","prompt":"…"}},
 "negative_prompt":"…"}
```

**`negative_prompt` 是个陷阱**——见下。

## HarnessUI 的版本史（每次为什么改）

| 版本 | 改了什么 | 为什么 |
|---|---|---|
| v1.0–1.3 | 迭代锚图与构图约束 | 早期试错 |
| v1.4.0 | 换无损高清锚图 | 发现 CDN 返回的是有损转码 |
| **v1.5.0** | 补入**禁 Q 版**排除项 | 用户截图否决过，而 594 条 prompt 里一个字都没有 |
| **v1.6.0** | 丝袜/露肤从 `where the design allows` 改为**强制**，加优先级裁决 | 逃生口让原设长裤的角色直接跳过；且与同段「严格照参考图」打架 |
| **v1.7.0** | `negative_prompt` **全文折进 prompt 正文**；补 9 个绝区零角色 | gpt-image-2 没有负面提示词参数，那个字段发不出去；花名册存的是 /Lore 子页 |

**每次改版都要更新 `manifest.version` 和 `changelog`，写清「为什么」而不是「改了什么」。**

## Prompt 的三条硬规则

### 1. 负面词必须写进正文

`gpt-image-2` **没有** negative prompt 参数。任务包里的 `negative_prompt` 字段
是给别的宿主（如 MiniMax Design）准备的，走 OpenAI API 时**发不出去**。

做法：把该字段全文追加到 prompt 尾部：
```
EXCLUDE — none of the following may appear: chibi, super-deformed or child-like
proportions, oversized head, doll or figurine look, <原 negative_prompt 全文>.
```
**注意**：原 negative_prompt 里可能**没有**用户后来提的要求（HarnessUI 的原字段里
就没有 chibi），要单独补。

### 2. 冲突要显式裁决

「严格照参考图」+「必须穿丝袜」= 模型随机取中。写清楚：

```
MANDATORY WARDROBE — applies to every character without exception: sheer
stockings, tights or thighhighs on fully visible legs. Where the canonical
design has trousers, greaves or armoured legs, restyle the legwear into sheer
stockings or thighhighs while keeping that design's own colours, patterns and
trim. The silhouette is open and skin-revealing.
PRECEDENCE: character IDENTITY (face, hair colour and style, eye colour,
signature accessories, colour palette) matches the reference exactly;
WARDROBE STYLING follows this paragraph and overrides the reference wherever
the two conflict.
```

**验证要用最难的案例**——原设全长裤的角色（如 Aloy），不要用本来就穿丝袜的。

### 3. 构图约束要能被机器复核

HarnessUI 的构图段（配合 `runner.py` 的 `spill` / `right_edge` 判据）：
```
COMPOSITION (strict): the character stands full-body in the LEFT THIRD of a
16:9 frame; the figure and ALL flowing hair, skirt, weapon and effects stay
inside the left 35% of the image. The RIGHT 65% is deliberately empty: an open
natural vista … rendered low-detail, low-contrast, atmospheric and out of focus,
with nothing readable in it. Nothing occupies the bottom centre of the frame.
```

**为什么右侧要刻意留白**：后面装进应用时，正文区要压一层可读性遮罩。
留白的那一侧正好承担它，人物那一段一点不遮。**构图是为消费场景设计的，不是为了好看。**

## 昼夜成对

每个变体出 light + dark 两张。dark 版**不是**把 light 调暗——
它是独立的一张夜景，prompt 里的 LIGHT 段不同，验收阈值也不同（见 06）。
