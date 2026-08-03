# 安装、升级与回滚

## 一键体检和安装

```bash
python3 START_HERE.py doctor
python3 START_HERE.py install
```

要求 Python 3.9 或更高版本，不需要 pip、Node、GPU、模型 API 或云服务。

## 安装位置

- 用户级：`~/.codex/skills/teleiosis/`
- 设置 `CODEX_HOME`：`$CODEX_HOME/skills/teleiosis/`
- 项目级：当前目录 `.agents/skills/teleiosis/`

```bash
python3 START_HERE.py install --project
```

## 升级行为

安装器支持 v0.0.0.1—v0.0.0.4 升级。它会：

1. 先验证源包、Genesis、Manifest、Taskpack、Skill Audit、复审和 8192 条回归语料；
2. 识别目标版本与未知文件；
3. 未知普通文件在无碰撞时保留；未知可执行碰撞、Genesis 异常和更高版本一律阻断；
4. 在同盘 staging 构建并验证；
5. 原子交换，保留旧目录备份；
6. 再次验证新安装；失败自动恢复。

## 回滚

安装成功会返回 receipt 路径：

```bash
python3 scripts/teleiosis.py rollback-install --receipt /path/to/install-receipt.json
```

全新安装没有前一版本，因此没有可回滚备份。升级安装具备精确回滚。

## 不写入目标仓的检查

```bash
python3 START_HERE.py install --dry-run
```

Dry-run 只输出计划，不写目标 Skill。目标 Registry 的真实 `main` 必须先执行 Stage 0 Semantic Reconcile，普通漂移用 adapt；身份、Genesis、高版本和未知可执行冲突会停止。
