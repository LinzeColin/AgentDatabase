# Peer Taxonomy and Category-Error Control

## Why this exists

Repository names are not product categories. The URLs `Curzibn/Luban` and `EasyDarwin/EasyDarwin` point to an Android image-compression library and a streaming-media server, not Agent Skills. They are useful engineering analogies, but allowing either to satisfy the five-peer market gate would contaminate the comparison set.

Teleiosis therefore records two independent dimensions:

1. `category`: the legacy coverage role used by the five-peer protocol (`direct`, `indirect`, `craft`);
2. `comparison_scope`: why the evidence is comparable.

## Comparison scopes

| Scope | Meaning | Counts toward five market peers |
|---|---|---:|
| `direct-competitor` | Evolves, optimizes, assures, or productizes Agent Skills in substantially the same job-to-be-done | Yes |
| `adjacent-competitor` | Creates, validates, publishes, or operates Agent Skills but is not a full evolution control plane | Yes |
| `method-reference` | Supplies a transferable AI optimization/evaluation method with evidence relevant to the job | Yes, subject to the frozen peer contract |
| `engineering-analogy` | Different product category; contributes only a mechanism analogy | **No** |
| `out-of-scope` | Evidence is too weak or unrelated | No |

An analogy may enter the mechanism-adoption ledger, but cannot satisfy the five-peer gate or enter market-outcome counts, category coverage, stars comparisons, or “market first” claims.

## Command

```bash
python3 scripts/wbi.py peer-audit \
  --input templates/peer-audit-records.json \
  --output /absolute/external/peer-audit.json
```

The output separates `market_scope_candidate_ids`, production-qualified `market_peer_ids`, and `engineering_analogy_ids`; classification alone never qualifies a production peer. Duplicate identities fail closed.

## Evidence rules

- Name overlap is discovery-only.
- A real peer still needs reproducible evidence, provenance, licence status and an exact commit or live observation procedure.
- Metadata-only rows do not satisfy production peer selection.
- Third-party code is statically inspected by default; no execution is implied.
- Classification can be overridden only by an explicit, auditable `comparison_scope`; invalid values become `out-of-scope`.

## Exact-link treatment in this release

| Repository | Actual public project type observed 2026-07-26 | Teleiosis role |
|---|---|---|
| `https://github.com/Curzibn/Luban` | Android image compression | Engineering analogy: empirical frontier reconstruction, adaptive policy, larger-output fallback, input/OOM defence |
| `https://github.com/EasyDarwin/EasyDarwin` | Cross-platform streaming server | Engineering analogy: adapter matrix, on-demand operation, monitoring/control plane, platform diagnostics |
| `https://github.com/LearnPrompt/luban-skill` | Agent Skill productization/craft workflow | Direct market peer |
| `https://github.com/alchaincyf/darwin-skill` | Agent Skill optimization ratchet | Direct market peer |

This separation is a correctness mechanism, not a semantic preference.
