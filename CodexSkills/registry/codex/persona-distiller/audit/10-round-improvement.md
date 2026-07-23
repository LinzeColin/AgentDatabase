# Ten-round improvement record

Each round started from a failure mode, changed executable behavior or release gates, and added a reproducible acceptance check. These are implementation rounds, not ten restatements of the prompt.

| Round | Failure mode | Material change | Acceptance evidence |
|---:|---|---|---|
| 1 | Required inputs and the earlier identity taxonomy were ambiguous | Frozen input contract: target name + seven-choice identity; scenario optional | identity registry/parser and CLI tests |
| 2 | Multi-identity weights could be malformed, silently averaged, or conflict | Alias/number/JSON parsing, normalization, conflict-aware primary routing, invalid-weight rejection | single/multi/percent/normalization tests |
| 3 | Persona could merely imitate speech instead of completing work | Added facts, cognition, decision policy, strategy, capability, Work, Persona, negative capability, task adapters, and plan/act/verify/record loop | target Skill contract and router tests |
| 4 | “Full-source research” had no auditable stopping condition | Added source universe, six lanes, identity-specific source topology, coverage cube, origin clustering, gap expansion, and two-round saturation | generated research artifacts and strict quality checks |
| 5 | Facts, competence, style, psychology, and role could contaminate each other | Separated model layers, identity facets, divergence map, and quarantined hypotheses; established precedence | required model files, Claim links, model-separation review |
| 6 | Runtime learning could overwrite the person and cause drift | Separated stable semantic model, procedural memory, episodic runs, user overlay, corrections, and promotion queue | package reset, memory firewall, correction and rollback tests |
| 7 | Voice similarity and target-name leakage could masquerade as fidelity | Expanded to 16 suites: anonymous, baseline, foil, task completion, planning, tool use, capability, stop/refusal, long-horizon, identity routing, token efficiency, and others | suite registry, blind packet, leakage hard-fail, aggregate tests |
| 8 | `0.0.0.N` could collide, be reused after failure, or diverge after a crash | OS file lock, atomic pending-directory commit, history/state reconciliation, stale-run recovery, immutable terminal records, artifact manifests, explicit override audit | first/failed/999/override/recovery/reconciliation/concurrency tests |
| 9 | Legacy install paths, duplicate sources, oversized context, and permissive activation wasted tokens or caused host ambiguity | Codex-only `.codex/skills`, cross-source duplicate refusal, only `name`/`description` frontmatter, explicit invocation, minimum-file runtime router, no raw corpus preload | install/frontmatter/router/self-check tests |
| 10 | Delivery could leak source bodies, accept corrupted installs, or contain stale build debris | One-top-level deterministic ZIP, raw/Holdout/runtime-history exclusion, source sanitization, secret scan, non-empty/no-duplicate checksums, source and installed-copy verification, clean extraction/install smoke test | deterministic package, tamper rejection, clean install and final release verification |

## Result

The framework passes 41 offline unit/integration/concurrency tests. This validates the builder, source/Claim contracts, runtime ledger, packaging, installation, corrections, rollback machinery, and seven-category unique product registry. It does **not** claim behavioral fidelity for a specific person before lawful target-specific research, frozen Holdout data, and independent evaluation are completed.
