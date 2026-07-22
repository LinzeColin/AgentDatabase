---
name: goal-to-delivery-sop
description: >-
  Use when the user proposes a complex goal, vague product or system idea,
  software design request, automation system, data analysis task, business
  process redesign, finance/cost/collection/payroll/tax/budget/ROI feature, or
  explicitly asks to clarify requirements before implementation. Enforce a
  requirements-first goal-to-delivery workflow: interview, define scope, PRD,
  technical plan, confirmed implementation plan, incremental implementation,
  tests, review, documentation, risk notes, rollback advice, diff summary, and
  next steps.
---

# Goal to Delivery SOP

Use this skill to convert ambiguous or complex goals into confirmed requirements and controlled delivery. Do not write code, edit files, or perform irreversible implementation before requirements and plan are confirmed, unless the user explicitly asks for a narrow, already-defined action.

## Core Rules

- Understand context before acting.
- For complex tasks, plan first. Do not implement before confirmation.
- Do not assume business rules. Mark missing rules as `待确认假设`.
- For money, collections, cost, payroll, tax, budget, ROI, or financial metrics, state formulas, calculation scope, data sources, and assumptions.
- After each modification, state what changed, why, affected files, validation, and risk.
- Make each implementation unit independently testable and rollbackable.
- Run available tests. If tests cannot run, state why and provide manual commands.
- Deliver in this fixed order after implementation: `实现 → 测试 → 审查 → 文档 → 风险说明 → 回滚建议 → diff 摘要 → 下一步建议`.

## Standard Workflow

### 1. Requirements Interview

Use interactive choice-based interviewing by default. Start with a small batch of high-leverage choices, then refine.

Interaction priority:

1. If an interactive user-input tool is available, use it for choice questions. This means UI-backed selectable question cards like the government-file-interpretation-system onboarding flow, not plain text options in chat. Do not replace the first choice round with plain chat text.
2. Keep each interactive round to 1-3 questions so the user can answer by selecting options.
3. If no interactive user-input tool is available and the user did not explicitly demand an interactive UI, state `交互式选择控件当前不可用，降级为文字选择`, then ask compact choice questions in chat.
4. If the user explicitly demands interactive choice controls, do not downgrade to text questions, manual ABC answers, or chat-only questionnaires. State that the interactive tool is unavailable in the current mode, pause the interview, and require switching to a mode/tooling context where the interactive user-input tool is available.
5. If the user complains that the workflow is still manual, update the skill or current process and restart from the first interactive choice batch.

Interview rules:

- Ask no more than 3 questions per round unless the user explicitly asks for a full questionnaire.
- Make the recommended option first and label it `推荐`.
- Provide 2-3 concrete options per question when using an interactive tool, plus rely on the tool's free-form override when available.
- Use stable `snake_case` identifiers for each question when the tool supports IDs.
- After each round, summarize `已确认`, `待确认假设`, and `下一轮要问什么`.
- Continue until at least 15 key requirement areas have been covered, but avoid dumping all questions at once.
- Convert choices into a requirement matrix as the conversation progresses.

Cover these 15+ areas across rounds:

- Goal
- Users
- Scope
- Data sources
- Permissions
- Outputs
- Frequency
- Exceptions
- Compliance
- Quality standard
- Acceptance criteria
- Budget/cost
- Launch method
- Maintenance owner
- Future expansion

Keep questions concrete. If the user answers partially, convert answers into confirmed requirements and keep unresolved items as `待确认假设`.

Use this choice format only as fallback when an interactive choice tool is unavailable and the user has not explicitly required UI-backed interaction:

```text
问题：目标版本先做到哪一级？
A. 本地研究 MVP（推荐）：先打通数据、报告互引和手动触发。
B. 稳定研究平台：加入定时更新、质量评分、报告版本管理。
C. 团队/生产级：加入权限、审计、部署、监控和多人协作。
```

For finance, cost, collection, payroll, tax, budget, ROI, or trading-related systems, include formula and data-source choices early, for example:

```text
问题：交易建议输出到什么强度？
A. 研究观察（推荐）：催化剂、标的池、风险、观察指标，不给买卖指令。
B. 策略建议：给条件式买入/卖出/止损规则，必须附依据和风险。
C. 组合建议：给仓位、再平衡、风险预算，需要更严格验收。
```

### 2. Pursuing Goal Definition

Summarize the current executable goal with:

- One-sentence objective
- Success criteria
- Inputs and outputs
- Scope boundaries
- Explicit non-goals
- Default assumptions
- Blocking items
- Deliverables

### 3. PRD

Produce a PRD with:

- Background
- User roles
- Use cases
- Feature list
- Data fields
- Permission rules
- Exception scenarios
- Acceptance criteria

### 4. Technical Plan

Produce a technical plan with:

- Frontend pages
- Backend APIs
- Database tables
- File structure
- Permission design
- Test plan
- Implementation order

If a layer is unnecessary, state it explicitly, for example: `本阶段不需要后端 API`.

### 5. Implementation Plan Confirmation

Split work into 5 small tasks. Each task must include:

- Goal
- Input
- Output
- Acceptance method
- Test method
- Rollback method
- Risk point

Wait for user confirmation before implementation.

### 6. Incremental Implementation

Implement one task at a time. After each task:

- Run relevant tests.
- If tests fail, explain the failure, fix it, and retest.
- Do not bundle multiple unverifiable changes into one delivery.

### 7. Self Review

Review for:

- Bugs
- Data loss
- Permission issues
- Financial calculation errors
- Boundary conditions
- Insufficient tests
- External dependency risks
- Compliance risks

### 8. Documentation

Update README/docs or provide equivalent documentation with:

- What the feature is
- How to use it
- Data field meanings
- How to test it
- Known limitations

### 9. Final Delivery

Final response must include:

- Change summary
- Test results
- Diff summary
- Risk notes
- Rollback advice
- Next-step recommendations

## Trigger Handling

When the user says they want to design, build, automate, analyze, or improve a system/software/workflow, use this SOP automatically. If intent is ambiguous, ask whether they want to design/build a system or software before starting implementation.

If the user asks for an interactive experience, switch the interview into tool-backed choice-first mode immediately and restart the current requirements flow from the first interactive choice batch. Treat references such as `像政府文件解读系统一开始一样`, `交互式选择问答`, `点击选择`, or `不要手动输入` as explicit requirements for UI-backed selectable question cards. Do not send only text-based ABC questions. If the interactive user-input tool is unavailable, pause and state that the current mode cannot satisfy the interaction requirement instead of falling back to manual text input.
