# Profile-to-Agent-Action Prompt

Use this prompt after reading the generated dynamic profile. It converts a profile change into a temporary, task-scoped behavior instruction.

```text
你正在读取一份“动态个人画像变化视图”，不是稳定记忆。

请只使用 status 为 current 或 emerging、且有 evidence 的条目。

对当前任务执行：
1. 找出与当前任务直接相关的画像变化；无关变化忽略。
2. 把变化翻译成一条临时 Agent 行为指令，明确适用范围和失效条件。
3. 保留用户当前明确指令；画像只能补充，不能覆盖当前指令。
4. 给出一个可验证的行为改变和一个失败/反证信号。
5. 不把本次临时指令写入稳定画像、Custom Instructions 或长期记忆。

输出格式：
- 相关变化：
- 临时行为指令：
- 适用范围：
- 失效条件：
- 验证方式：
- 不应改变的稳定规则：
```

Promotion rule: use the instruction in one real task first. Only repeated successful use with independent evidence may become a reusable Prompt Template, Workflow, or Skill.
