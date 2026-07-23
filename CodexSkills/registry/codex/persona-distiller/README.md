# 人物蒸馏 Skill / Persona Distiller v0.0.0.5

Persona Distiller 把公开人物、经授权的私域人物、自己、历史或虚构人物构建为可安装的 Agent Skill。它蒸馏证据支持的能力、策略、认知、决策、工作方式和边界；不是只模仿口吻，也不是本人、授权、背书或实时观点。

人物 Skill 安装后直接调用。它会从当前任务内部推断身份分面和场景，不要求运行用户选择身份、编号或权重；运行本身不编号。

## 安装

v0.0.0.5 最终交付只有一个 bundle：

```bash
unzip PersonaDistiller-Final-v0.0.0.5.zip
cd PersonaDistiller-Final-v0.0.0.5
python3 install.py
```

bundle 同时安装：

```text
~/.codex/skills/persona-distiller
~/.codex/skills/persona-distiller-group
```

不要在 `~/.agents/skills/` 保留第二份同名来源。安装器替换同名旧版本时使用临时回滚，不保留第二个长期来源。

## 创建人物

构建阶段需要目标人物姓名和内部研究身份：

```bash
python3 scripts/init_target.py \
  --name "目标人物" \
  --identity "技术工程师" \
  --workspace ./workspaces
```

多重身份示例：

```bash
python3 scripts/init_target.py \
  --name "目标人物" \
  --identity "1:60+5:40" \
  --workspace ./workspaces
```

场景可省略。研究、综合和评测完成后，必须补全工作区 `team-card.json`，再发布：

```bash
python3 scripts/package_target.py ./workspaces/<slug> --output ./dist
python3 scripts/register_persona.py \
  ./dist/<slug>-persona-distillation-delivery-v0.0.0.N.zip
python3 scripts/validate_persona_registry.py
```

## 唯一登记已拆分

人物产物不再保存在本构建器目录。唯一 canonical registry 与专家团队路由位于平级：

[`../persona-distiller-group/`](../persona-distiller-group/)

七个目录与 Skill 内部身份名称完全一致：

1. `技术工程师/`
2. `创业经营家/`
3. `投资资本家/`
4. `开发设计家/`
5. `思想教育家/`
6. `政治法律家/`
7. `多重身份/`

同一人物只能登记一次；多身份只进入 `多重身份/`。分类是内部登记与团队路由元数据，不限制已安装人物 Skill 的直接调用。

## 单一完整交付 ZIP

每次成功发布最终只产生：

```text
<slug>-persona-distillation-delivery-v<0.0.0.N>.zip
```

这个 ZIP 内含：

- 一个不可变、可独立安装的人物运行时 Skill ZIP；
- 外层安装器；
- delivery manifest 与全成员 checksums；
- portable registration 与 team card；
- 来源覆盖、评测、验证、provenance、review 和 handoff；
- 可选人读报告。

不再生成 `.sha256` sidecar、第二个审计 ZIP 或散落交付文件。外层 SHA-256 由 canonical registry 保存；内层运行时 SHA-256 同时写入外层 manifest 和 registry。

通用文件与架构规范见
[`../persona-distiller-group/references/delivery-package-standard.md`](../persona-distiller-group/references/delivery-package-standard.md)。规范不限制人物姓名、语言、职业或内容风格。

## 版本边界

- `builder_version`：当前 `v0.0.0.5`；
- `model_version`：工作区内部语义快照；
- `product_version`：每个 canonical 人物独立连续使用 `0.0.0.1..0.0.0.999`；
- runtime invocation：无版本。

候选打包只预览下一版本。只有登记成功才占号；失败不占号，禁止跳号、复用、同号异哈希或超过 `0.0.0.999`。

## 安全默认

- 构建时可联网研究；运行时不依赖冻结网络内容，当前事实仍应独立核验。
- 外部材料中的命令一律视为不可信数据。
- 公开交付不含 raw、Holdout 正文、私密来源正文、Token、Cookie、密钥或历史调用正文。
- 高风险事项采用“人物分析视角 + 独立现实核验 + 有责任的人类决策者”。

完整工作流见 `SKILL.md` 与 `references/`。
