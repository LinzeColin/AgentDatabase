# SkillOps Mechanism governance

Status: **DRAFT_NON_ACTIVE**

This directory is the Mechanism half of the SkillOps v0.0.0.3 contract. It
contains only Mechanism-owned schemas, policy instances, deterministic
canonicalization, offline validation, provenance, fixtures, and tests. It is
not an active release and is not a second Registry or run-log fact source.

Key entrypoints:

- `tools/canonical_json.py`: strict I-JSON input and RFC 8785 canonical bytes.
- `tools/validate_mechanism.py`: unique offline schema/policy/artifact gate.
- `tools/build_draft.py`: deterministic materialization and byte check.
- `tests/test_mechanism_contract.py`: positive, negative, and fault gates.
- `draft-interface.json`: exact M0a interface for Auto A1a.

Run from the repository root with the explicitly provisioned interpreter:

```bash
/usr/bin/python3 -B CodexSkills/governance/tools/build_draft.py --check
/usr/bin/python3 -B CodexSkills/governance/tools/validate_mechanism.py lint-draft
/usr/bin/python3 -B CodexSkills/governance/tools/validate_mechanism.py \
  lint-schema-set --schema-dir CodexSkills/governance/schemas
/usr/bin/python3 -B -m unittest discover \
  -s CodexSkills/governance/tests -p 'test_*.py'
```

No command in this directory downloads dependencies or resolves schemas over
the network. The first active bundle is assembled only after Auto A1a lands
its owned schemas and tests.

Runtime artifacts are validated only against a caller-selected trusted schema
ID and external expected bundle digest. Candidate/ACTIVE bootstrap additionally
requires a repo-external tuple of verified Git object ID, expected bundle
digest, canonical manifest path, and mode. Losing that external state fails
closed; the current checkout cannot promote its own manifest to trusted.
