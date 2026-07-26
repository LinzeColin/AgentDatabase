# Competitor Intelligence

## What counts as a peer

At least five unique real projects must qualify, with direct >=2, indirect >=1 and craft/infrastructure >=1. A qualifying record is either:

- `github-pulled-static`: canonical repository, exact 40-character commit and bounded static no-exec inspection;
- `product-live`: real product with observed artifacts and reproducible observation procedure;
- `artifact-bundle-live`: supplied real bundle with provenance and observation procedure.

Metadata, papers, articles, Issues, search results and local test fixtures cannot satisfy production peer quotas. Formal open-source runs require at least one real GitHub pull; the run may set a higher quota.

## Automatic GitHub pipeline

1. derive queries from target name/description/README;
2. add explicit seeds;
3. query GitHub API with dated provenance;
4. quarantine shallow clone with hooks/submodules disabled;
5. resolve exact commit and preflight file/byte limits;
6. materialize through `git archive` and a traversal/link-safe extractor;
7. inventory Skill files, README, license, CI, tests, scripts and real artifacts;
8. classify with evidence and allow a recorded human correction;
9. write JSONL dataset, selection, matrix and content hashes.

Pulled repositories are untrusted data. They are not installed, built or executed by default. Dynamic eval requires explicit authorization and an ephemeral no-secret/no-host-mount sandbox with allowlist, timeout and filesystem diff.

A network or permission failure remains `PULL_BLOCKED`; it never becomes a synthetic PASS.
