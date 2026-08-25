# 人物蒸馏完整交付 ZIP 规范 v0.0.0.5

## 目标

每次成功发布最终只交付一个 ZIP。ZIP 内含运行时 Skill 和全部交付、验证、登记与交接信息；不得要求接收方同时保存 sidecar、第二个 ZIP 或散落文件。规范只限制文件与架构，不限制人物姓名、语言、职业或内容风格。

## 固定外层

```text
<slug>-persona-distillation-delivery-v<product_version>/
├── README.md
├── handoff.md
├── install.py
├── install.sh
├── install.ps1
├── delivery-manifest.json
├── delivery-checksums.sha256
├── registration.json
├── team-card.json
├── runtime/
│   └── <slug>-persona-skill-v<product_version>.zip
├── audit/
│   ├── verification.json
│   ├── provenance.json
│   ├── source-coverage.json
│   ├── evaluation-summary.json
│   └── review-record.json
└── reports/                         # 可选；人读 PDF/DOCX/Markdown 等
```

只有一个顶层目录。`runtime/` 内只能有一个 ZIP。版本目录和公开 registry 中也只能保存这个外层完整交付 ZIP。

## 内容硬门

- `delivery-manifest.json` 必须声明 subject、identity、人物产品版本、模型快照、运行时路径/哈希/大小、兼容性、隐私、证据状态和全部 payload 文件。
- `delivery-checksums.sha256` 必须覆盖除自身以外的每个文件，包含 `delivery-manifest.json`，且不能遗漏、重复或越界。
- 外层 ZIP 自身 SHA-256 由 `registration.json` 的 registry 记录保存，避免自引用哈希悖论。
- 内层运行时必须可独立安装并包含 `SKILL.md`、`meta.json`、`PACKAGE_MANIFEST.json`、`checksums.sha256`。
- `install.py` 先校验外层，再校验并安装内层；默认安装到 `~/.codex/skills/<slug>`。
- 运行时不包含 raw、Holdout 正文、私密来源正文、凭据、缓存、symlink 或历史调用内容。
- 人物 Skill 运行不编号；`0.0.0.N` 只标识成功登记的产品版本。

## 审计文件语义

- `verification.json`：结构、哈希、安装、路由、隐私和测试状态。
- `provenance.json`：构建器、输入类型、权利/授权摘要、研究截止与生成方式；不泄露私密路径。
- `source-coverage.json`：定义的来源宇宙、时间/角色/观点覆盖、偏差控制、剩余缺口和饱和声明。
- `evaluation-summary.json`：测试套件、baseline、候选分数、关键失败、盲评/独立性和 frozen output 哈希。
- `review-record.json`：研究、构建、生成、复审、裁判、反证的角色隔离与结论。

新产物必须给出真实结果。历史迁移若原包没有某项证据，仍须保留对应文件并写：

```json
{"status": "not-available-in-source-artifact", "claims": []}
```

这表示交付结构完整，不表示缺失证据被补造。

## team card

必须包含非空数组：

- `selection_reasons`
- `distillation_traits`
- `user_value`
- `application_scenarios`
- `key_capabilities`

还必须包含 `hard_boundaries`、`readiness`、identity、研究截止和版本引用。这里允许任何人物姓名；schema 不枚举具体人物。

## 完整性与兼容

- 文件路径使用 UTF-8 和 POSIX `/`，拒绝绝对路径、`..`、反斜杠、NUL、重复成员和 symlink。
- 文件名不得依赖人物姓名中的空格、大小写或非 ASCII；路径使用稳定 slug，展示名保留原文。
- 运行时 Skill 名称遵循小写 ASCII kebab-case，最长 64 字符。
- ZIP 使用确定性顺序、固定时间戳和固定权限，未变输入应生成同一哈希。
- 最低兼容为 Python 3.10+、Codex Skills；其他 host 只能在已实际验证时声明。

## 发布顺序

严格质量门 → 构建内层运行时 → 构建单一外层交付 → 全成员校验 → 新目录安装演练 → registry 唯一性/连续版本校验 → 登记外层哈希与内层哈希 → 重建团队索引/README/route → Git 同步。
