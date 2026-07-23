# 人物蒸馏 Skill v0.0.0.5

这是唯一发行 ZIP 的解压目录，完整包含：

- `persona-distiller/`：人物蒸馏构建器；
- `persona-distiller-group/`：7 类 canonical 人物登记、完整交付备份与专家团队路由；
- 原子双 Skill 安装器、发行清单和全文件 SHA-256。

默认只安装到 `~/.codex/skills`，不会同时安装到 `~/.agents/skills`。

```bash
python3 install.py --force --remove-conflicts
```

安装器先验证 ZIP 内全部文件，再在临时目录验证两个 Skill；全部通过后才替换旧安装，并删除 `~/.agents/skills` 下同名重复来源。失败时恢复原安装。

人物产物 `0.0.0.1..0.0.0.999` 是每个 canonical 人物各自的连续产品版本；人物 Skill 的调用不编号，也不要求用户选择身份。
