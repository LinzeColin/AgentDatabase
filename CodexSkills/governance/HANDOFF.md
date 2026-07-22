# Mechanism handoff

- State: `DRAFT_NON_ACTIVE`
- Task Pack authority: immutable `CodexSkills-Mechanism-Design-TaskPack-v0.0.0.2`
- Protocol: `urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1`
- Mechanism schema owner: `CodexSkills/governance/schemas/`
- Mechanism policy owner: `CodexSkills/governance/policies/`
- Auto schema owner: `CodexSkills/auto/schemas/{public,private}/` (not present in M0a)

## Completed in M0a

- Mechanism schema IDs, policy instances, digest pointers, and compatibility
  boundary are materialized and validated offline.
- RFC 8785 canonicalization is pinned to a provenance-checked author reference
  implementation and wrapped by strict raw-byte I-JSON parsing.
- UTC-Z, UID, digest, Git OID, URN, enum, count, and repository-path semantics
  are shared through `common-definitions:v1`.
- Privacy, source material, retention, notification, and SRV/transaction
  separation are represented as bundle-member policies without a self-cycle.
- EvalProfile, EvalRun, Scorecard, PromotionEvidence, and PromotionDecision
  bind the seven scoring dimensions, eight non-waivable gates, five routing
  strata, calibration, critical incidents, sealed isolation, 2x2 attribution,
  shadow/canary evidence, rollback, and one-way notification semantics.
- `draft-interface.json` freezes all 29 shared schema IDs, single-owner planes,
  exact self-digest pointers, the five policies, and the four Auto-private
  schemas that can never enter the shared bundle.
- Negative fixtures prove fail-closed behavior for privacy, binding, schema
  resolution, timestamps, paths, canonicalization, and contextual digests.
- The A1a pre-write corrective gate explicitly admits only
  `adapter_schema_digest`, `included_tree_digest`, and
  `mapping_policy_digest` as additional public SHA-256 fields, and adds the
  closed `actor_role=UNKNOWN` value for observed CLAUDE/AGENTS activity whose
  actor role cannot be proven. `UNKNOWN_LEGACY` remains forbidden; the 18
  historical records remain unmapped and produce no run event.

## Explicitly not active

M0a does not create `CodexSkills/VERSION`, an active manifest, a complete
candidate bundle, a canonical event, a public receipt, or a watermark. No
runtime producer may consume this draft as ACTIVE.

## Next exact action

Auto A1a rebases its expected head to the verified M0a main SHA, adds only
Auto-owned public/private schemas and tests, and returns its verified main
SHA. Mechanism M0b then consumes both ownership sets and constructs the first
complete candidate manifest and digest without activating it.
