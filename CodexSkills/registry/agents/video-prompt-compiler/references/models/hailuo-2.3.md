# MiniMax Hailuo 2.3 Adapter

状态：`ACTIVE_OFFICIAL`；核验日期：2026-08-17。

官方 API 记录：Hailuo 2.3 支持 T2V 与 I2V；Fast 版本支持 I2V。官方接口的 Prompt 最大长度为 2,000 字符，时长与分辨率由参数单列。

## T2V

按“主体与环境 → 主动作 → 一个相机行为 → 材料/环境反馈 → 结束状态”写清楚。避免长篇多镜头项目塞入单次 Prompt。

## I2V

图片已定义主体、构图、光线和风格。正文重点写：保持项、主体运动、相机运动、环境运动和结束状态。不要重述全部外观。

## 长度

超过 2,000 字符直接阻断；复杂任务拆镜头。

来源：
- https://platform.minimax.io/docs/release-notes/apis
- https://platform.minimax.io/docs/api-reference/video-generation-i2v
