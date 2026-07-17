# Memory Atlas v1.2.1 S09-P2-T2 Review

## 结论

`S09-P2-T2` 为 `PASS_LOCAL_ONLY`。一个 `fixture` 状态的
`standard-agent-example` 已通过纯 registry 配置接入通用 reader；runtime
没有按该名称硬编码。fixture 仅能 dry-run，真实验收由临时 workspace runner
完成，不能把 synthetic 数据写入正式 Memory Atlas。

## 实现

- tracked JSONL fixture 包含 2 个 event、3 条 message，SHA-256 固定；CLI
  只返回 count/hash，不返回内容或本机路径。
- acceptance runner 要求 repository 外的空 workspace；重跑只接受自己创建的
  marker/database/bundle/restore，内部 symlink 或特殊文件 fail closed。
- T1 reader 读取 fixture 后，既有 generic sync 生成 2 个 append-only public-raw
  文件、immutable raw ledger、run manifest 和 1 个 replaceable derived summary。
- runner 将 raw、ledger、manifest、derived 共 5 个文件封装为 canonical JSON
  recovery bundle，强制走现有 45 MiB archive contract，逐 part 和整包校验后
  no-overwrite restore；恢复包再次逐文件 base64、bytes、SHA-256 对照当前输出。
- registry main policy 固定为 `final_delivery_only/main/no PR/no force/
  remote-race-stop`。fixture source 的非 dry-run apply 在 parser 前失败；直接
  `--push-main --dry-run` 也以 0 次 push attempt 停止。

## 验证

- test-first：T2 模块不存在时 `ModuleNotFoundError`。
- dedicated fixture：最终 `11/11 PASS`。
- fixture/reader/registry/S04/S06/R7/CLI/profile/test-value 相关回归：
  `141/141 PASS`。
- public-raw layout 修复后 fixture/layout/registry：`36/36 PASS`。
- script migration/profile/test-value：`35/35 PASS`。
- `py_compile` PASS；当前全局 Python runtime 仍未提供 `ruff`，未声称通过。
- `validate:fast`：`6/6 PASS`，25.771 秒。
- `validate:sync` 首次在 337 项 unit 中仅暴露 fixture 被错误视为生产活跃分区；
  修正为 `fixture` 非活跃后，最终 `10/10 PASS`，480.868 秒，其中 unit
  80.378 秒、credential scan 377.118 秒，`raw_mutation=false`、
  `remote_push=false`、`shell=false`。

## 风险与回滚

- example 是 synthetic acceptance source，不代表任何真实未来平台已接入。
- 生产 generic source 必须使用新的 `configured` source id；不得复用 fixture
  namespace。非标准格式、plugin 权限与安全接口仍属于 `S09-P2-T3`。
- 回滚可 revert T2 registry 行、fixture runner/contract/test；既有 T1 reader、
  ChatGPT、Codex、raw ledger 和 archive/restore 合同保持不变。

## 下一步

下一 run 只执行 `S09-P2-T3`。整包、最终复审与补救全部完成前禁止 push、
部署或共享缓存清理；`S08-P3-T1` 继续保持 owner-deferred/open。
