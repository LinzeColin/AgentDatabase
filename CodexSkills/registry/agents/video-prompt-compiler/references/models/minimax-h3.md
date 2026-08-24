# MiniMax H3 Adapter

状态：`ACTIVE_OFFICIAL`；核验日期：2026-08-17。

官方信息显示 H3 接受文字、图片、视频和音频上下文，生成原生立体声视频，支持多镜头、参考、编辑与运动迁移。关键不是堆摄影词，而是用自然语言描述“哪个上下文负责什么、目标视频如何变化”。

## Base 模式

T2VA 默认结构：

```text
integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...
```

I2VA / FL2VA / L2VA 需要使用官方指南要求的首帧/末帧对齐语句；时间点必须在有效时长内。

## Full-reference 模式

```text
subject_definitions:
...

summary:
...

retention_analysis:
...

detailed_description:
...

overall_soundscape:
...

non_diegetic_music:
...
```

Reference 类型：`<Subject N>` 可复用主体/运动/表演；`<Picture N>` 具体帧；`<Video N>` 整段编辑/相机/时间结构；`<Audio N>` 声音复制或参考。

每个标签必须有定义、保留分析和实际使用位置。动作参考来自视频时，应把表演/运动定义为 Subject；整段视频的镜头路径、剪辑与节奏才由 Video 关系承担。

精确台词保持用户原文，不自动改写。时长、比例、分辨率作为界面参数，只有时间戳和关键帧对齐需要写进正文。

来源：
- https://www.minimax.io/blog/minimax-h3
- https://huggingface.co/MiniMaxAI/MiniMax-H3
