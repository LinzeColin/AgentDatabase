# 运行环境、Provider 与安装

## 角色

| 角色 | 职责 | 正式发布要求 |
|---|---|---|
| task | 用候选执行测试任务 | 记录稳定身份 |
| reflection | 读取失败轨迹并提出候选 | 可与 task 相同，但应可追踪 |
| evaluator | 搜索期评分与反馈 | 不拥有最终发布权 |
| final_judge | 候选冻结后独立终审 | 必须与 task 不同身份 |
| compiler | 生成 ChatGPT、Codex、Claude、Gemini 四目标版本 | 记录模型和父版本 |

稳定身份键由运行方式、声明身份、模型和可执行文件组成。

## 运行环境

- Python：3.10 ≤ 版本 < 3.15；
- GEPA：固定 0.1.4；
- Promptfoo：固定 0.121.20；
- Node.js：最低 22.22.0，推荐 24；
- 控制面：Python 标准库；
- 外部依赖：安装在用户缓存的隔离环境，不污染目标仓。

## 零技术安装

解压任务包后：

- macOS/Linux 双击 `INSTALL_TO_CODEX.command`；
- Windows 右键使用 PowerShell 运行 `INSTALL_TO_CODEX.ps1`；
- 或执行 `python3 START_HERE.py`。

安装器会先校验清单和离线自检，再事务式移动旧版到 `.backups/`，安装新版本，复验失败则自动恢复旧版。重复安装是幂等升级，不覆盖用户项目数据。

## Provider 优先级

1. 用户或项目显式角色配置；
2. 角色环境变量；
3. 自定义 JSON 命令；
4. 当前已登录 Codex；
5. 无法解析则阻塞。

独立终审不自动继承任务模型。

## 外部 Bridge

Bridge 从标准输入读取种子、训练、验证、目标、要求和冻结预算，标准输出返回候选数组。主控不会发送最终测试。模板：`scripts/external_engine_adapter.py`。

## 降级原则

- 无网络：基础 Skill、历史、数据准备、自检可用；官方依赖安装标记阻塞；
- 无独立终审：可研究候选，不发布；
- 无 Promptfoo：不把内部断言冒充 Promptfoo；
- 无官方 GEPA：该路径直接 `BLOCKED`，不运行兼容执行器；
- 无真实成本 Token：成本维度明确使用字符代理，不伪造金额。

## Promptfoo Optimize 角色合同

被优化的目标 Provider 由项目 task 角色决定；候选建议 Provider 由 Promptfoo 官方 `suggestionsProvider` 决定。两者是独立逻辑角色，报告分别记录身份来源；项目可开启强制 Provider 身份不同门。
