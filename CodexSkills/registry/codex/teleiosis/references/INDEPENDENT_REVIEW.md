# Independent Review

Formal promotion requires **two panels × six genuinely independent SubAgents**, followed by a distinct thirteenth read-only verifier. Role-play, repeated calls in one context, locally invented actor IDs, or a JSON file written by the Candidate do not prove independence.

## Frozen external attestation contract

At `init-run`, a formal run may receive `--review-attestation-contract /absolute/path/contract.json`. The contract is copied into the control plane and bound by the immutable run seal before Candidate changes. It must point to:

- an absolute runtime adapter executable outside the workspace, target and optimizer roots;
- the adapter's expected SHA-256;
- an external receipt root outside Candidate-visible paths;
- declared capabilities `independent-subagents` and `read-only-verifier`;
- provider/runtime identity and isolation semantics.

The trusted stable runner invokes the adapter without a shell and with a minimal environment. All twelve reviewer receipts and the final-verifier receipt are checked in one batch call against the frozen packet hashes, actor/context/provider-run IDs, evidence hashes and receipt root. Local `runtime-capability.json`, self-signed receipts, or Candidate-authored attestations cannot satisfy the gate.

## Panel structure

**Panel 1:** competitive research; architecture; evaluation science; safety/governance; runtime/install; efficiency/maintenance.

**Panel 2:** red team; ambiguity/triggering; overfitting/negative transfer; recovery/rollback; long-horizon drift; governance boundary.

Each reviewer receives one immutable evidence packet, no preferred verdict and no earlier reviews. Records require unique actor ID, context ID and provider run ID, runtime/model, packet hash, evidence paths, findings, confidence and unknowns.

## Decision rule

- all twelve independent submissions must be present and externally attested;
- one actor/context/provider run cannot fill multiple seats;
- unresolved `CRITICAL`, or hard-domain `HIGH`, findings block;
- soft strategic or aesthetic dissent remains visible and does not force lowest-common-denominator design;
- the thirteenth verifier must be a distinct actor/context/provider run, remain read-only and assess the frozen evidence rather than modify the Candidate;
- missing trusted adapter capability returns `INDEPENDENT_REVIEW_UNAVAILABLE / BLOCKED`—never a simulated PASS.

Provider attestation reduces, but cannot mathematically eliminate, provider dishonesty. The residual trust boundary must remain explicit in the final receipt.
## Evidence-index preflight

Before any immutable review packet is created, Teleiosis resolves every role-specific and default evidence path, reports the complete missing/unsafe set in one fail-closed diagnostic, and writes zero packets on failure. This avoids partial plans and repeated one-path-at-a-time reruns while preserving exact content-hash binding.

