# Model Status — 2026-08-17

| ID | 展示名 | 状态 | 默认用途 | 关键边界 |
|---|---|---|---|---|
| minimax_h3 | MiniMax H3 | ACTIVE_OFFICIAL | 多模态 Reference/Edit、品牌、音画、多镜头 | 复杂模式按官方 Schema；账户可用性仍需验证 |
| hailuo_23 | Hailuo 2.3 | ACTIVE_OFFICIAL | T2V/I2V 单镜头 | Prompt ≤2,000字符；Fast 只确认 I2V |
| seedance_20 | Seedance 2.0 | ACTIVE_OFFICIAL | 多参考、复杂动作、工业、Edit/Extend | 官方性能声明不替代成片验证 |
| kling_video_30 | Kling VIDEO 3.0 | ACTIVE_OFFICIAL | 人物、元素绑定、对白、多镜头 | 功能开关以账户界面为准 |
| veo_31 | Veo 3.1 | ACTIVE_OFFICIAL | 高端电影叙事、同步音频 | 具体参数/API surface会变化 |
| runway_gen45 | Runway Gen-4.5 | ACTIVE_OFFICIAL | 简洁 T2V/I2V，运动控制 | I2V 不重述输入图；当前网页 2–10秒 |
| wan22 | Wan2.2 | ACTIVE_OPEN_OFFICIAL | 开源 T2V/I2V/S2V/Animate | 不把 Wan 2.6/2.7 当作同一官方版本 |
| ltx2 | LTX-2 | ACTIVE_OPEN_OFFICIAL | 逐时序单段落音视频生成 | 官方建议 200词以内 |
| minimax_design | MiniMax Design | PLATFORM_VERIFY_AT_RUNTIME | 项目编排、素材与多模型工作台 | Router、模型池、credits按账户验证 |
| sora2 | Sora 2 | RETIRED_NON_DEFAULT | 不默认推荐 | 网页/应用已于 2026-04-26 停止；API 计划于 2026-09-24 停止 |
| other | 其他版本/封装名 | VERIFY_AT_RUNTIME | 先输出通用 IR | 不从名字猜能力 |

机器可读注册表：`scripts/model_registry.py`。
