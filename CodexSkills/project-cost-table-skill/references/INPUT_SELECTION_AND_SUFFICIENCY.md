# 输入选择与充分性门禁

本说明适用于每次 `inventory`、`reference-replay`、`calculate`、`review` 或 `restate` 操作。R3 只实现运行前门禁与诊断输出，不生成财务工作簿；最终工作簿仍须等待后续 Run 的计算和校验能力全部实现。

## 固定顺序

1. 先从 `templates/operation_request.template.json` 形成私有操作请求。
2. 只读取请求、公共配置、私有 manifest 和原始目录元数据，生成 mode/Metric/basis 专属清单；在这一步前不得打开原始业务文件正文。
3. 每个必需 slot 必须由私有 manifest 显式选中唯一 opaque source ID，并锁定完整 SHA256、schema fingerprint、reader version 和 logical source period。mtime 只作诊断，不能作权威选择依据。
4. 输入足够时不再询问，输出 `input_sufficiency_report.json`、绝对路径索引和封存哈希，然后进入下一门禁。
5. 输入不足时只提出一次紧凑编号矩阵，并停止正式处理。未回复不是授权。

## 明确处理选项

1. `SUPPLIED`：补充输入；必须提供证据，并重新扫描为 `PRESENT` 后才算满足。
2. `SCOPE_REDUCED`：明确移除受影响的 Metric/basis/期间/类别；若该 Metric 仍在新请求中则拒绝。
3. `QUALIFIED_ALTERNATE_EVIDENCE`：提供合格替代证据；必须重新验证为 `PRESENT`。
4. `OMIT_OPTIONAL_PRESENTATION`：仅能省略不影响金额、谱系、门禁或解释的展示字段。
5. `BLOCKED`：保持 `BLOCKED`，停止正式计算并保留诊断。

任何安全、身份、必需公式、算术、来源守恒或一分钱对账门禁都不能通过“授权省略”绕过。处理记录必须包含用户原话、opaque instruction ref、受影响 Metrics 和效果，并同时绑定：上一份已封存的不足报告 request hash、当前结果请求 hash、manifest hash、要求配置 hash。任一绑定漂移都必须重新确认。

## 输出定位

默认输出目录是 `<private_runtime>/runs/<run_id>/outputs`；也可指定一个全新的绝对私有目录，但不能与原始输入重叠或落入非私有 Git 跟踪路径。每次运行都打印并写入：

```text
RESULT_STATUS
OUTPUT_DIR
PRIMARY_OUTPUT
OUTPUT_INDEX
NEXT_STEP
```

发生明确处理时，输出目录必须另含已封存的 `input_resolution.json`。Skill 不设置财务负责人、授权人或公司审批状态；所有数据和产品校验通过后才直接生成最终版本，生成后的公司内部流程由 Codex/用户在 Skill 外继续。
