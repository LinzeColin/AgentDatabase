# Seedance 2.0 Adapter

状态：`ACTIVE_OFFICIAL`；核验日期：2026-08-17。

官方发布信息：支持文字、图片、音频、视频四种输入，具备多模态参考、编辑、延长、联合音视频和多镜头能力；官方强调复杂动作、物理准确性与可控性。

## Reference 编译

先写每个素材角色：

```text
Image 1 defines identity and wardrobe.
Video 1 provides performer motion only.
Video 2 provides camera path and edit rhythm only.
Audio 1 provides voice timbre.
```

再写目标场景、时间节拍、动作与相机、声音、结束状态和不变量。

## 工业任务

显式写工具—工件关系、夹持/轴线、接触或固定间距、轨迹、材料响应和最终状态。复杂物理场景仍需真实参考和结果观看，不能因官方强调“物理准确”而跳过验证。

## Edit / Extend

Edit：明确严格编辑哪个视频、保留项、只修改项、时空范围和禁止改变项。

Extend：从最后已确认状态继续，只增加一个主事件，保持身份、空间、光向、速度和声音。

来源：https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0
