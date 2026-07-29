# Teleiosis v0.0.0.3 安装与 GitHub main 兼容手册

本文件是当前版本唯一安装与发布说明。普通用户只使用任务包根目录 `START_HERE.py`。

## 一键只读检查

```bash
python3 START_HERE.py
```

## 一键安装

```bash
python3 START_HERE.py install
```

默认安装到 `${CODEX_HOME:-~/.codex}/skills/teleiosis`。可用 `--skills-root` 指定其他 Skills 根目录。安装器支持新装、v0.0.0.1/任一 v0.0.0.2 语义升级、v0.0.0.3 幂等重装、未知上游文件保留和精确回滚。备份与收据默认放在 `~/.teleiosis/`，不污染 Skills 目录。

## 一键发布到 AgentDatabase main

```bash
python3 START_HERE.py publish --yes --json
```

缺少 `--yes` 自动降级为 dry-run。真实发布会 fresh-clone 远端最新 `main`，做语义适配、完整测试、Catalog 更新、Scope 校验、commit、远端竞态复核、非 force push 和 readback。远端前进时丢弃临时 Candidate 并从最新 main 重试；不会使用陈旧 ahead/behind 工作树，不创建 branch/PR。

## 语义兼容边界

普通 README、`metadata/release.json` 或其他受管文件字节变化走 `adapt`，不使用固定 repo/file/overlay SHA 前置门。只有身份冲突、永久 Genesis 改变、未来高版本、路径类型/符号链接、安全规则、权限、测试失败或变更范围越界才阻断。

## 高级入口

- `install.py`：安装与安装回滚；
- `scripts/integrate_repo.py`：已有工作树 plan/apply/rollback；
- `scripts/publish_main.py`：移动 main 发布；
- `scripts/verify_package.py`：任务包冻结验收。

这些入口供调试和自动化使用，普通安装/发布无需手工组合。
