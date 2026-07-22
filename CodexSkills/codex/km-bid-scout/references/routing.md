# Mode routing

| Mode | 最小链 | 降级/停止 |
|---|---|---|
| FULL_DISCOVERY | discover -> evidence -> adjudicate -> qualify -> audit -> brief | 源降级可继续；无官方证据只到 P2 |
| INCREMENTAL_DISCOVERY | discover -> evidence -> adjudicate -> qualify -> audit -> brief | 无 cursor 时不默认转 full，由 budget 决定 |
| EVIDENCE_BACKFILL | evidence -> adjudicate -> qualify -> audit -> brief | 不重跑无关来源 |
| DEADLINE_WATCH | evidence -> qualify -> audit -> brief | 只处理 deadline/version/动态证据变更 |
| AUDIT_ONLY | audit | 不加载前序自然语言辩护 |
| BRIEF_ONLY | brief | 仅接受已审计结构化决策 |
| DINGTALK_SYNC | lifecycle | DWS 任一前置不足即 BLOCKED |
| OUTCOME_WATCH | lifecycle -> brief | 无官方结果保持 OUTCOME_PENDING |
| EVOLVE_SHADOW | evolve | 不调用发布，不修改 ACTIVE |

路由器不隐式插入不在表中的 Skill。若新的业务需求需要改链，先更新契约和测试。
