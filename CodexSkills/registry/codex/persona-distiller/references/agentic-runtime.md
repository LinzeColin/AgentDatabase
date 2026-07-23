# Agentic runtime

## Direct invocation state machine

`RECEIVED → INTERNAL_ROUTE → PLANNED → ACTING → VERIFYING → COMPLETED|FAILED`

The caller invokes the installed person Skill and states a task. The Skill must not ask for an identity, number, or weight. It automatically selects or combines distilled identity facets and infers scenarios from the task. Identity categories remain internal routing and product-registration metadata.

## Execution quality

The target model influences what to notice, how to decompose, which options to generate, what evidence to seek, how to use tools, when to stop and how to communicate. It does not manufacture tool access, current facts or domain expertise.

Before acting: identify objective, constraints, reversibility, unknowns, required tools and success checks. During action: use the host's real tools and record material assumptions. After action: verify outputs, facts, safety, target-model consistency and counterarguments.

## Token discipline

The router returns only required files. Do not preload source bodies, all identity facets, all run history or full evidence ledgers. Retrieve source/Claim detail only for audits, citations, contested reasoning or high-stakes checks.

## Output and audit contract

Invocations have no version number. Do not display a runtime version, append `0.0.0.N` to files, or create numbered run directories. `0.0.0.N` is reserved for successfully registered person-Skill products.

When audit or memory is useful, append one optional unnumbered record after completion or failure with `runtime_recorder.py`. Store the task hash by default, not task content. Record timestamps, internal routing summary, status, result summary, and result hashes without a serial or run version.
