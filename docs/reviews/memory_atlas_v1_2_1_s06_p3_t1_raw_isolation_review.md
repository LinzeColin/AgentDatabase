# Memory Atlas v1.2.1 S06-P3-T1 Raw Isolation Review

## Scope

- Task: `S06-P3-T1`
- Acceptance: `ACC-MA-V121-S06-P3-T1`
- Original TaskPack: `v1.2.1_四线16Stage质量收敛升级_TaskPack.zip`
- TaskPack SHA-256: `db59f4db3ac02845fb3cde346a301cba64146c81c7ba19168f52c27e82ddd0f1`
- Completed here: default raw exclusion for rg, Codex resource routing, root/project CI sparse checkouts, Vite resolution and production-dist validation.
- Excluded: `S06-P3-T2` push-size guard, `S06-P3-T3` full raw contract fixtures, raw/ledger/archive mutation, push, deploy, branch, PR, rebase and cache cleanup.

## Requirement Trace

- TaskPack `02_Roadmap_16Stage_Phase_Task.md` requires search, Codex routing, CI and frontend build to exclude raw bodies by default.
- The acceptance theme is low context cost: publishing raw must not make every development action scan raw.
- Stage validation requires the frontend production output to contain no public-raw body.
- The Task boundary keeps push-size governance and the complete append/dedupe/tamper/chunk/restore credential fixture matrix in T2 and T3.

## Contract And Implementation

- `config/data_sources/raw_isolation.json` is the canonical T1 contract for both `codexproject_monorepo` and `standalone_openaidatabase` topologies. It fixes forbidden raw roots, exact ignore rules, route policy, CI sparse patterns, Vite boundaries, dist checks and the next-Task boundary.
- Root and project `.rgignore` files exclude `data/public_raw/**` and `data/raw_archives/**` from normal rg traversal. Explicit `rg --no-ignore` remains available; isolation does not delete or make raw unrecoverable.
- `route_agent_resources.py` loads the contract before returning any of eight routes. A raw root in unconditional or conditional route paths fails closed, and successful output reports runtime enforcement.
- Both actual CI workflows use non-cone sparse checkout, omit both raw roots, set `MEMORY_ATLAS_RAW_ISOLATED=1` and run the raw-isolation audit. The root workflow also performs a fresh frontend install and production build.
- Vite uses the pre-enforced `memory-atlas-raw-isolation` plugin to reject raw-root IDs at resolve, load and transform boundaries. `publicDir` and `server.fs.allow` stay limited to the app and derived visualization data.
- The audit uses Git and path-only rg inventories. It never opens raw bodies. Built-dist files are opened with no-follow regular-file checks and a 64 MiB cap; byte-identical leakage is detected through the existing 512-row raw ledger hashes.

## Runtime Evidence

- Default worktree and OpenAIDatabase inventories each expose 0 raw paths; explicit `rg --no-ignore` and Git tracked inventories each expose 549.
- All eight Codex routes pass runtime contract validation with 0 forbidden paths.
- Vite probes reject two raw roots and allow two app/derived paths.
- The production dist contains 6 regular files and 3,249,771 bytes, with 0 raw path components and 0 collisions against 512 raw ledger hashes.
- Tiny real Git fixtures prove default search hides raw while explicit override sees it. Real sparse clones prove both repository topologies retain required code and omit raw directories.

## Validation

- Dedicated raw-isolation tests: 8/8 PASS.
- Focused raw isolation, routing, layout, profile, test-value and script-governance tests: 58/58 PASS.
- Frontend TypeScript lint and production build: PASS; Vite 8.0.16 transformed 1,768 modules. The existing greater-than-500-kB chunk warning remains non-blocking and is unrelated to raw isolation.
- Built-dist raw-isolation audit: PASS with `raw_content_read=false`, `raw_mutation=false` and `remote_push=false`.
- Complete local Python suite: 419/419 PASS in 521.773 seconds.
- Actual non-cone sparse clone with both raw roots absent: fresh npm install added 154 packages; runtime audit PASS; 419 tests PASS in 304.549 seconds with 3 contract-defined raw-absent skips; frontend build and post-build isolation PASS.
- `validate:fast`: 5/5 PASS in 18.196 seconds.
- `validate:sync`: 7/7 PASS in 200.585 seconds; complete credential scan took 180.151 seconds.
- `validate:ui`: 14/14 PASS in 444.175 seconds, including build isolation, three home viewports, command/proposal/Owner Daily paths, canvas, accessibility/privacy and visual semantics.
- `validate:release`: 1/1 PASS; final audit took 1,069.327 seconds. Every profile reported zero critical skips, audited commands, `raw_mutation=false`, `remote_push=false` and `shell=false`.
- Final repository privacy scan: PASS across 513 tracked raw/control files and 35 large public-raw files, with no large-file skip, credential-like path or high-risk secret hit.

## Independent Review

- Engineering/security first pass found 0 Critical / 1 Important / 2 Minor. The Important finding required CI evidence that explicit raw access remains possible when real raw is omitted; the fixture now tracks both ignore files and proves default exclusion plus explicit discovery. One Minor required executable standalone sparse-checkout proof; the test now uses a real Git repo and clone. The other Minor identified a dist file type/read race; no-follow open, `fstat` regular-file validation and a bounded read close it.
- Product/scope first pass found 0 Critical / 2 Important / 1 Minor. Canonical governance and this owner-facing review were missing and are added here. Four unrelated KMFA changes remain explicitly outside staging. The misleading test name was corrected to describe path-component and byte-identical-body checks.
- Engineering/security final rerun independently checked the staged diff, exact workflow/config/Vite boundaries and built-dist audit. Final result: **0 Critical / 0 Important / 0 Minor**.
- Product/scope final rerun confirmed canonical governance, four rendered human views, owner review, exact staged boundary, unchanged unstaged KMFA work and no T2/T3 implementation. Final result: **0 Critical / 0 Important / 0 Minor**.

## Risk And Recovery

- `.rgignore` changes rg defaults, not Git tracking or explicit raw tools. Users needing raw must opt in with `rg --no-ignore` or a dedicated audited command.
- Non-cone sparse patterns are exact workflow contracts; adding a runtime dependency outside them must update the contract and tests together.
- The dist hash comparison proves no byte-identical raw file was emitted. Derived provenance may legally name a public-raw source path and is not itself a raw-body leak.
- Before commit, roll back only the exact T1 patch. After local commit, use `git revert <S06-P3-T1 commit>`; never delete raw data to roll back tool isolation.

## Decision

Implementation and automated acceptance evidence satisfy the T1 behavior. Deterministic governance render, exact staged-scope inspection and both independent reviewer reruns are final and clean. `S06-P3-T1` is accepted locally; the next and only eligible Task is `S06-P3-T2`, and no T2 implementation is included here.
