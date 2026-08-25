# 安装说明

## Codex

在本目录运行：

```bash
python3 scripts/install.py --target codex
```

默认安装到：

```text
~/.codex/skills/video-prompt-compiler
```

## Claude Code

```bash
python3 scripts/install.py --target claude
```

默认安装到：

```text
~/.claude/skills/video-prompt-compiler
```

## 同时安装

```bash
python3 scripts/install.py --target both
```

## 自定义目录

```bash
python3 scripts/install.py --target-path /absolute/path/to/skills
```

## 预览安装内容

```bash
python3 scripts/install.py --target codex --dry-run
```

## 已存在旧版本

默认不覆盖。确认需要替换时：

```bash
python3 scripts/install.py --target codex --force
```

## MiniMax Design

本包不是 MiniMax Design 内置 Marketplace Skill。默认方式是：

1. 在 Codex、Claude Code、ChatGPT 或 Claude 中调用本 Skill；
2. 把其输出的 `MINIMAX_COPY_PROMPT` 直接粘贴到 MiniMax Design；
3. MiniMax Design 负责素材节点、模型路由和生成。

若未来 MiniMax Design 支持导入自定义 Skill，可使用 `bridges/MINIMAX_DESIGN_BRIDGE.md` 中的简化合同，但在未验证前不声称可以直接安装。
