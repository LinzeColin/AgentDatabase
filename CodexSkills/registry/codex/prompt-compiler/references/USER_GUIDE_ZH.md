# 零技术用户说明

## 安装

1. 解压唯一 ZIP；
2. macOS/Linux 双击 `INSTALL_TO_CODEX.command`，Windows 运行 `INSTALL_TO_CODEX.ps1`；
3. 看到“安装完成”后重启 Codex；
4. 输入 `$prompt-compiler`。

基础安装不需要懂 Python。正式同场竞技需要可用模型、不同身份的独立终审、真实案例、官方 GEPA/Promptfoo 环境，以及 AutoResearch/MetaHarness 的可验证工作区与真实命令；Skill 会明确列出缺项，不会用本地模拟假装通过。

## 推荐输入

```text
$prompt-compiler
把下面内容优化为全维冠军版本：GEPA、AutoResearch、Meta-Harness、Promptfoo 同时作为同层竞品和下层执行器。原文不可覆盖；使用一个守恒总预算；最终测试必须密封；任何维度不第一都不得发布。

【原始内容】
……
```

## 看结果只看三处

1. **发布决策**：通过、退回或阻塞；
2. **冠军矩阵**：每个竞品 × 每个维度的状态；
3. **下一步**：若未通过，优先修复哪个维度、由哪个执行器承担。

## 常见结果

- `CHAMPION_PASS`：当前封印竞技场逐维第一；
- `CHAMPION_NOT_PROVEN`：证据不足或并列，继续补测试或优化；
- `CHAMPION_REJECTED`：竞品在某项明确更强；
- `PASS`：冠军门和全部现实发布门都通过。

## 不需要做

不需要手写 GEPA 或 Promptfoo 配置，也不需要人工比较每次结果。Agent 应代为运行、保存证据并给出中文结论；首次正式运行只需按阻塞报告提供真实工作区、命令、账户授权、预算和业务案例。
