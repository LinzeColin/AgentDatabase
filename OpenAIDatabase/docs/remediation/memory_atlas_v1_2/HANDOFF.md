# Memory Atlas v1.2 Remediation Handoff

## Migration Preservation Checkpoint (Authoritative)

- Date: `2026-07-17`.
- Canonical repository after the eight-repository split:
  `LinzeColin/AgentDatabase`; the active frontend is now top-level
  `MemoryAtlas/`.
- Feature development is paused at `66/149` (`44.30%`).
- `S09-P2` is `3/3` complete. `S08-P3-T1` remains owner-deferred/open and
  uncounted. The next and only development task after migration is
  `S09-P3-T1`.
- The complete paused task line is reachable from `main` as an isolated
  `OpenAIDatabase` subtree history:
  - scoped baseline: `dfd6c4f44f7e9d743418c6e8d1bd3021c87a5fee`;
  - scoped tip: `b77dc48288786735ee4a0b1ba933f668f7b7c42e`;
  - 57 task commits plus one baseline commit;
  - final scoped tree:
    `7404f1ac43f3042da0e05d5722ada364ed91cb17`.
- Every scoped task commit retains its source author/date/message and a
  `Source-CodexProject-Commit` trailer. The source identifiers were
  `12d10f63d15e41cec50026d5dfd2ea0fab5a0e69` (integration base),
  `ade2c852ce077c36e5683caf25cdd408f5e45964` (integrated candidate), and
  `3f7af705774a16986e06650050b63c5bcf13ac55` (original local tip).
- The history-only merge keeps the migrated active tree byte-identical to the
  target repository. The scoped history uses the old subtree layout, so
  `apps/memory-atlas/` there maps to active `MemoryAtlas/`; never restore the
  scoped root wholesale.
- Before the repository split, the integrated candidate passed canonical
  `fast` `19/19`, `unit` `33/33`, command ownership, directory lifecycle,
  repository privacy, workflow security, TypeScript lint and production
  build. Its three-viewport browser gate remained `FAIL` because seven SVG
  `<title>` tooltips inherited thread names containing `S06-P2/P3`.
- The migration-safe active checkpoint then passed TypeScript lint,
  production build, canonical `fast` `19/19`, `unit` `33/33`, `integration`
  `153/153`, security `151/151`, privacy guard, and the real `1470x661`,
  `1440x900`, `390x844` browser gate. This validates the active checkpoint,
  not the paused scoped product candidate.
- No export, deployment, force push, branch or PR belongs to this checkpoint.
  Do not re-enable automated ChatGPT login, UI scraping, export download or
  repository raw-archive production.

Read `migration_preserved/runtime/README.md` and
`migration_preserved/validation/README.md` before inspecting the scoped
history. The R0-R7 material below is historical; this checkpoint wins where
the two conflict.

## Current Goal

Complete reopened v1.2 remediation R0-R8 with at most one phase per run and one final
GitHub main upload only after R8 passes.

## Current State

- R0-R7: complete locally; this does not mean the release is complete.
- R7 public raw: 512 sanitized files / 452,781,632 bytes; manifest and ledger each have
  512 entries with 0 drift, deletion or unledgered files.
- R7 immutable release: `memory-atlas-v1-2-r7-20260710`; snapshot SHA-256
  `b608631fded9e116d350895be20e6e61be3c7e42ba651ccdf7fc52afd8fefcbc`.
- Snapshot: 278 active memories / 379 conversations / 128 Codex sessions / 435 nodes /
  2,325 edges; derived/release/local candidate/Pages candidate bytes match.
- Tracked-only recovery: PASS for functional candidate `f65668b9`; 8,372 tracked files,
  0 working-tree-only files, two source packages restored, fresh npm install/build and
  Pages parity PASS. Exact pushed-remote clone recovery is not yet proven.
- Requirements after R7: `VERIFIED 53 / PARTIAL 2 / FAILED 3 / NOT_VERIFIED 0`.
- Release: `FAIL_REMEDIATION_REQUIRED`.
- GitHub push, app reinstall and Cloudflare deployment: not performed.
- Online website and installed app: still the prior release; do not present them as R7.
- Final fetch: `origin/main=37d757be958e1546b5263e86d2193663b184bbe8`;
  before R7 record commit local `main` was ahead 52 / behind 17.

