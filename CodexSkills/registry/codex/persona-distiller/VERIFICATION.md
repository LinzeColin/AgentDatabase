# Release verification — Persona Distiller v0.0.0.3

Date: 2026-07-23

## Result

**PASS** — builder/runtime framework release gates completed.

## Automated evidence

| Gate | Result |
|---|---:|
| Offline unit/integration/concurrency tests | 43 / 43 passed |
| Standalone suite runtime | 10.898 seconds |
| Final checksum-aware self-check runtime | 11.190 seconds |
| Reviewer Round 1 | 6 roles, 24 / 24 checks passed |
| Reviewer Round 2 | 6 roles, 39 / 39 adversarial checks passed |
| JSON Schema files | 13 valid Draft 2020-12 documents |
| Python scripts covered by syntax check | 23 |
| Root `SKILL.md` progressive-disclosure ceiling | passed; under 500 lines |
| Secret-pattern scan | 0 findings |
| Target-package deterministic rebuild | passed |
| Target-package checksum tamper rejection | passed |
| Target runtime counter reset on publication | passed |
| Concurrent invocation serial allocation | unique and contiguous |
| Snapshot/diff/verify/rollback | passed |
| Seven-category persona registry | 7 / 7 category manifests valid |
| Cross-category persona uniqueness | subject UID, canonical key, and ZIP hash hard gates passed |

## Runtime version cases exercised

- identity menu and invalid identity do not consume a serial;
- first accepted invocation is `0.0.0.1`;
- failed runs remain immutable and consume their serial;
- next accepted run advances normally;
- `0.0.0.999` formatting and allocation;
- explicit override requires both user-intent flag and a value greater than all history;
- stale started calls recover to failed without reuse;
- state lagging a committed run directory is reconciled;
- concurrent processes allocate no duplicate serials;
- result files receive logical versioned names and SHA-256 entries.

## Privacy and supply-chain cases exercised

- Holdout source IDs cannot be promoted into model Claims;
- target runtime ZIP excludes raw data, source bodies, Holdout bodies, and prior runtime history;
- private target source locators are sanitized;
- source and installed-copy checksum verification;
- empty/duplicate/path-escaping checksum entries are rejected by the verifier contract;
- tampering with a packaged target file blocks installation;
- package top-level count is one;
- secret-like credentials are a release hard failure.
- one released persona ZIP is routed to exactly one category;
- multi-identity output is routed only to `多重身份/`;
- private/self products are rejected from the public GitHub registry;
- repeat registration of the same model version and hash is idempotent;
- the generated persona index must equal the canonical registrations.

## Fresh-package end-to-end smoke

A new temporary directory was used to extract the final candidate ZIP. The extracted package then:

1. verified all 204 listed immutable payload checksums plus the separately validated mutable product index;
2. installed to a clean custom Skill path;
3. verified both source and installed copies and passed post-install self-check;
4. initialized a weighted `技术工程师 70% + 开发设计家 30%` target without a scenario input;
5. inferred `product-creation` and `research-problem-solving`;
6. allocated `0.0.0.1`;
7. completed the run and recorded `result-v0.0.0.1.md` plus SHA-256 metadata;
8. verified runtime history/state consistency;
9. uninstalled cleanly.

The final local installation additionally verified the builder at
`~/.codex/skills/persona-distiller`, confirmed no same-name source under
`~/.agents/skills`, and passed the post-install self-check.

## Review-method limitation

The environment did not provide a genuine independent SubAgent execution tool. The two review rounds therefore use six isolated domain reviewer protocols backed by deterministic checks. They are not represented as six independently sampled models.

## Scope limitation

This verifies engineering behavior and release integrity. It cannot establish fidelity to a particular real person until that target has a lawful source corpus, frozen unseen evaluation material, and independent behavior judging.
