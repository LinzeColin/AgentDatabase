# Veo 3.1 Adapter

状态：`ACTIVE_OFFICIAL`；核验日期：2026-08-17。

Google 官方模型页将 Veo 3.1定位为高端电影叙事、4K 输出、原生同步音频和复杂相机运动模型。具体分辨率、时长和输入控制以当前 API/产品界面为准。

## Prompt 顺序

```text
shot type and camera
subject and visible action
environment and spatial relation
lighting, palette and material
temporal progression
foreground sound / ambience / dialogue / score policy
stable end state
```

短镜头仍限制一个主要相机运动。原生音频能力不代表可以省略音频方向；明确现场声、台词和是否需要配乐。

来源：https://ai.google.dev/gemini-api/docs/models/veo-3.1-generate-preview
