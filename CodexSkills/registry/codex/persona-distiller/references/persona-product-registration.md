# 人物产物唯一登记

v0.0.0.5 起，人物蒸馏构建器与 canonical registry 分离：

- 构建器：`persona-distiller/`
- 唯一登记与专家团队：`../persona-distiller-group/`

登记规则、七个身份目录、完整交付 schema、team card、route 和机器索引以
[`../../persona-distiller-group/README.md`](../../persona-distiller-group/README.md)
及其 [`CANONICAL-ROOT-ROUTE.md`](../../persona-distiller-group/CANONICAL-ROOT-ROUTE.md)
为准。

## 强制规则

1. 登记对象只能是一个 v0.0.0.5 完整交付 ZIP，不能是裸运行时 ZIP、目录、sidecar 或同版本多文件。
2. 同一人物只能有一个 canonical `registration.json`；不得跨身份重复。
3. 目录名必须是 `技术工程师`、`创业经营家`、`投资资本家`、`开发设计家`、`思想教育家`、`政治法律家`、`多重身份` 之一。
4. 每个版本目录只能保存一个完整交付 ZIP；外层和内层运行时 SHA-256 都要登记。
5. 人物产品版本按 canonical 人物独立、连续使用 `0.0.0.1..0.0.0.999`，成功登记才占号；人物运行不编号。
6. `team-card.json` 必须登记选入原因、最值得蒸馏特点、用户价值、应用场景、关键能力和硬边界。
7. 每次登记后重建 group 的 `team-index.json`、README 和 canonical route，再运行全目录验证。

```bash
python3 scripts/register_persona.py /absolute/path/to/full-delivery.zip
python3 ../persona-distiller-group/scripts/rebuild_team_views.py
python3 scripts/validate_persona_registry.py
```
