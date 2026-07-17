# Memory Atlas v1.2.1 S09-P2-T3 Review

## 结论

`S09-P2-T3` 为 `PASS_LOCAL_ONLY`。非标准来源只能在 Memory Atlas 外部转换为
严格、有限的 JSON envelope；Memory Atlas 不 import、不执行任意 plugin 代码，
只把 envelope 当作不可信数据。host 在任何写入前重新执行 identity、schema、
hash、credential、append-only raw、raw ledger、derived 与 main policy gate。

## 实现

- registry 只允许 `external_envelope_only`，固定 protocol、host entrypoint、
  contract/model refs、host-owned gates 和 `final_delivery_only` push policy；
  不存在 module、command、network、database 或 direct-write capability。
- envelope 顶层和 event/message 均为 exact-key schema，绑定 source/plugin
  identity，并限制文件、event、message、identifier、title 和正文大小。未知字段、
  重复 ID、非法 role、hash 漂移与超限一律 fail closed。
- `canonical_events` 的 canonical JSON SHA-256 由 host 重算。外部 source
  artifact 的 hash/byte size 仅标为 `producer_claim_only`，不伪装成 host
  已验证事实。
- T1 read-only snapshot 在 downstream commit 前后复核 envelope 未变化；随后
  host 复用既有 normalize、credential exclusion、public sanitizer、append-only
  raw、immutable ledger、run manifest 与 replaceable derived pipeline。
- fixture source 只能 dry-run 或在 repository 外的隔离数据库验收；正式数据库
  apply 在 parser/write 前拒绝。plugin source 的 `--push-main --dry-run` 在
  canonical Codex gate 前停止，fetch/commit/push attempt 均为 0。

## 验证

- test-first：实现前预期 `ModuleNotFoundError`。
- dedicated plugin regression：`12/12 PASS`。
- source registry/read adapter/fixture/public layout/atlasctl/S04：`61/61 PASS`。
- script consolidation/test value/validator profile：`35/35 PASS`。
- plugin 与 raw/credential/archive/restore/main 边界回归：`183/183 PASS`。
- fixture compatibility remediation：Codex raw archive/restore/source registry
  `33/33 PASS`。
- `py_compile` PASS；`ruff check` PASS。
- `validate:fast`：`6/6 PASS`，24.277 秒。
- `validate:sync` 首次在 349 项 unit 中发现完整 registry 的 Codex 临时数据库
  fixture 未携带新 plugin host stub/model，造成 1 failure、26 errors；生产
  registry 的严格存在性检查未放宽，只补齐 fixture。最终 `10/10 PASS`，
  500.686 秒，其中 unit 136.561 秒、credential scan 354.267 秒，
  `raw_mutation=false`、`remote_push=false`、`shell=false`。

## 风险与回滚

- contract 只证明安全接入边界与 synthetic fixture，不代表任何真实第三方来源
  已连接。
- source artifact digest 是 producer claim；可信 raw 仍从 host 实际收到并
  校验的 envelope bytes 与 canonical events 开始。
- 外部 transformer 的部署、认证和运行不属于本任务；不得把任意 executable
  写入 registry 或在 Memory Atlas 进程内加载第三方代码。
- 回滚可 revert plugin registry 行、合同、host adapter、fixture 与测试；现有
  standard generic reader、ChatGPT、Codex、raw ledger 和 main gate 保持不变。

## 下一步

下一 run 只执行 `S09-P3-T1`。整包、最终复审与补救全部完成前禁止 push、
部署或共享缓存清理；`S08-P3-T1` 继续保持 owner-deferred/open。
