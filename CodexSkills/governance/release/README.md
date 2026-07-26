# SkillOps release foundations

Status: **DRAFT_NON_ACTIVE_POLICY_RECONCILIATION_REQUIRED**

This directory owns deterministic Mechanism semantics for Task Pack M-004,
M-005, M-006, M-008, and M-009:

- unbounded `v0.0.0.n` parsing, comparison, and increment;
- a single-flight revision allocation ledger whose reserved or abandoned SRV
  can never be reused;
- exact settlement checks binding VERSION bytes, all artifact SRVs, and an
  advanced remote readback head;
- ROUTINE/MATERIAL/MAJOR to PATCH/MINOR/MAJOR compatibility without treating
  SRV as SemVer;
- locked-trigger impact classification with unknown codes failing closed;
- sanitized policy-precedence conflicts that expose source and value digests,
  never raw values;
- a machine-readable Handoff whose stale head/SRV/bundle, missing evidence,
  unresolved policy, schedule, or external readiness blocks activation.

`foundations.py` is pure. It does not persist the ledger, create
`CodexSkills/VERSION`, write Git, send notifications, or touch runtime state.
The externally coordinated executor remains separately owned and must persist
the ledger before any planned write, then satisfy the existing activation
settlement.

The current v2 version policy does not enumerate six Owner-locked MAJOR
triggers. `foundation-interface.json` records that exact conflict and therefore
sets `release_write_permitted=false`. The three schemas in this directory are
not candidate-bundle members; adding them or a replacement version policy to a
future bundle requires a separate consumer-first coordinated Phase.

Validate from the repository root:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_release_foundations.py --check
/usr/bin/python3 -B CodexSkills/governance/tools/validate_mechanism.py \
  lint-schema-set \
  --schema-dir CodexSkills/governance/schemas \
  --schema-dir CodexSkills/governance/release/schemas
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_release_foundations
```
