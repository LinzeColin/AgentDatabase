# Adaptive Target Routing

## 为什么新增

v0.0.0.2 已能验证 Teleiosis 自身与普通 Skill，但仍容易把所有目标套进同一证据形状。Luban 的有效之处不是“压缩图片”，而是按输入画像选择策略；Teleiosis 也应按目标画像选择 Gate、证据和交付物。

## 目标画像

| target_class | 典型标记 | 重点证据 | 额外风险 |
|---|---|---|---|
| `agent-skill` | `SKILL.md` | activation kernel、schema、tests、安装 | 伪独立复审、prompt 膨胀 |
| `self-evolving-agent-skill` | `SKILL.md` + Genesis | self-evolution seal、外部 anchor、回滚 | 自改自验、holdout 污染 |
| `runtime-service` | Dockerfile/Makefile/configs/deploy/web/go.mod | deploy、status、rollback、protocol gateway | 服务状态不等于业务验收 |
| `library-or-tooling` | pyproject/go.mod/gradle | API、兼容、性能、版本 | 示例替代真实使用 |
| `web-product` | package.json/web | UI flow、状态、真实用户结果 | HTTP 200 伪通过 |
| `unknown-or-documentation` | 标记不足 | 先补身份、范围、产物 | 错把文档当产品 |

## CLI

```bash
python3 scripts/wbi.py market-profile /absolute/path/to/target --output profile.json
```

输出不修改目标，只生成 adoption lanes、risk flags 和 next evidence。