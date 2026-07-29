# Teleiosis v0.0.0.3 安装、校验与回滚

本文件是 Skill 内的高级安装说明。普通用户优先使用最终任务包根目录的 `START_HERE.py`；不要从历史谱系文档复制旧命令。

## 1. 校验当前 Skill

```bash
python3 scripts/wbi.py verify-self --strict
python3 scripts/wbi.py release-smoke
python3 scripts/wbi.py self-test --timeout 600
```

基础 Genesis 的永久锚点为：

```text
14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086
```

安装可从包内 lock 自动发现锚点；需要外部信任锚时，仍可显式传入 `--expected-genesis-hash` 和 `--expected-effective-genesis-hash`。

## 2. 安装独立 Skill ZIP

最终任务包内的 canonical Skill archive：

```text
dist/Teleiosis-v0.0.0.3-skill.zip
```

从 Skill 源目录执行高级安装：

```bash
python3 scripts/wbi.py install /absolute/path/Teleiosis-v0.0.0.3-skill.zip \
  --skills-root /absolute/path/to/skills \
  --profile optimizer \
  --verification-level release \
  --result-file /absolute/path/outside/skills/install-result.json
```

需要额外绑定外部 archive 摘要时，加：

```text
--expected-archive-sha256 <external-sha256>
```

不要从待校验 ZIP 内部读取“预期摘要”再自我证明。

## 3. 状态、恢复与回滚

```bash
python3 scripts/wbi.py install-status \
  --skills-root /absolute/path/to/skills \
  --verify-installed --profile optimizer

python3 scripts/wbi.py recover-install \
  --skills-root /absolute/path/to/skills \
  --profile optimizer
```

安装器返回的收据包含 predecessor backup 与精确 rollback 参数。不要手工猜测备份路径，也不要删除尚未完成 readback 的 predecessor。

## 4. 兼容性边界

- v0.0.0.1 和任一 v0.0.0.2 采用语义升级；
- v0.0.0.3 重复安装幂等；
- 未知 Owner 文件默认保留；
- README、release metadata 或普通受管文件漂移不因固定 SHA 阻断；
- 永久 Genesis 改变、身份冲突、未来高版本、路径类型冲突、符号链接、安全规则或测试失败必须阻断；
- 安装备份和收据必须位于 Skill 目录外。
