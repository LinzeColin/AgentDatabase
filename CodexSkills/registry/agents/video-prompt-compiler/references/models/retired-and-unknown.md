# Retired / Unknown Model Labels

## Sora 2

当前注册表标记 `RETIRED_NON_DEFAULT`：Sora 网页/应用入口已于 **2026-04-26** 停止，API 停止日期为 **2026-09-24**。在本包研究截止日 **2026-08-17**，不得把网页/应用当作可用默认入口；只有用户账户中的剩余 API surface 已经现场确认时，才建立临时适配。

官方状态来源：OpenAI Help Center 的 Sora discontinuation 说明。

## 未经官方核验的版本标签

例如 `Wan 2.6/2.7`、`Seedance 2.5`、供应商封装名或客户端昵称：

```text
VERIFY_AT_RUNTIME
```

处理方式：

1. 保留用户原始标签；
2. 不猜测模式、时长、分辨率或参考能力；
3. 先用通用 IR 输出；
4. 读取当前官方说明或界面后再映射；
5. 无法确认时选择已核验模型族作为备选。
