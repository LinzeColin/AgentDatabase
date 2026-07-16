# Memory Atlas v1.2.1 S07-P3-T3 Codex Restore Proof Review

## 结论

`S07-P3-T3` 本地验收通过。实现从一个已存在且为空的临时目录开始，连续两次独立复制并验证同一份 immutable baseline Codex archive，执行 archive 自带且经 verifier 校验的 `restore.sh`，随后在只登记这一份 archive 的隔离数据库中运行正式 `build_codex_derived()`。两轮 restore inventory、derived outputs、event provenance 和 replay 结果一致。

本 Task 只证明一份 baseline archive 的本地可恢复性和派生重建确定性。它不会把单归档的 427 events 冒充当前 canonical 两归档的 432 events，也不更新 canonical derived snapshot、Memory Atlas 页面或线上数据。

## 交付范围

- Contract：`config/data_sources/codex_restore_proof.json`
- Model parameters：`机器治理/参数与公式/codex_restore_proof.v1_2_1_s07_p3_t3.json`
- Runtime：`scripts/memory_atlas_cli/codex_restore_proof.py`
- CLI：`scripts/audit_memory_atlas_codex_restore_proof.py`
- Regression：`tests/test_memory_atlas_codex_restore_proof.py`
- Machine proof：`机器治理/证据与日志/codex_restore_proof/codex_restore_proof.v1_2_1_s07_p3_t3.json`

## 隔离和失败关闭

- CLI 使用 `python3 -I -B`，不加载 `PYTHONPATH` 或 user site。
- 每轮 restore 子进程只收到 task-owned `HOME`、`CODEX_HOME`、`TMPDIR` 和 XDG 路径；不继承用户环境。
- 输入 archive 采用字节复制并重新校验，不使用会改变 canonical inode `ctime/link count` 的 hardlink。
- 隔离数据库只包含 canonical baseline index、该 index 在原 raw manifest 中的精确 ledger 行、archive copy、derived contract 和 model。
- Workspace 必须是绝对、canonical、非 symlink、已存在且为空，并且不得与 database tree 重叠。
- 每个 run directory 只在 inode identity 未变时删除；未知或被替换路径不清理并 fail closed。
- archive、workspace、空间、restore、derived、provenance、重复性、清理或隔离任一不确定即失败；没有 fetch、push、deploy、branch、PR、merge 或 rebase 路径。

## 真实恢复证据

执行命令：

```bash
python3 -I -B OpenAIDatabase/scripts/audit_memory_atlas_codex_restore_proof.py \
  --database-dir OpenAIDatabase \
  --archive-id codex-public-raw-20260715t1300z \
  --workspace-root /private/tmp/memory-atlas-s07-p3-t3-current-workspace \
  --output /private/tmp/memory-atlas-s07-p3-t3-current.json
```

结果：

- Baseline archive manifest SHA-256：`6640cbdeed803df4c3090aaa2e51350d68210bf059bdcafe5ec65f40561cef81`
- Package：558,731,407 bytes，12 parts，SHA-256 `e1406eea8b67ffdac96fb41f26f821696389b6eb5ed9ef069b1b42b186d1f174`
- 每轮恢复：432 files，其中 430 data files，共 2,068,870,942 data bytes
- Restored inventory SHA-256：`3442d5ffac6f574793eea20000a27bb5cc9e066d4fc3a2eadb29aace933751c6`
- 每轮重建：427 events、427 facets；427/427 event provenance 与 restored member/source manifest 一致
- 两轮初次结果：`BUILT_FROM_IMMUTABLE_RAW`
- 两轮立即重放：`NO_CHANGES`，零 parsed archive、零文件写入
- 两轮五个 derived output 的 byte size 与 SHA-256 全部一致
- Canonical archive 前后 stable identity、manifest、package、parts 一致
- 两轮 workspace 均清空；没有保留 runtime data
- Machine proof SHA-256：`6dd8139b48ba528015a6d42e069048e4565b9d7cee1dc89b13f5470ad0afa7eb`

