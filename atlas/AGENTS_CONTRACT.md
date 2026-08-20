<!-- BEGIN memory-atlas:agent-contract v1 -->
## 开发经验沉淀 —— 动手前先查，收尾必须回写

> 这一节由 `atlas/build/install_agents_md.sh` 统一分发到 Claude Code / Codex / Kimi Code / DSH。
> 不要手改这一段：改了会在下次分发时被覆盖。要改就改 `AgentDatabase` 仓的
> `atlas/AGENTS_CONTRACT.md`，然后重新跑一次分发。

### 唯一地址

`LinzeColin/Private-Database` 的 **`dev-notes` 分支** → `Private-AgentDatabase/dev-notes/`

- `AGENT_BRIEF.md` —— 给人和 agent 读的正文
- `agent_brief.json` —— 给程序读的同一份数据
- `compounding-events/` —— agent 收尾时产的成果复利事件（见下）

```bash
gh api "repos/LinzeColin/Private-Database/contents/Private-AgentDatabase/dev-notes/AGENT_BRIEF.md?ref=dev-notes" \
  --jq .content | base64 -d
```

网页版：`memoryatlas.linzezhang.com/brief/`（在 Cloudflare Access 后面）。
本机副本：`~/.memory-atlas/brief/AGENT_BRIEF.md`。

里面的内容全部是从本机所有 agent 会话**确定性派生**出来的 —— 没有一句是模型现编的：
被反复问过的事、每个项目的进入简报、最烧钱的会话形态、报错最密集的地方、工具使用分布。

### 动手前：先查

1. **先查再问。** 简报里每一条都是已经被问过很多次的。最贵的那条被问过 738 次、
   烧掉 2.27 亿 token。再问一次就是再烧一次。
2. **进某个项目之前**，读该项目那一节：它的常见话题、常用工具、每场平均报错次数。
3. 查不到再问。查得到还问，就是在给同一个答案付第二次钱。

### 收尾时：必须回写（这是硬要求，不是建议）

**什么算「收尾／归档」**：会话结束、上下文被压缩、一件交付做完、PR 合并、
或者你正准备说「完成了」的那一刻 —— 任意一个成立就算。

收尾时按顺序做三件事：

1. **复审这一轮**：这次踩过什么坑、什么判断当时不明显、下一个 agent 怎样能少走一遍？
   只留**下一次真的用得上**的，不写流水账。
2. **写进对应仓的 `AGENTS.md`**（哪个仓的活就写哪个仓，不跨仓）。
   一条经验一段，格式：
   ```
   - **结论**：<一句话，直接可执行>
     **为什么**：<不写这句，下一个 agent 会以为可以绕过去>
     **代价**：<踩这个坑花了多少时间／token／几次返工；没量到就写「没量」>
   ```
3. **跑一次蒸馏并推送**：
   ```bash
   bash ~/.memory-atlas/on-archive.sh
   ```
   它会重新蒸馏本机全部会话、更新 `AGENT_BRIEF.md`，并推到上面那个私有仓。
   30 分钟内重复调用会自动跳过（去抖），所以多调几次不会有副作用，漏调才有。

**Claude Code 和 Codex 已经挂了钩子**（`PreCompact` / `SessionEnd` / `SessionStart`），
第 3 步会自动触发；**Kimi Code GUI 和 DSH 没有钩子机制，必须自己跑那一行**。
第 1、2 步在哪个 agent 里都得自己做 —— 钩子只能重算机器派生的那一半，
「这次学到了什么」只有你知道。

### 收尾时还可以多做一步：产一条「成果复利事件」

上面三步管的是「经验有没有留下来」。这一步管的是**「留下来的东西有没有变成结果」**。

不是每次都要做 —— 只有当这一轮**确实结束了一件事**（不是随手改两行）时才值得：

把结论写成一个 `memory_atlas.compounding_event.v1` JSON，推到

    LinzeColin/Private-Database @ dev-notes 分支
    Private-AgentDatabase/dev-notes/compounding-events/<event_id>.json

Memory Atlas 每天会把它拉进来，投影成转化漏斗，显示在站点的「档案 → 转化」那一屏。

**最小可用的字段**（完整 schema 见 Memory Atlas 仓的 `atlas/build/compound.py`）：

```json
{
  "schema_version": "memory_atlas.compounding_event.v1",
  "event_id": "<agent>-<日期>-<序号>",
  "generated_at": "<ISO-8601>",
  "producer": { "kind": "agent_closeout", "name": "<哪个 agent>" },
  "missions": [{ "mission_id": "", "project": "", "objective": "",
                 "actual_outcome": "", "completion_state": "COMPLETE|PARTIAL|BLOCKED|ABANDONED",
                 "evidence": [], "unresolved_obligations": [] }],
  "lessons": [{ "lesson": "", "scope": "project|cross_project|tentative",
                "evidence": [], "do_not_repeat": "" }],
  "failure_inputs": [{ "failure_id": "", "project": "", "symptom": "", "impact": "",
                       "root_cause_state": "PROVEN|HYPOTHESIS|UNKNOWN",
                       "failed_attempts": [], "effective_fix_or_workaround": "",
                       "do_not_repeat": "", "regression_asset_candidate": "" }],
  "candidates": [{ "candidate_id": "", "type": "prompt|workflow|sop|bug_guard|checklist|skill|stop_rule|other",
                   "problem": "", "evidence": [], "recurrence": "",
                   "cost_of_not_fixing": "", "stage": "CAPTURED|QUALIFIED|EXPERIMENT|HOLD|REJECT" }],
  "verification_state": "VERIFIED|PARTIAL|UNVERIFIED"
}
```

**四条硬规矩**（写之前先读，写错了系统会当场压回去并记一笔）：

1. **「做完了」不等于「被采用」。** 文件写完、commit 了、部署成功了，都还只是 OUTCOME 之前的事。
2. **没有采用证据不许写 ADOPTED，没有经济证据不许写 ECONOMIC_IMPACT。**
   写高了 Memory Atlas 会按证据压回去，并在「被压回去的」那张表里点名 —— 只会更难看。
3. **金额未知就留 `null`，不要填 0。** 0 是一个断言（「没赚到」），未知不是。
4. **不要放完整聊天、思维过程、大段工具日志。** 只留下一个 agent 真的用得上的东西。

允许一次都不产 —— 一个模式只出现过一次就做成 Skill，是把这套东西做坏的最快方式。

### 三条边界

- **别手写 `AGENT_BRIEF.md`。** 它每天重新生成，手写内容会被整体覆盖。
  新结论写进仓里的 `AGENTS.md`，下一轮蒸馏会自己带进去。
- **别把密钥、token、Owner 原话写进任何公开仓。** 沉淀目标仓是私有的；
  推送脚本会先核对目标仓可见性，不是 PRIVATE 就直接拒绝推送。
- **别跨仓写。** 一个仓的经验只写进那个仓的 `AGENTS.md`。
<!-- END memory-atlas:agent-contract v1 -->