## Key Decisions

- Rendered/runtime evidence is required; source markers and document presence are not
  product acceptance.
- Required browser viewports remain `1470x661`, `1440x900` and `390x844`.
- Public transcript recovery is sanitized and credential-free. Private source paths,
  credentials, original binary bodies and private export bytes are intentionally absent.
- Raw acceptance requires non-empty source families, byte-wise privacy audit, immutable
  manifest and a drift/deletion/new-file ledger audit; vacuous zero-row PASS is invalid.
- One immutable release snapshot drives derived, local candidate and Pages candidate
  bytes; install/deploy scripts must consume that release rather than rebuild ad hoc.
- Recovery proof distinguishes the functional candidate `f65668b9` from later evidence
  binders. Exact final pushed HEAD recovery is an R8 gate.
- Hosted static remains read-only. Command/proposal/Owner Daily execution remains
  local-app only and all R3-R6 security boundaries remain in force.
- Incoming remote history must be preserved. R8 may reconcile it, but must not force-push.

## Read First

- `docs/remediation/memory_atlas_v1_2/R7_DATA_PARITY_RAW_EVIDENCE_AND_RECOVERY.md`
- `机器治理/证据与日志/remediation/v1_2_r7/status.json`
- `机器治理/证据与日志/remediation/v1_2_r7/browser_regression.json`
- `机器治理/证据与日志/remediation/v1_2_r7/recovery/status.json`
- `机器治理/证据与日志/remediation/v1_2_r7/source_provenance.json`
- `docs/remediation/memory_atlas_v1_2/R0_SOURCE_RECOVERY_AND_GAP_BASELINE.md`
- `docs/superpowers/plans/2026-07-10-memory-atlas-v1-2-remediation.md`

## Verified Commands

- `python3 -m unittest tests.test_memory_atlas_r7_public_raw tests.test_memory_atlas_r7_raw_integrity tests.test_memory_atlas_r7_release_parity tests.test_memory_atlas_r7_recovery -q`
- `python3 scripts/audit_memory_atlas_public_raw.py --database-dir .`
- `python3 scripts/raw_archive_manifest.py audit --database-dir .`
- `python3 scripts/materialize_memory_atlas_release.py verify --database-dir .`
- `python3 scripts/audit_memory_atlas_snapshot_parity.py --database-dir . --local-runtime <prepared-local-runtime> --pages-candidate apps/memory-atlas/dist/memory_atlas.json`
- `python3 scripts/privacy_guard.py --database-dir . --scan-only`
- `npm run lint`
- `npm run build`
- `npm run validate:v1.2-visual-models`
- `npm run validate:v1.2-visual-workflows`
- `npm run validate:v1.2-home-multiviewport`
- `npm run validate:v1.2-command-workflows`
- `npm run validate:v1.2-proposal-e2e`
- `npm run validate:v1.2-owner-daily-e2e`
- `npm run validate:stage7-visual`
- `npm run validate:stage7`

## Remaining Risks

- Five requirements remain non-VERIFIED: `S03-AC05`, `S04-AC04`, `S10-AC04`,
  `S14-AC02`, `S14-AC05`.
- Overall final audit does not yet require all new R1-R7 gates in one fail-closed chain.
- Local and remote histories diverge; R8 must preserve both before the single push.
- Remote clone recovery, exact pushed commit install, exact pushed commit deployment and
  online multi-viewport/workflow acceptance are not yet proven.
- Installed app and online site are intentionally unchanged.

## Next Phase

Run only `R8_OVERALL_ACCEPTANCE_AND_SINGLE_FINAL_DELIVERY`: reconcile both histories,
wire and pass all 58 requirements, perform the one authorized GitHub main push, recover
from that exact remote HEAD, reinstall/deploy that exact commit and repeat browser/workflow
acceptance online. Do not mark the goal complete unless every R8 gate passes.
