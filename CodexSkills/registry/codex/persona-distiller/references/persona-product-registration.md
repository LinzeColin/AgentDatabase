# 人物蒸馏产物唯一登记

“人物蒸馏 Skill”根目录下的七个身份目录保存通过发布门并打包后的完整目标人物 Skill ZIP。七个身份目录是产品登记标签，不替换构建时的七项身份菜单名称。

## 分类映射

| 登记目录 | 内部身份 ID | 登记模式 |
|---|---|---|
| `技术工程/` | `technical-engineer` | 单身份 |
| `企业领导/` | `entrepreneur-operator` | 单身份 |
| `金融投资/` | `investor-capital-allocator` | 单身份 |
| `软开设计/` | `developer-designer` | 单身份 |
| `思想教育/` | `thinker-educator` | 单身份 |
| `政治法律/` | `political-legal` | 单身份 |
| `多重身份/` | `multi-identity` | 多身份 |

## 强制规则

1. 同一人物只能有一个 canonical `registration.json`，不得在不同身份目录重复登记。
2. 单身份按 `identity_selection.primary` 自动归类；加权或多身份产物一律进入 `多重身份/`。
3. 每个 canonical 人物独立使用 `0.0.0.1` 至 `0.0.0.999` 的连续 `product_version`；完整发布 ZIP 保存为 `<分类>/<人物>/versions/<product_version>/*.zip`。
4. 产物版本只在成功登记后正式占用；失败不占号，跳号、复用、同号异哈希和超过 `0.0.0.999` 都会被拒绝。
5. 根级 `persona-registry-index.json` 是脚本生成的发现视图，不是第二份登记；不得手工制造平行记录。
6. 公共 GitHub 登记拒绝 `private`、`self` 产物，以及包含原始材料、Holdout、私密来源正文或疑似秘密的包。
7. 每次登记后必须运行 `python3 scripts/validate_persona_registry.py`，再通过仓库同步流程更新 `CodexSkills/README.md` 的人物产物清单。

登记命令：

```bash
python3 scripts/register_persona.py /absolute/path/to/target-persona-skill.zip
python3 scripts/validate_persona_registry.py
```
