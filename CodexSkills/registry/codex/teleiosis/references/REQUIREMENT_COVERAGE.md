# Genesis Requirement Coverage

Formal promotion is not inferred from one score. `evidence/validation/requirement-coverage.json` must contain `WBI-GB-001` through `WBI-GB-027` exactly once, in locked Genesis order and bound to the run's Baseline ID, locked Genesis SHA-256 and `valid_as_of` date.

Each record contains:

- `id`;
- `status`: `PASS`, `BLOCKED`, `UNKNOWN` or `FAIL`;
- one or more immutable evidence bindings: path/reference, SHA-256 and byte size where applicable;
- residual unknowns.

The trusted gate re-hashes local evidence; a summary, score, assertion or unbound path cannot replace the raw result. Any non-PASS requirement blocks **formal promotion**. Engineering packaging may still be truthful and installable when an external capability is unavailable, but the receipt must separate `engineering_release_status` from `autonomous_promotion_status`.

## WBI-GB-019 special rule

The 2×6 requirement can be `PASS` only when the frozen external review-attestation adapter validates twelve unique reviewer receipts plus a distinct thirteenth read-only verifier. Local capability claims, fallback role reviews, fixture receipts and self-authored IDs remain useful diagnostics but must map WBI-GB-019 to `BLOCKED`, not PASS.

This file is an evidence-routing guide, not a second editable copy of Genesis. The authoritative language remains `constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md`.
