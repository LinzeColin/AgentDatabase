# Agentic runtime

## Per-invocation state machine

`WAIT_IDENTITY → ALLOCATED → PLANNED → ACTING → VERIFYING → COMPLETED|FAILED`

Identity questions do not consume a serial. `begin` atomically consumes `0.0.0.N`; terminal failures keep it. A run directory is immutable except the single transition from `started` to one terminal status.

## Execution quality

The target model influences what to notice, how to decompose, which options to generate, what evidence to seek, how to use tools, when to stop and how to communicate. It does not manufacture tool access, current facts or domain expertise.

Before acting: identify objective, constraints, reversibility, unknowns, required tools and success checks. During action: use the host's real tools and record material assumptions. After action: verify outputs, facts, safety, target-model consistency and counterarguments.

## Token discipline

The router returns only required files. Do not preload source bodies, all identity facets, all run history or full evidence ledgers. Retrieve source/Claim detail only for audits, citations, contested reasoning or high-stakes checks.

## Output artifact contract

Every accepted invocation receives one immutable `0.0.0.N`. The final chat response displays `运行版本：0.0.0.N`; newly created files use `-v0.0.0.N` when practical. `runtime/runs/0.0.0.N/artifact-manifest.json` records status, logical versioned names and hashes. A failed or interrupted invocation keeps its serial.

Use `invocation_manager.py recover --older-than-seconds N` to close stale started runs after a crash; never delete and reuse them.
