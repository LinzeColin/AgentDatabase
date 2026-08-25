# Current Environment、Evidence Lease 与 Reheat

每个正式 Run 在首次 Candidate 变更前及最终交付前各冻结一次环境快照。Candidate、Acceptance、Environment、Dataset 或 Toolchain 任一哈希变化，或租约到期/触发重大同行发布、模型变化、安全事件、Field 失败，旧证据立即 STALE/REHEAT_REQUIRED。`PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT` 只在固定比较集、同预算、无硬退化且所有证据域 PROVEN 时成立。
