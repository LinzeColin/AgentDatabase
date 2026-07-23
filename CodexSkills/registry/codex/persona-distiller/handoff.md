# Handoff — 人物蒸馏 Skill / Persona Distiller v0.0.0.4

## 1. Builder contract

This package is the builder/orchestrator Skill. It accepts:

- target person's name;
- one of six primary build identities or a weighted multi-identity selection.

Scenario is optional. The builder performs evidence research, synthesis, evaluation, refinement, packaging, and unique registration.

Build identity menu:

1. 技术工程师
2. 创业经营家
3. 投资资本家
4. 开发设计家
5. 思想教育家
6. 政治法律家
7. 多重身份

Private/self/fictional/historical targets remain separate `subject_origin` governance modes. Private/self data still requires authority and retention controls.

## 2. Generated person-Skill runtime contract

An installed person Skill is directly callable:

```text
caller task → automatic internal identity/scenario route → minimum model load
→ plan → act with host tools → verify → deliver → optional unnumbered audit
```

- Never ask the caller to select an identity, number, or weight.
- Treat build identity and the seven registration folders as internal metadata, not runtime restrictions.
- Automatically select or combine only the distilled identity facets relevant to the task.
- Do not display a runtime version, append a version to output filenames, or create numbered run directories.
- Optional audit records contain timestamps, task hashes, internal route summaries, status, and result hashes. Task content remains opt-in.

## 3. Product version contract

`0.0.0.N` identifies published person-Skill products, not invocations.

- Each canonical person has an independent sequence.
- The valid range is `0.0.0.1` through `0.0.0.999`.
- Versions are contiguous; gaps, reuse, same-version/different-hash, and overflow are rejected.
- Packaging derives the next candidate number from the canonical registry.
- The number is consumed only when registration succeeds; failures do not consume it.
- A registry lock serializes concurrent writers on one machine.
- Repeated distillations of the same person append new product versions under the original canonical registration, even when an internal model snapshot label is unchanged.

## 4. Identity and registration

Released target-person ZIPs are registered exactly once under:

Skill 根级
`<技术工程|企业领导|金融投资|软开设计|思想教育|政治法律|多重身份>/`

Single-identity products use the matching folder. Weighted multi-identity products use only `多重身份`. A person must never be copied across categories; reclassification moves the canonical record.

Public GitHub registration rejects private/self products, raw materials, Holdout bodies, credentials, private source text, and secret-like content.

## 5. Version boundaries

- Builder release: `v0.0.0.4`.
- Internal model snapshot: research/correction lifecycle metadata only.
- Published person product: per-person `0.0.0.1..0.0.0.999`.
- Runtime invocation: unversioned.

## 6. Packaging and installation

Builder default and only user installation:

`~/.codex/skills/persona-distiller`

Do not keep a second source under `~/.agents/skills/persona-distiller`.

Builder and generated-person ZIPs have one top-level directory, checksums, installer metadata, no symlinks/caches, and privacy-minimized payloads. Generated-person packages reset runtime/episodic records but contain no invocation counter.

## 7. Verification gates

- full offline unit/integration/concurrency suite;
- strict target release quality gate;
- automatic runtime router and unnumbered audit tests;
- per-person first/next/999/exhaustion/gap/idempotence tests;
- deterministic target packaging and checksum-tamper rejection;
- seven-category uniqueness and generated-index validation;
- source and installed-copy checksum verification;
- reviewer rounds, schema parsing, syntax checks, secret scan, fresh extraction/install;
- repository README/index synchronization and remote GitHub verification.

## 8. Residual limits

- Target-specific fidelity remains unproven until lawful target research, frozen Holdout data, and independent judging are completed.
- Host models and tools differ; execution portability requires separate evaluation.
- The filesystem registry lock protects one machine. Multi-machine publishing still requires Git serialization or a transactional service.
- Deletion, paywalls, private archives, oral history, and undigitized sources prevent proof of absolute source completeness.

## 9. Core architectural insight

The durable artifact is a versioned person-product release backed by an evidence-grounded decision operating system and divergence map. Runtime calls are ordinary executions of that installed product; they are not new releases.
