# v0.0.0.32 — T02 稳定指标与 Benchmark Registry

分类：**apply**。实质在 2026-08-03 就落了地，但**它的证据到 2026-08-04 才第一次真的跑起来**，
这份记录是补的，并且把补的原因写在这里。

## 指标拆分（MA-LIVE-AC-006）

混合分母被拆成五个各自发布的指标，旧字段仅作兼容、不参与首页真值：

| 指标 | 分母 |
|---|---|
| `verified_outcome_rate_event` | 事件数 |
| `verified_outcome_rate_work_time` | 已知工时（分钟） |
| `work_time_coverage_rate` | 有工时记录的事件 |
| `outcome_evidence_coverage_rate` | 有结果证据的事件 |
| `verification_debt_proxy_event` | 未验证事件 |

`legacy_verified_outcome_rate` 带 `compatibility_only: true`，
`test_live_snapshot_adapter_v31.py` 断言它不等于旧的混合值且被标为仅兼容。

## Benchmark 严格门（MA-LIVE-AC-013）

`benchmark_comparator.compare()` 只有在分类法、单位、时间窗、总体范围和样本数**同时**一致时
才允许直接差值；否则降到 `DIRECTION_ONLY` 或 `NOT_COMPARABLE`，并给出理由。
生产当前是 `INSUFFICIENT_DATA`——没有同口径总体，所以不生成任何全球百分位。

## 这份记录为什么是补的

T02 的声明产物是「metric contract tests」和「benchmark gate tests」。两个文件都在，
也一直被当作它已完成的依据。**它们从来没有跑过。**

文件放在 `scripts/memory_atlas_private/`，用的是裸导入
（`from visual_analytics import …`），只有那个目录恰好在 `sys.path` 上才解析得了；
pytest 连收集都做不到，判据、policy、CI 三处都没有任何一处引用过那五个文件。

移进仓里唯一受管的测试目录、改成绝对导入之后，**第一次真跑：21 条里 18 条失败。**
全部是移动带来的路径假设，或是此后合同已经变化的断言——其中一条断言
「Tier B 缺失使产品降级」，而 `MA-LIVE-AC-009` 并不要求这一条。
现在 21/21 通过，五个文件全部登记进 `verification_policy.json`。

新增判据 `test_no_test_file_hides_outside_the_gated_directory` 钉住这条性质：
**每个测试文件都必须有东西在跑它。** 它不是「scripts/ 下不许有测试」——
验收 oracle 就在那里，判据用 unittest discover 跑它们；
写成更粗的规则会每次都报那三个，然后我就学会无视它。

## 证据

- `OpenAIDatabase/tests/test_visual_analytics_v31.py`（5 条）
- `OpenAIDatabase/tests/test_benchmark_comparator_v31.py`（3 条）
- `OpenAIDatabase/tests/test_live_snapshot_adapter_v31.py`（8 条，含指标拆分与兼容字段）
- `OpenAIDatabase/tests/test_live_snapshot_store_v31.py`（4 条）
- `OpenAIDatabase/tests/test_api_live_snapshot_v31.py`（1 条）
- 全部进入 canonical gate 的 `backend_suite`，实测 PASS。
