# Handoff — 人物蒸馏 Skill v0.0.0.145

## 当前架构

- `persona-distiller/`：人物研究、构建、评测、运行时打包和完整交付生成器。
- `../persona-distiller-group/`：唯一 canonical registry、十二个身份目录、团队卡、route 和 5–20 人专家团队路由。
- 最终发布 bundle 同时安装二者到 `~/.codex/skills/`；不得在 `~/.agents/skills/` 保留第二来源。

## 十二个 canonical 身份

1. 材料建工师
2. 软件开发师
3. 艺术设计师
4. 创业经营师
5. 投资资本师
6. 思想教育师
7. 政治法律师
8. 客户营销师
9. 建造采购师
10. 财务合规师
11. 医疗护理师
12. 农林牧渔师

名称与构建器 `registries/identity-families.json` 完全一致。同一人物只能登记在一个目录（多重身份已移除，每个人物只归属单一主身份）。

## 运行合同

已安装人物 Skill 直接接收任务：

```text
caller task → automatic internal identity/scenario route → minimum model load
→ plan → act with host tools → verify → deliver → optional unnumbered audit
```

不得要求运行用户选择身份、编号或权重。人物产品使用独立连续版本
`0.0.0.1..0.0.0.999`；人物 Skill 的单次运行不编号。

## 构建前同名消歧 gate

构建第一步由编排层检索 canonical registry 与权威公开资料，并整理候选 JSON。运行
`scripts/namesake_gate.py` 后才可调用 `scripts/init_target.py --namesake-gate`。
没有候选可继续；单候选即使证据较弱也自动绑定；多候选返回
`BLOCKED_NAMESAKE_SELECTION`，输出完整 A/B/C/D 候选卡片，禁止身份解析、workspace
写入和研究启动。gate 会把规范化姓名、候选证据与 `chosen_subject_uid` 写入目标
`meta.json`。

## 单一完整交付

每次成功发布只输出：

`<slug>-persona-distillation-delivery-v<0.0.0.N>.zip`

不输出 sidecar、第二个 ZIP 或散落文件。外层包含：

- 一个不可变人物运行时 ZIP；
- 外层安装器、manifest 与全成员 checksums；
- registration、team card、来源覆盖、评测、验证、provenance、review、handoff；
- 可选人读报告。

外层 ZIP SHA-256 由 canonical registry 保存；内层运行时 SHA-256 同时保存于外层和 registry。规范只限制文件与架构，不限制人物姓名、语言、职业或文本风格。

## 历史迁移

三个既有政治法律产品保留人物版本 `0.0.0.1`，并保留原运行时字节：

- Beth Wilkinson runtime SHA-256 `e0a30abd20dc8740bc35fd21840ff62d2492ffc64fb1b59ced4525a0e66e9802`
- Evan R. Chesler runtime SHA-256 `cc97e267284eec2799656d1e357caa2b676b43e44e64449e285c1a4056becefd`
- Theodore V. Wells Jr. runtime SHA-256 `462a320084a6ba73388a7133a8627f39cd13b2696adfbf3b8598c280e3a4197a`

v0.0.0.5 外层只规范交付，不消费新的人物版本。历史来源包没有的审计证据显式记为 `not-available-in-source-artifact`。

## 团队路由

调用 `persona-distiller-group` 时，内部推断身份与场景并选择 5–20 个角色。人物专家主要担任正向解决者；至少一个中立复审、一个中立裁判和一个中立反证角色必须隔离。无合格人物时返回 `insufficient_roster`，不得虚构。

## 验证

```bash
python3 scripts/self_check.py
python3 ../persona-distiller-group/scripts/validate_group.py
python3 ../persona-distiller-group/scripts/route_team.py \
  --task "分析重大诉讼的证据、证人和策略风险"
```

最终 bundle 还必须通过：确定性重建、所有成员校验、新目录双 Skill 安装、三份人物完整交付安装、凭据扫描、CodexSkills 索引同步和 GitHub `main` 回读。
