# Context Kernel Handoff — Teleiosis v0.0.0.3

```yaml
product: Teleiosis
version: v0.0.0.3
internal_revision: v0.0.0.3-r5-clean-universal
identity: teleiosis
scope_mode: FULL_NO_ROUTING
round: T1 -> C1 -> S1 -> C2 -> P1 -> C3
group: 3 rounds
run: 3 groups
candidate_semantics: C is the evolving iteration object itself, not a fixed SHA checkpoint
base_genesis_sha256: 14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086
effective_genesis_sha256: 65e5cd626836d7d76c753360977baa49a6b0f096a430d49222a5c25bed51248f
canonical_skill_archive: Teleiosis-v0.0.0.3-skill.zip
fixed_repo_sha_precondition: false
fixed_file_sha_precondition: false
fixed_overlay_sha_precondition: false
real_market_evidence: NOT_CLAIMED
formal_independent_review: UNAVAILABLE_NOT_CLAIMED
final_promotion_authority: external verifier on frozen Candidate
```

## 不可丢失的决策

- T/S/P 是一个 Registry Skill 内的三个全量模块，不使用 Router；
- T 的实现复用父 Skill canonical engine，不保留第二套旧源码；
- S/P 只供证，不得自行输出最终 PASS；
- Candidate 修改、Evidence、Manifest、revision 与公开状态采用事务边界；
- 移动 main 采用 fresh clone、语义适配、非 force push、竞态重试与 readback；
- 模拟、Fixture、压力流量和 LLM judge 不冒充真实市场或 Field。
