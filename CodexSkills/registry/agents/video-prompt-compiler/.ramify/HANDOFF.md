# HANDOFF — Video Prompt Compiler v0.0.0.2

## To

Codex 最后一公里执行会话

## Result

`PROPOSED_NOT_COMMITTED`

## Destination

```text
LinzeColin/AgentDatabase/CodexSkills/registry/codex/video-prompt-compiler/
```

## Read First

1. `README_FIRST.md`
2. `SKILL.md`
3. `research/comparison_matrix.md`
4. `taskpack/CODEX_EXECUTION.md`
5. `taskpack/ACCEPTANCE.md`
6. `taskpack/TEST_RESULTS.md`

## Key Changes from v0.0.0.1

- VideoPromptIR；
- 双候选与 15 维评分；
- 结构证据与真实生成证据分离；
- 当前模型注册表与独立适配器；
- 工业物理账本；
- 人物连续性、剧本分镜和确定性剪辑路线；
- 旧/未知模型标签降级为 RETIRED 或 VERIFY_AT_RUNTIME。
- 中文真实素材剪辑路由与源/目标双时长解析；
- 包清单验证 PASS，Unit/Regression 52/52 PASS，安装保留完整治理与研究文件；压缩包独立解压复跑 52/52 PASS。

## Hard Boundaries

不覆盖现有 Skill；不引入密钥/收费生成；不把本地测试称为外部 PASS；不改变 NOT_RUN；不重新研究或重写产品。

## Next Single Action

严格执行 `taskpack/CODEX_EXECUTION.md`：落库、运行验证、commit、push、PR/merge、回报事实。
