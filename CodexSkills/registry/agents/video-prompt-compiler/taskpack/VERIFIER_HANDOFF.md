# External Verifier Handoff

Subject: `video-prompt-compiler v0.0.0.2`

Current status: `INSTALLABLE_CANDIDATE / EXTERNAL_PASS_NOT_ISSUED`

独立检查：

1. 路由是否避免 T2V/剪辑/I2V/Reference 混淆；
2. IR 是否真正保护硬约束；
3. 双候选是否产生实质差异而非同义改写；
4. 评分是否可解释、硬门槛是否优先；
5. 模型适配是否符合 2026-08-17 当前官方资料；
6. H3 Full-reference、Runway I2V、LTX 长度等特殊规则是否正确；
7. 工业物理是否包含因果、轨迹、材料反馈和最终不变量；
8. 人物微表演是否包含触发、反应延迟和余韵；
9. Reference/人物连续性是否依赖明确素材角色；
10. 结构分是否与真实生成证据严格分离；
11. 安装是否不破坏现有 Skill；
12. 是否存在第三方文字/代码直接复制或许可证越界。

建议盲测：6 工业、6 人物、3 产品 I2V、3 Reference、3 素材剪辑、2 剧本分镜、3 失败修复。正式 PASS 必须由独立上下文产生。
