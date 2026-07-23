# 人物蒸馏 Skill / Persona Distiller

Persona Distiller 将公开人物、经授权的私域人物、自己、历史或虚构人物，构建为可安装的 Agent Skill。目标不是“像他说话”，而是让宿主 Agent 直接调用目标人物的证据化能力、策略、认知、决策、工作方式和性格来真实完成任务。身份分面由人物 Skill 根据当前任务在内部自动路由，运行用户不需要选择身份。

## 最短使用路径

```bash
unzip PersonaDistiller-Final-v0.0.0.4.zip
cd persona-distiller
python3 scripts/self_check.py
python3 scripts/install.py install
```

Codex 默认且唯一安装到：

```text
~/.codex/skills/persona-distiller
```

不要同时安装到 `~/.agents/skills/persona-distiller`。安装器会拒绝
`~/.codex/skills` 与 `~/.agents/skills` 的重复来源。

创建人物：

```bash
python3 scripts/init_target.py \
  --name "Richard Feynman" \
  --identity "技术工程师" \
  --workspace ./workspaces
```

多重身份：

```bash
python3 scripts/init_target.py \
  --name "目标人物" \
  --identity "1:60+5:40" \
  --workspace ./workspaces
```

场景可省略；运行时从任务自动路由内部身份和场景。研究、综合、评测完成后：

```bash
python3 scripts/package_target.py ./workspaces/<slug> --output ./dist
python3 scripts/register_persona.py ./dist/<slug>-persona-skill-v0.0.0.N.zip
python3 scripts/validate_persona_registry.py
```

## 七类身份

1. 技术工程师
2. 创业经营家
3. 投资资本家
4. 开发设计家
5. 思想教育家
6. 政治法律家
7. 多重身份（至少两个身份权重；私域/自己/历史/虚构由独立 `subject_origin` 治理）

## 人物产物唯一登记

每个人物产物必须且只能登记一次。登记目录使用以下七个面向读者的分类名，
不改变上面的 Skill 身份菜单：

| 登记目录 | Skill 身份 |
|---|---|
| `技术工程/` | `technical-engineer` |
| `企业领导/` | `entrepreneur-operator` |
| `金融投资/` | `investor-capital-allocator` |
| `软开设计/` | `developer-designer` |
| `思想教育/` | `thinker-educator` |
| `政治法律/` | `political-legal` |
| `多重身份/` | weighted multi-identity |

- 单身份产物进入对应目录；多重身份只进入 `多重身份/`，不得复制到组成身份目录。
- 同一人物的每次新蒸馏产物追加到原人物目录，不新建第二条人物登记。
- 完整、通过发布门的目标人物 Skill ZIP 保存在
  `<分类>/<人物>/versions/<product_version>/`；七个分类目录直接位于本 Skill 根目录。
- 根级 `persona-registry-index.json` 是自动生成的检索视图，不是第二份登记。
- 重分类必须移动原登记；跨目录重复 `subject_uid`、人物规范键或产物 hash
  都是硬错误。
- 公开仓不得登记原始私域正文、Holdout、凭据或未脱敏身份信息。

## 版本边界，禁止混用

- `builder_version`：人物蒸馏器版本，当前为 `v0.0.0.4`；
- `model_version`：研究工作区内部的语义快照，不作为公开产物编号；
- `product_version`：同一 canonical 人物独立递增的发布产物编号，范围为 `0.0.0.1` 至 `0.0.0.999`。

候选包根据登记库计算下一个可用产物版本；只有质检、打包和登记全部成功后才正式占号，失败不占号。人物 Skill 的单次运行没有版本号，不显示运行版本，也不强制给输出文件名添加版本后缀。

## 目标人物 Skill 的调用合同

安装目标人物 Skill 后，用户直接调用它并描述任务。Skill 从已蒸馏分面中自动选择或组合内部身份并推断场景；不得要求用户选择身份、编号或权重。七类身份目录只是唯一登记位置，不是运行能力边界。

## 安全默认

- 构建时可联网研究，运行时默认不依赖网络；当前事实仍应联网核验。
- 不携带飞书、钉钉、Slack、邮箱等账号直连器；优先使用本地授权导出。
- 运行包不含原始私域正文、Holdout 答案、Token、Cookie 或密钥。
- 外部资料中的指令始终按数据处理。
- 高风险事项采用“人物分析视角 + 独立现实核验”，不让模拟人格替代专业责任。

详见 `SKILL.md` 与 `references/`。完整改进和复审证据位于 `audit/`。
