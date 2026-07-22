# SkillOps Auto draft contracts

State: `DRAFT_NON_ACTIVE`.

This directory owns eight public schemas and four Auto-private schemas. The
public set completes the shared contract only after Mechanism M0b constructs a
candidate manifest and digest. The private set is never a shared-bundle member.

Deterministic entrypoints:

```bash
/usr/bin/python3 -B CodexSkills/auto/tools/build_schemas.py --check
/usr/bin/python3 -B CodexSkills/auto/tools/validate_auto.py lint-draft
/usr/bin/python3 -B -m unittest \
  CodexSkills.auto.tests.test_auto_contract
```

Both tools import the repository-pinned canonicalizer and offline validator
from `CodexSkills/governance/tools/`. They do not implement JCS independently,
resolve schemas over the network, or install dependencies at runtime.
