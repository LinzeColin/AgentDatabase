# 示例：十字轴激光熔覆

## 用户口语

```text
做一个十字轴激光熔覆镜头，要真实、高级、有工业电影感，机器人动作自然，火花别太假。
```

## 编译判断

- 路线：若有工件图片，优先 Image-to-Video；若有真实动作视频，优先 Reference-to-Video；纯文字只是最后选择。
- 主预设：industrial
- 辅预设：brand
- 目标模型：Seedance 2.0 / MiniMax H3
- 建议时长：6–8 秒

## Seedance / 通用多参考可复制 Prompt

```text
使用图片 1 锁定大型钢制十字轴的几何结构、表面状态、夹持位置和车间环境；使用视频 1 只参考机器人末端的匀速轨迹、动作节奏和摄像机轻微跟随，不继承视频 1 中的工件外观。

生成一个连续的 8 秒工业实拍质感镜头。近景侧前方机位，固定夹持的十字轴占据画面中央，机器人激光熔覆头沿已标记的磨损曲面从左向右匀速移动。熔覆头与工件表面始终保持稳定间距，工具中心线沿曲面连续推进；熔池只在实际作用区域形成，少量橙色火花和细微烟气沿运动反方向自然散开，不出现爆炸式粒子。摄像机前 2 秒稳定建立工件、夹具与机器人之间的空间关系，2–7 秒以极缓慢的侧向跟随保持熔覆头和熔池同时清晰，最后 1 秒停止移动并停在新形成的连续熔覆带特写。

真实重工业车间，石墨灰和钢铁本色，熔池暖橙色为唯一强调；材料表面保留加工痕迹和真实反射，光源方向保持稳定。声音为低沉车间底噪、机器人伺服运动和轻微金属加工声，无旁白、无音乐、无文字。

十字轴几何结构、轴线、夹持位置和机器人外形全程保持不变；不新增零件，不发生穿模、漂浮、整体熔化或工具位置跳变。镜头结束时机器人停在工件右侧，工件仍稳定固定。
```

## MiniMax H3 可复制 Prompt（Base T2VA Schema）

> 下列版本不使用参考素材；如需图片/视频参考，应改走 H3 full-reference 六段 Schema，而不是在 Base Prompt 里口头写“图片 1 / 视频 1”。

```text
integrated_multimodal_description: [Shot 1] A high-trust industrial live-action scene inside a real heavy-machinery workshop. A large steel cross shaft is rigidly clamped at the center of frame, viewed from a close three-quarter side angle. A robotic laser-cladding head advances from left to right along the worn curved surface at constant speed. The tool centerline follows the curvature continuously while the stand-off distance remains stable. A compact molten pool forms only at the active contact zone; a small quantity of warm orange particles and thin process smoke trail naturally opposite the travel direction, with no explosive spray. The camera first establishes the spatial relationship among the cross shaft, fixture, and robot, then performs one very slow lateral tracking move that keeps the cladding head and molten pool simultaneously readable. Graphite gray and natural steel dominate the palette; restrained warm orange from the process is the only accent. Surface machining marks and physically plausible reflections remain visible. The cross-shaft geometry, axis, fixture position, robot shape, light direction, and travel direction remain unchanged. No added components, penetration, floating, whole-part melting, or position jumps. In the final second, the robot decelerates and stops at the right side while the camera holds on the newly formed continuous cladding band and the workpiece remains firmly fixed.

overall_soundscape: Low heavy-workshop ambience, restrained servo motion, and light metal-processing sound synchronized with the moving cladding head. No narration and no spoken dialogue.

non_diegetic_music: N/A
```

## 界面参数

- 画幅：9:16
- 时长：8 秒
- 第一轮：Fast / Draft，只生成 1 个版本
- 通过结构与动作后再升级最终模型
