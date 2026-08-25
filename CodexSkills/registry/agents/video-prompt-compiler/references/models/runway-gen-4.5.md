# Runway Gen-4.5 Adapter

状态：`ACTIVE_OFFICIAL`；核验日期：2026-08-17。

官方指南显示 Gen-4.5 支持 T2V 与 I2V，当前网页列出 2–10 秒。Runway 强调清晰、直接、正向描述。

## T2V

描述场景中的可见元素和运动：主体、动作、环境、相机与时间发展。需要多个事件时增加时长或拆镜头。

## I2V

输入图已经定义构图、主体、光线与风格。Prompt 几乎只写：主体动作、环境运动、相机运动、运动方式/速度/方向、最后状态。除非要引入新元素或改变外观，不重复描述图片。

先用简单关键运动生成，再逐项增加细节；失败时每次只改一个变量。

来源：
- https://help.runwayml.com/hc/en-us/articles/46974685288467-Creating-with-Gen-4-5
- https://help.runwayml.com/hc/en-us/articles/48324313115155-Image-to-Video-Prompting-Guide
- https://help.runwayml.com/hc/en-us/articles/47313737321107-Text-to-Video-Prompting-Guide
