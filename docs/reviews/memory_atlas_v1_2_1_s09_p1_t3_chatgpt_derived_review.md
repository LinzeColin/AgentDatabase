# S09-P1-T3 ChatGPT Derived Inputs Review

## Scope

本 Task 只从 `S09-P1-T2` 的 validated canonical ledger 与对应 append-only
public raw 生成 ChatGPT facets、主题、活动和 Universe State 输入。`S09-P2`
通用 Agent adapter、Atlas snapshot/UI、export/browser/Mail/download、远端上传均不在
本轮范围；`S08-P3-T1` 继续保持 owner-deferred/open。

## Implementation

- 构建前完整验证 canonical JSONL schema、identity、hash 与连续版本链；每个
  `raw_ref` 必须是仓库相对路径、普通文件、内部 `content_sha256` 正确，并能重建出
  完全相同的 canonical conversation/version。
- latest canonical version per conversation 生成 current facet；共享
  `TOPIC_RULES` 优先形成可聚合主题，无法匹配时才回退到脱敏压缩标题；主题与
  Universe cluster 仅使用 latest projection。
- 每个 canonical version 生成一条 activity，因此修改后的对话保留完整活动历史，
  而 current facet/topic 不重复计算旧版本。
- 每条 facet、topic、activity 和 Universe cluster 都直接携带 raw file SHA-256、
  raw content SHA-256、canonical event/version ID 与 version SHA-256。消息正文只在
  内存中用于分类，不写入任何派生文件。
- 输出 bundle 以 state 最后发布；输入/contract/model/output hash 全部一致时返回
  `NO_CHANGES`，不改派生字节或 mtime。raw 或 canonical 在构建中变化时失败关闭。
- 正常 ChatGPT sync 在 canonical commit 后调用构建器；独立
  `atlasctl analyze --stage chatgpt-derived` 也可执行同一合同。registry 和
  `validate:sync` 已登记新入口与测试。

## Evidence

- Test-first：实现前因 `memory_atlas_cli.chatgpt_derived` 缺失触发
  `ModuleNotFoundError`。
- Dedicated regression：`9/9 PASS`，覆盖 strict contract/model、四类输出与双证据、
  replay no-write、latest/history projection、raw/ledger tamper、CLI 和 normal sync。
- Canonical/source-registry/S04/CLI compatibility：`37/37 PASS`。
- Cross-source follow-up：移除 Codex-only temp fixture 对 ChatGPT T3 文件存在性的耦合，
  同时保留 registry exact-value gate；Codex/registry 定向回归 `52/52 PASS`。
- Related regression：final evidence refresh 前 `154/154 PASS`。
- `ruff check` 与 `py_compile`：PASS。
- `validate:fast`：`6/6 PASS`，`23.149s`；首次运行只暴露两处剩余的同一
  ChatGPT dry-run stdout hash，更新到已核验的新 contract 输出后通过。
- `validate:sync`：`10/10 PASS`，`193.074s`；sync unit step `50.231s`，
  credential scan `136.698s`；`raw_mutation=false`、`remote_push=false`、
  `shell=false`。首次运行暴露并关闭 Codex-only fixture cross-source coupling。
- Full profile 前 human-plane 已在 `182` machine files、`45` active configs、
  `135` evidence payloads 下通过；renderer 为 0 drift/reference issue，required
  project governance 为 0 errors/warnings。最终 evidence hash refresh 后仍需重跑这些
  窄门禁，不把刷新前 hash 当作最终 hash。

## Decision

状态：`PASS_LOCAL_ONLY`。T3 核心行为和 full profile 已闭环；本 Task 是第
`63/149` 个已完成 Task，S09-P1 为 `3/3`。最终 evidence hash/renderer 的窄刷新门禁
完成后创建本地 Task commit。下一 run 才能执行 `S09-P2-T1`，整包完成前禁止
push/deploy。
