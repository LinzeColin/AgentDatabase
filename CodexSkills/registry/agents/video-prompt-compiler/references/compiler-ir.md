# VideoPromptIR 0.2

## 目的

同一个创意在 H3、Seedance、Kling、Veo、Runway、Wan、LTX 上需要不同表达。IR 将“创意与事实”从“厂商语法”中分离，避免一个 Prompt 到处复制。

## 核心结构

```yaml
ir_version: 0.2
constraint_ledger:
  locked_facts: []
  creative_space: []
  unknowns: []
  forbidden: []
production:
  method: text_to_video | image_to_video | reference_to_video | video_edit | ...
  source_duration_seconds: null   # 仅真实素材/已有视频的输入时长
  duration_seconds: null          # 目标成片或生成时长
  aspect_ratio: null
  output_mode: copy | director | reverse | repair
assets:
  - id: Image1
    type: image
    role: identity_and_wardrobe
scene_ir:
  subject_anchor: null
  environment: null
  action_beats: []
  camera:
    shot_size: null
    angle: null
    primary_movement: null
    viewer_effect: null
  lighting_material_palette: {}
  audio:
    dialogue: []
    foreground_sfx: []
    ambience: []
    score_policy: null
  timeline: []
  end_state: null
  continuity_invariants: []
  physics_ledger: null
candidate_plan:
  precision_branch: ...
  expressive_branch: ...
  selector: ...
model_render:
  target_model: null
  adapter_path: null
  interface_parameters: {}
evidence:
  routing: EXECUTED
  structural_prompt_score: NOT_RUN
  native_model_generation: NOT_RUN
  human_visual_review: NOT_RUN
  external_verifier: NOT_RUN
```

## 时长语义

- `source_duration_seconds` 只记录已有素材/原片的长度；
- `duration_seconds` 只记录目标成片或目标生成时长；
- ‘40 秒素材剪成 18 秒’必须保留为 `source=40`、`target=18`；
- 只有输入素材长度、没有目标长度时，目标保持 `UNKNOWN`，不得静默复用源时长。

## 编译规则

1. `locked_facts` 不允许被候选改写；
2. `creative_space` 只加入可观察、无冲突细节；
3. `unknowns` 不填入确定性宣传；
4. `forbidden` 先于加权评分；
5. `scene_ir` 只包含跨模型语义，不包含厂商 API 字段；
6. `model_render` 才决定 H3 多段 Schema、Runway 简洁运动描述或 LTX 单段落等格式；
7. 生成结果产生后才改变 evidence 状态。

## 候选差异

Precision：最小充分、低歧义、低负载。

Expressive：增加叙事/感官价值，但必须复用同一事实层、动作预算和结束状态。

候选择优不得通过删除硬约束换取更高简洁度。
