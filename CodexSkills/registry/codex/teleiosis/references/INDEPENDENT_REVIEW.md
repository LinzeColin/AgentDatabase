# Independent Review

Formal promotion requires **two panels × six genuinely independent SubAgents**, followed by a distinct thirteenth read-only verifier. Role-play, repeated calls in one context, locally invented actor IDs, or a JSON file written by the Candidate do not prove independence.

## Frozen external attestation contract

At `init-run`, a formal run may receive `--review-attestation-contract /absolute/path/contract.json`. The contract is copied into the control plane and bound by the immutable run seal before Candidate changes. It must point to:

- an absolute runtime adapter executable outside the workspace, target and optimizer roots;
- the adapter's expected SHA-256;
- an external receipt root outside Candidate-visible paths;
- a pre-existing external Ed25519 public trust anchor and expected SHA-256;
- an isolation mode of remote provider, separate OS principal, or hardware-attested runtime;
- declared capabilities `independent-subagents`, `read-only-verifier`, and `provider-identifiable-runs`;
- provider/runtime identity and isolation semantics.

The signing private key must remain inaccessible to the Candidate. Each provider receipt is independently signed and binds packet index, provider, actor, context, provider run, provider request, round/seat, verdict, runtime/model and timestamps. The aggregate attestation is also signed. Reused identities, receipts, provider requests, paths, wrong signatures, hash drift or incomplete 2×6 coverage fail closed.

The bundled package contains only protocol, Schema, tests and diagnostic examples. A diagnostic fixture can prove parser and signature verification behavior but always returns `DIAGNOSTIC_ONLY`; it cannot satisfy formal review.

## Panel structure

**Panel 1:** competitive research; architecture; evaluation science; safety/governance; runtime/install; efficiency/maintenance.

**Panel 2:** red team; ambiguity/triggering; overfitting/negative transfer; recovery/rollback; long-horizon drift; governance boundary.

Each reviewer receives one immutable evidence packet, no preferred verdict and no earlier reviews. Records require unique actor ID, context ID, provider run ID and provider request ID, runtime/model, packet hash, evidence paths, findings, confidence and unknowns.

## Decision rule

- all twelve signed independent submissions must cover exactly rounds 1-2 and seats 1-6;
- one actor/context/provider run/request or receipt cannot fill multiple seats;
- unresolved `CRITICAL`, or hard-domain `HIGH`, findings block;
- soft strategic or aesthetic dissent remains visible and does not force lowest-common-denominator design;
- the thirteenth verifier must be a distinct actor/context/provider run, remain read-only and assess frozen evidence rather than modify the Candidate;
- missing trusted adapter, cryptographic verification dependency or real isolation capability returns `INDEPENDENT_REVIEW_UNAVAILABLE / BLOCKED` - never a simulated PASS.

Ed25519 proves receipt integrity and possession of the signing key; it does not mathematically prove organisational independence. The external provider/separate principal remains the explicit trust root and residual trust must remain visible in the final receipt.

## Evidence-index preflight

Before any immutable review packet is created, Teleiosis resolves every role-specific and default evidence path, reports the complete missing/unsafe set in one fail-closed diagnostic, and writes zero packets on failure. This avoids partial plans and repeated one-path-at-a-time reruns while preserving exact content-hash binding.
