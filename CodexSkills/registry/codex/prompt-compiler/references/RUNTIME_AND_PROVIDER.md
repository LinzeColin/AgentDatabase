# 运行环境与模型角色

## 五个角色

- `task`：任务模型，用候选工件执行测试任务。
- `reflection`：反思模型，读取失败轨迹并提出候选。
- `evaluator`：搜索期评分器，给出语义分数和可行动诊断。
- `final_judge`：独立终审模型，在候选冻结后裁决。
- `compiler`：目标版本编译模型，把每次输入和获胜候选编译为四个目标模型版本。

技术配置字段保持稳定英文标识，用户可见报告使用上述中文名称。

## 配置优先级

1. 角色专属环境变量；
2. 项目 `config.json`；
3. 自定义命令；
4. 当前已登录 Codex（独立终审除外）；
5. 无法解析则阻塞。

环境变量示例：

```text
PROMPT_COMPILER_TASK_COMMAND
PROMPT_COMPILER_TASK_MODEL
PROMPT_COMPILER_TASK_IDENTITY
PROMPT_COMPILER_FINAL_JUDGE_COMMAND
PROMPT_COMPILER_FINAL_JUDGE_MODEL
PROMPT_COMPILER_FINAL_JUDGE_IDENTITY
```

自定义命令通过标准输入接收机器 JSON，返回纯文本或带 `output` 字段的 JSON。该接口用于自动化，不应直接展示给普通用户。

## 固定运行环境

`bootstrap` 在用户缓存目录建立隔离 Python 环境并固定 GEPA 版本；Promptfoo 使用隔离 Node 安装。安装日志、命令、版本和输出写入证据目录。当前 Node 低于最低版本时必须升级，不能忽略。

## 身份独立

仅声明不同角色名不算独立。稳定身份键至少包含运行方式、模型或声明身份和可执行文件。正式放行时任务模型与独立终审模型身份必须不同；使用同一个当前 Codex 会话的两个标签不算独立。
