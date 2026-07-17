# Memory Atlas v1.2.1 S09-P2-T1 Review

## 结论

`S09-P2-T1` 为 `PASS_LOCAL_ONLY`。本轮只完成通用只读 Agent reader；
`S09-P2-T2` 的 future-Agent fixture、raw archive、parser、derived、restore、
main-push contract 和 `S09-P2-T3` plugin contract 均未实现。

## 实现

- 一个 registry 绑定 reader 覆盖显式 file、递归 directory、JSON、JSONL、
  self-contained SQLite export。
- directory 按 UTF-8 relative path 确定性排序；unsupported regular file 不读取，
  symlink、special file、entry/file/byte/record/schema/scalar 上限漂移 fail closed。
- JSON 支持 object、object list 和 `events` object list；JSONL 只允许 object row。
- SQLite 仅使用 `mode=ro&immutable=1` 与 `query_only`，拒绝 WAL/SHM/journal、
  BLOB、无 user table、非法 `record_json` schema 和超限输入。
- reader 保存运行时来源 provenance，但 CLI 只输出 count/hash，不输出 record、
  title、message body 或本机绝对路径。
- generic sync 在 downstream append-only commit 前后重新验证完整 source tree 与
  supported-file SHA-256；source directory 包含 database output 时写入前拒绝。

## 验证

- test-first：实现前按预期 `ModuleNotFoundError`。
- dedicated：`14/14 PASS`。
- generic/source-registry/S04/R7/CLI compatibility：`56/56 PASS`。
- Codex archive/derived/restore cross-source follow-up：`56/56 PASS`。
- validator-profile 与 test-value：`23/23 PASS`。
- script migration：`12/12 PASS`。
- `py_compile`：PASS。当前全局 Python 未提供 `ruff`，未虚构 lint 结果；
  official `validate:fast` 的 frontend lint 实际通过。
- `validate:fast`：`6/6 PASS`，`73.960s`，`raw_mutation=false`、
  `remote_push=false`、`shell=false`。
- 最终 `validate:sync`：`10/10 PASS`，`482.041s`；sync unit `109.872s`，
  complete credential scan `346.132s`，安全标志全部为 false。

第一次 sync profile 已通过新 unit/layout/三来源 dry-run，只在复制来的历史 Codex
archive part hash 处 fail closed。隔离验证副本从 `HEAD` 恢复 canonical part；已知
空的复制版 ChatGPT part 同样只在验证副本恢复。共享 checkout 和来源数据未修改。

## 风险与回滚

- 活跃 SQLite WAL 数据库不是 self-contained export，必须由来源工具先导出一致副本。
- T1 不猜测未来 Agent 的字段映射；首个 source fixture 与完整恢复证据属于 T2。
- 回滚仅 revert 本 Task reader/registry/sync integration；ChatGPT、Codex、旧 Markdown
  adapter 与 append-only raw 保持。

## 下一步

下一 run 只执行 `S09-P2-T2`。整包、最终复审与补救全部完成前禁止 push、部署或
共享缓存清理；`S08-P3-T1` 继续保持 owner-deferred/open。
