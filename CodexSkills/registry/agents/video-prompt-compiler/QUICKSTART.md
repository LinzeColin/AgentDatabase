# Quick Start v0.0.0.2

## 1. 自然语言直接变成模型 Prompt

```text
$video-prompt-compiler
把下面自然语言编译为 Runway Gen-4.5 的 8 秒 I2V Prompt：产品图保持结构和文字不变，镜头慢慢环绕，金属表面反射随角度变化，最后停在正面英雄构图。只给最终 Prompt、参数和评分。
```

## 2. 工业级镜头

```text
$video-prompt-compiler
机器人熔覆头沿固定夹持的十字轴曲面匀速移动。把这句话编译为 Seedance 2.0 Prompt。补齐工具—工件关系、固定间距、作用区域、材料响应、车间声和结束状态，但不要编造温度、硬度或效果参数。
```

## 3. 人物微表演

```text
$video-prompt-compiler
女生听到“我们到这里吧”后没有立刻哭，只是呼吸停半拍、视线躲开、下颌收紧，最后重新看向对方。编译为 Kling VIDEO 3.0 的 10 秒单镜头 Prompt。
```

## 4. 多参考素材

```text
$video-prompt-compiler
Image 1 锁定人物脸和服装，Video 1 只提供走路动作，Video 2 只提供低机位跟拍，Audio 1 提供对白音色。编译为 MiniMax H3 full-reference Prompt。
```

## 5. 真实素材剪辑

```text
$video-prompt-compiler
我有现场原片。输出 40 秒竖屏企业片的素材角色表、EDL、字幕/旁白/现场声、缺失镜头和 MiniMax Design 总控 Prompt。真实项目镜头不得被 AIGC 替换。
```

## 6. 优化已有 Prompt

```text
$video-prompt-compiler
优化下面 Prompt：先保留所有硬约束，再生成 Precision / Expressive 两版，按 15 维百分比评分择优，只输出选中版和差异说明。
```

## 7. 修复失败结果

```text
$video-prompt-compiler
原结果中工件几何漂移、工具与表面距离不稳定。保留构图、时长和灯光，只修改几何锁定与轨迹，输出一个最小 Delta Prompt。
```

命令行辅助：

```bash
python3 scripts/route_request.py --text '需求' --format markdown
python3 scripts/compile_request.py --text '需求' --format json
python3 scripts/score_prompt.py --file prompt.md --source-idea '原需求'
```