关键 derived hashes：

| Output | Bytes | SHA-256 |
|---|---:|---|
| `codex_events.jsonl` | 1,978,617 | `aa425fc07738f4b737989eb1a59901f64d7772f7a41d6388916635e80d865988` |
| `codex_facets.jsonl` | 719,675 | `41c5a0d6978182e7d9af81f56a95a8cc681223f5da6d716864f8a2f4ee15dfcc` |
| `codex_behavior_summary.json` | 3,989 | `e164de6bd246b0b462e100ba42139d31b928861491f0bfd0c45d033da9ac3d0f` |
| `codex_universe_state_input.json` | 7,211 | `33032405f1cbba0735bc41d0e031ed1728d292d2176c5d8f2af2b78c9451f1ec` |
| `codex_derived_state.json` | 2,438 | `adaac9aface70cd41fbe73e3fdf097a73cee3e6a355a1739d28c7aa5402a1350` |

## 验证状态

- Test-first import failure：按预期失败，生产模块当时不存在。
- Dedicated fixture：4/4 PASS，含真实小 archive 双轮 restore/rebuild、合同/模型漂移、workspace 安全和结构化 CLI 失败。
- Restore/profile/test-value/human-plane/script-migration focused regression：63/63 PASS；扩大后的相关回归在实现候选为 105/105 PASS（15.401 秒），治理收口后再跑为 105/105 PASS（11.331 秒）。
- 当前机器证明已由现行 `python3 -I -B` 代码重跑；实现提交 `9b9e6a1d4` 的干净克隆再次从空目录完成双轮恢复，报告与 tracked proof byte-identical。
- 干净克隆 `validate:fast` 6/6 PASS（31.224 秒），`validate:sync` 10/10 PASS（214.895 秒）；命令审计均记录 `raw_mutation=false`、`remote_push=false`。
- 首次 fast 因临时 sparse checkout 漏掉 `.rgignore` 和 tracked raw inventory 正确失败；补齐完整 checkout 后原命令通过。首次 `--ci-checkout` 在 raw roots 仍物化时正确 fail closed；改用 GitHub Actions 的精确 sparse patterns 后 raw-isolated audit PASS，570 个 tracked raw 路径未读取正文。
- Human-plane PASS：7 个浅层中文入口、3 个 owner 入口、162 个机器文件、35 个 active configs、125 个 evidence payloads；test-value PASS。Script migration validation 无错误，scanned scripts 74、exact duplicates 0、mapped scoped scripts 213、retained representatives 18。
- Project governance required validation 为 0 error/0 warning，renderer 为 0 drift/0 reference issue，48 条 governance events 全部为合法 JSONL。带全仓 semantic drift 的组合命令仍因本 Task 外既有 root/KMFA 62 条旧 manifest/private-runtime reference 错误返回非零，但其 OpenAIDatabase section 为 `errors: 0`；本 Task 未修改或掩盖这些外部错误。
- 完整 privacy scan PASS（180.39 秒）：515 个 public raw files、35 个 large public raw files 全部纳入检查，high-risk secret、credential-like path、tracked private raw 和 credential echo 均为 0。
- 共享仓库边界复核发现并行外部执行流在 01:32 运行 `fetch --prune origin`、01:33 运行 `pull --rebase --autostash origin main`，把 unrelated S04 commits 留在 canonical detached HEAD `216bc36ac`；它没有移动本 Task 的 `main` 引用、没有 push。本 Task 自身未调用 fetch/push/merge/rebase，并在隔离 clean main worktree 完成。该并发事件已显式记录，不能用“全仓无 fetch/rebase”掩盖。

## 回滚和边界

如后续 gate 失败，保留 immutable archive、机器 proof 和失败原因；用本 Task 的本地纠正提交或 `git revert` 精确回退。不得删除 raw、force push 或重写历史。本 run 完成后只把下一 Task 指向 `S08-P1-T1`，不开始 S08，不执行任何远端上传。
