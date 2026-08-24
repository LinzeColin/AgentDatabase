# 模型适配器合同

每个适配器必须声明：

- 官方/可信来源与核验日期；
- 当前状态：ACTIVE / ACTIVE_OPEN / PLATFORM_VERIFY / RETIRED / VERIFY_AT_RUNTIME；
- 支持的输入模式；
- Prompt 正文结构；
- 参数应放正文还是界面；
- I2V/Reference/Edit 的不同处理；
- 长度与复杂度预算；
- 明确失败模式；
- 不得从模型名推断的能力。

编译器先建立统一 IR，再由适配器执行：

```text
IR fields
→ remove non-applicable detail
→ order information by model behavior
→ convert reference roles to model syntax
→ keep interface parameters outside prose
→ validate model-specific limits/schema
```

模型适配器不得修改 `LOCKED_FACT`，不得把未知功能包装成当前账户可用能力。
