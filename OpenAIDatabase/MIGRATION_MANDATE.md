# ⛔ 未完成的强制迁移：OpenAIDatabase 数据 → Private-AgentDatabase

> **给后续接手 OpenAIDatabase 的每一个开发者/agent：这是一项必须完成的待办，不是可选项。**
> 本仓 `OpenAIDatabase/data/`（约 536MB，702 跟踪文件）目前仍是**活运行记忆**，
> 与全仓「数据只进 Private-Database、不进代码仓」的政策相悖。**它尚未迁走，是因为现在迁会当场搞坏运行，不是因为不用迁。**

## 终态（必须达成）

1. `OpenAIDatabase/data/` 的数据落到私有仓 `LinzeColin/Private-Database` 的 `Private-AgentDatabase/` 区（内容寻址 + manifest）。
2. 所有消费方的**启动/CI 读取路径改为经 SDK 从 Private 读**（不再读本地 `data/`）。
3. 校验通过后，**从本公开仓删除本地 `data/`**（含 git 历史清除由 Owner 决策）。

## 为什么现在还没做（现状事实）

- 启动契约 `AGENTS.md`：`Default startup reads only data/memory/agent-memory.json` —— **启动即读本地**。
- 路由器 `scripts/route_agent_resources.py` + `config/context_sources/resource_routes.json` 的 `read_order` 全是**本地相对路径**。
- CI `atlasctl build-atlas`、个性化导出/评估、多个 `tests/test_*` 直接读本地 `data/memory/agent-memory.json`。
- 跨仓消费方 `CodexProject/AGENTS.md` 的 memory discovery 指针也指向本地 `OpenAIDatabase/data/...`。
- SDK 客户端 `scripts/private_db_client.py` **已存在但未接入**任何启动/CI 链路。
- **结论：现在删/迁本地 `data/` = 启动 handshake、CI、个性化链、跨仓消费方、测试套件全部当场失败。**

## 必须按序完成的前置步骤

1. 把上述消费方（含 CodexProject 跨仓消费方与 CI `atlasctl`）的读取改为
   `private_db_client.py get Private-AgentDatabase <path>` 经 SDK 读 Private。
2. 改造后跑通：启动路由 + `atlasctl build-atlas` + 个性化评估 + 全量测试，并校验数据一致。
3. **重新校验镜像新鲜度**：`data/MIRROR_STATUS.json` 记的一致性是时间点快照；本地 `data/` 是活读写，
   镜像很可能已落后，退役前用 `private_db_client.py verify Private-AgentDatabase` 补齐。
4. 三项全绿后，才从本公开仓删除本地 `data/`。**在此之前保持只读对待，勿删勿改。**

## 底线

- 在启动/CI 完成 SDK cutover 之前，本地 `data/` 是本仓活权威，**任何 agent 不得删除或迁走**。
- 但这项迁移**必须最终完成**——它是全仓「代码/数据分仓」政策下唯一尚未闭环的缺口。
- 完成后请删除本文件，并更新 `data/WHERE_IS_THE_DATA.md` 与 `data/MIRROR_STATUS.json`。
