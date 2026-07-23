# Promoted AU-040 public schemas

State: `DRAFT_NON_ACTIVE_SCHEMA_PROMOTED`.

This stable sibling root contains exact-byte copies of the four Auto transport
schemas accepted by the Mechanism interface at
`CodexSkills/governance/au040/semantic-policy-acceptance.json`.

The machine evidence is `promotion-interface.json`. It binds:

- the immutable draft interface and its verified Git object;
- the Mechanism acceptance interface and its raw SHA-256;
- each draft path, final path, raw-byte SHA-256, canonical schema SHA-256,
  self-digest pointer, and replacement relationship;
- all seven Mechanism production semantic guard codes;
- the historical 29-schema / five-policy candidate and the Auto promotion
  object that preserved its manifest bytes;
- the later target of 31 schemas / five policies.

Run the deterministic promotion gates from the repository root:

```bash
/usr/bin/python3 -B \
  CodexSkills/registry/auto/tools/build_schema_promotion.py --check
/usr/bin/python3 -B \
  CodexSkills/registry/auto/tools/validate_schema_promotion.py lint-promotion
/usr/bin/python3 -B -m unittest discover \
  -s CodexSkills/registry/auto/tests -p 'test_schema_promotion.py'
```

These files are intentionally outside the recursive `schemas/public/` loader
used by the historical candidate. Promotion validation reads that 29/5
manifest from the pinned candidate and promotion Git objects; it does not
require a later working tree to remain 29/5. The files are ready only for the
next Mechanism-owned candidate, consumer, and activation-control
materialization phase. This promotion does not bind a repository runtime,
create a bundle, integrate a publisher or writer, create
`CodexSkills/VERSION`, activate, or permit canonical publication.
