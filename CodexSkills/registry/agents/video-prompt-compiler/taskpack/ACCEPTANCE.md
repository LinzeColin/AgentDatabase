# 验收标准 v0.0.0.2

## P0 — 必须通过

- 独立安装，不覆盖 `prompt-compiler`；
- 自然语言可路由到 T2V/I2V/Reference/Edit/Extend/Footage/Screenplay/2D/3D/True3D/Reverse；
- IR 保留事实、未知、禁止项、资产角色和证据状态；
- 真实素材路由必须区分源素材时长与目标成片时长，不能把源时长静默当作目标；
- 两个候选与硬门槛/多维评分合同完整；
- 模型注册表区分 ACTIVE、PLATFORM_VERIFY、RETIRED、VERIFY_AT_RUNTIME；
- 工业物理账本、微表演、人物连续性、EDL/分镜路线存在；
- H3、Hailuo、Seedance、Kling、Veo、Runway、Wan2.2、LTX-2 适配文件存在；
- 不把结构分写成真实视频质量；
- 不内置密钥、收费调用、用户素材或伪工程结论；
- 包内离线测试通过。

## P1 — 生产前证据

- 至少 2 个工业镜头、2 个微表演、1 个产品 I2V、1 个多参考、1 个素材剪辑项目的真实模型测试；
- 每例保存原需求、IR、两个候选、选择分、模型参数、成片、人工评分和 Delta；
- 多镜人物连续性在至少两种模型/工作流上盲测；
- 外部 Verifier 独立审查。

P0 通过只代表“可安装和可进入真实模型测试”，不代表 P1。
