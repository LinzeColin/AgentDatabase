# HarnessUI

给 DSH / Kimi Code 做角色皮肤的素材库与生产线。原神 + 崩铁 + 绝区零 + 鸣潮全量女角色。

**定位:个人自用、非商业、不分发。** 角色版权归米哈游,本目录下所有产物只在本机 DSH 里用。

## 目录约定

```
HarnessUI/
├── README.md                      本文件：目录约定 + 版本规则 + 流水线
├── research/
│   ├── roster-genshin.json        原神女角色全量清单（79）
│   ├── roster-hsr.json            崩铁女角色全量清单（56）
│   ├── roster-zzz.json            绝区零女角色全量清单（45）
│   ├── roster-wuwa.json           鸣潮女角色全量清单（43）
│   ├── names_zh.json              简体中文名映射（198）
│   ├── douyin-analysis.md         抖音三博主蒸馏与角色清单
│   ├── generation-stack.md        生成链路选型（为什么必须用 LoRA）
│   └── material-sources.md        素材来源调研（哪些平台真的有用）
├── characters/<id>/
│   ├── character.json             该角色的台账：素材、LoRA、版本历史
│   ├── refs/                      原始输入素材（官方立绘等），带来源标注
│   └── renders/v1/ v2/ …          各版本产物，只增不改
├── skins/<id>/                    装配好的 DSH 皮肤包
└── tools/                         生产脚本
```

## 版本规则（防止乱掉的核心）

**每一次出图批次都是一条独立的素材登记，不是同一件东西的新版本。**

这一点是 2026-08-19 改的。原来的 schema 假设「一个角色-变体只有一个产物，versions 是历史，只有最新那条算数」——
**这个假设是错的**。同一个甘雨跑 v1.0 和 v1.1，出来的不是"更好的同一张"，而是
**动作、服装解读、场景都不同的另一张**，两张都能当皮肤用，都应该能在画廊里被挑到。

所以台账按 `<library>/<游戏>/<角色>/ledger.json` 存，`batch` 是一等维度：

```jsonc
{
  "character": "ganyu", "game": "genshin", "schema": 2,
  "batch_count": 2,
  "batches": [
    { "batch": "v1.0", "variant": "default",
      "engine": "minimax-design/niji7", "pack_version": "1.0.0",
      "generated": "2026-08-19",
      "verdict": "reject",                       // 批次级
      "machine_fails": ["G1 暗版亮度 0.23"],
      "human_review": null,                      // C1/C2/C6/D/E/F 待人眼填
      "images": [
        { "side": "light", "file": "…", "verdict": "accept",
          "metrics": { "brightness": 0.80, "right_edge": 4.4, "spill": 0.41 } },
        { "side": "dark",  "file": "…", "verdict": "reject",
          "fails": ["G1 暗版亮度 0.23"] }
      ] },
    { "batch": "v1.1", "verdict": "accept", … }
  ]
}
```

**可挑选皮肤总数 = 角色 × 变体 × 批次 × 2（明暗）。** 每多跑一轮 prompt 变体，
整个库就多一整层可选项，而不是覆盖掉上一层。

规则:

1. **批次永不覆盖。** 重跑就是新 `batch`，旧的留着。
2. **`verdict` 分两级**：批次级 + 单图级。批次可以整体 accept 而其中某张 reject 单独重出。
3. **`machine_fails` 由 `tools/ledger.py` 自动判**（B/C3/G1 这些有阈值的）；
   `human_review` 留给人眼条款（C1/C2 收边、C6 场景黑名单、D 洁净度、E 解剖、F 角色一致）。
4. **每个批次必须记 `engine` / `pack_version` / `generated`。** 少一样就复现不出来。

---

## 旧版本规则（schema 1，已废弃）

**一个角色的每一次出图都是一个新版本,旧版本永不覆盖、永不删除。**

`characters/<id>/character.json` 是该角色的唯一台账:

```jsonc
{
  "id": "raiden-shogun",
  "name_en": "Raiden Shogun",
  "name_zh": "雷电将军",
  "game": "genshin",
  "status": "generated",          // pending → refs-collected → generated → shipped
  "refs": [                       // 原始输入，每条必须能追回来源
    { "file": "refs/official-splash.webp", "kind": "official-art",
      "source": "fandom", "url": "https://…", "fetched": "2026-08-19",
      "note": "仅作参考与校验，不进产物" }
  ],
  "lora": {                       // 没有就是 null，代表走降级路线
    "name": "raiden-illustrious-v2", "source": "civitai",
    "url": "https://…", "sha256": "…", "trigger": "raidenshogun",
    "license": "…"
  },
  "current_version": "v2",        // 指向当前采用的版本
  "versions": [
    { "v": "v1", "engine": "mmx/image-01", "lora": null, "seed": 20260819,
      "prompt_sha": "3f2a…", "at": "2026-08-19", "verdict": "reject",
      "why": "角色不可辨认，只是通用紫发少女" },
    { "v": "v2", "engine": "comfy/wai-illustrious", "lora": "raiden-illustrious-v2",
      "seed": 771, "prompt_sha": "9b1c…", "at": "2026-08-20", "verdict": "accept" }
  ]
}
```

规则:

1. **`renders/vN/` 只增不改。** 重摇就是 `v(N+1)`,不覆盖旧的。
2. **每个版本必须记 `engine` / `lora` / `seed` / `prompt_sha`。** 少一样就复现不出来。
3. **`verdict` 必须填。** `accept` / `reject` / `hold`,并写 `why`。被否的版本留着,是下次调参的证据。
4. **`refs` 里每条都要能追回来源。** 没有 `url` + `fetched` 的素材不许进 `refs/`。
5. **`current_version` 是唯一的"当前采用"指针。** 装配皮肤只读它。

## 质量门（未过不进 skins/）

一个版本要标 `accept`,必须同时满足:

- **可辨认**:与官方立绘并排,能认出是同一个角色
- **构图合规**:人物及头发收在左 35% 以内,右侧三分之二为低细节留白
- **上机可读**:套上 DSH 版面模拟图后,对话区与输入框上的文字清晰
- **零动画**:皮肤模板本身不含任何 CSS 动画(见下)

## 流水线

```
名单 → LoRA 覆盖率核对 → 下模型 → 出图(ComfyUI) → 质量门 → 装配皮肤包 → 版面模拟验收
```

装配脚本在 `tools/`,输入一个 `character.json` + `renders/<current_version>/`,
输出一个可安装的 DSH 皮肤包。

## 两条焊死在模板里的硬约束

均来自 2026-08-19 在本机的实测(详见 `~/.dsh/AGENTS.md` §8.7 §8.8):

1. **生成的皮肤零 CSS 动画。** 一条 `infinite` 动画就让合成器永不进 idle,
   实测在 4K 外接屏最大化时空转烧 **111% CPU**(无皮肤时 0.9%)。只用静态美术。
2. **`[data-slot="sidebar.settings"]` 强制 `position: sticky; bottom: 0`。**
   否则别的插件的侧栏页脚卡片会把设置按钮挤出视口且滚不到。

## 不进 git 的东西

产物体积大且是二进制,不入库:

```
characters/*/refs/
characters/*/renders/
skins/
tools/models/
```

只有 `character.json`、清单、调研文档和脚本入库——**台账入库,素材留本地。**
