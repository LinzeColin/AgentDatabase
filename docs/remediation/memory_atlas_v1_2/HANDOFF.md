# Memory Atlas v1.2 Remediation Handoff

> **Current v1.2.1 note (2026-07-15):** This file preserves the earlier v1.2 R7
> handoff below. Memory Atlas is executing the v1.2.1 Task Pack with one Task per run.
> S04 and S05 are complete locally; S06-P1-T1 is complete and the next Task is
> only S06-P1-T2. S05-P1 compressed the human
> plane to seven shallow Chinese files, compressed the three root owner entries, and
> added the deterministic v1.2.1 change/five-workflow map. `S05-P2-T1` added
> `config/memory_atlas_machine_truth_index.json` and deterministically renders
> `机器治理/README.md` as a 72-line/4,702-byte shallow index over exactly five domains
> and 11 canonical targets. The index stores paths, responsibilities and mutability
> only; it does not copy parameter values, formula expressions, runtime status, test
> assertions or data. `S05-P2-T2` then used
> `config/memory_atlas_machine_plane_cleanup.json` to delete exactly eight approved
> Stage-era nested READMEs (1,948 lines / 90,721 bytes). It preserved byte-identical
> sets of 29 active configs, one current release and 122 evidence payloads, migrated
> the only executable README evidence reference to `docs/governance/roadmap.yaml`,
> migrated the same three stale references in the tracked derived collaboration report
> without changing scores or business values, and permanently verifies all eight Git
> restore paths from commit `187577cc9`.
> `S05-P3-T1` keeps `apps/memory-atlas/src/i18n/zh-CN.ts` as the only typed
> human-interface copy source. Version
> `memory_atlas.zh_cn_copy.v1_2_1_s05_p3_t3` now provides the visible glossary
> explanations, 11 field labels, nine enum groups and a Chinese unknown-value
> fallback. Help, runtime status, Inspector and proposal surfaces consume the same
> source; code/API/schema/data attributes, persistence fields and exported payload
> keys remain English and unchanged. The shared fail-closed audit/tests remain
> `scripts/audit_memory_atlas_human_plane.py` and
> `tests/test_memory_atlas_human_plane.py`; the new copy-source suite has 6 tests,
> while 65 focused tests, 325 full Python tests, fast 4/4, ui 12/12, frontend
> lint/build, dual-runtime deterministic render and desktop/mobile Help browser checks
> passed. `S05-P3-T2` adds a TypeScript AST semantic-readability rule without a
> new public profile. It scans 83 UI source files for mojibake, default-visible
> machine fields, actionless errors and English empty states. The exact baseline is
> 79 findings (78 machine-field/enum points and one actionless error); mojibake and
> English empty states are zero. Any new, missing-unreconciled or fingerprint-drifted
> finding fails. UI executes the rule as `semantic_readability`; release executes the
> same rule through its existing final-audit Chinese UX gate. `S05-P3-T3` then
> remediated all 79 findings: finding, known-finding and known-T3-debt counts are zero,
> and `semantic_readability_clean=true`. Core default-visible fields, statuses, risk,
> tier, sync, proposal, formula and canvas labels use Chinese humanizers; API, schema,
> data attributes, internal enums, persistence and export payload keys remain English.
> Seven semantic tests, 35 governance/profile tests, 332 full Python tests, fast 4/4,
> ui 13/13, frontend lint/build and the release profile plan passed. Real Home browser gates
> passed at 1470x661, 1440x900 and 390x844 with no section overlap, horizontal overflow,
> console error or failed response. Data Guide structure and detail/proposal browser
> gates also passed with raw edge/ID evidence and version strings excluded from the
> default-visible surface. Independent engineering/governance and product/UI reviews
> both closed at 0 Critical / 0 Important / 0 Minor.
> `S06-P1-T1` extends the sole canonical
> `config/data_sources/source_registry.json` with the 11 TaskPack sync fields for
> ChatGPT official export, Codex local data, generic agents and the existing
> codex-reviewer source. Discovery and data paths are portable and repository-relative;
> parsers, schedules, state/archive/derived paths and final-delivery-only push policy
> are explicit. `atlasctl sync` now dispatches through registered `source_type` and
> `parser.entrypoint`; a standard generic source can reuse the generic adapter by
> configuration. Environment candidates now drive the matching adapter argument;
> concrete generic sources cannot redirect `source_id`/`agent_id`, and parser/type,
> state/archive/derived conventions plus push policy fail closed. The active raw policy
> points to the canonical registry; the old machine-governance registry has no live
> script/test/app/config references and remains historical. The protected active-config
> manifest was updated for that one reviewed reference change. Explicit generic input
> blocks a conflicting environment candidate, and the generic adapter now parses
> multi-record JSONL. Canonical ID/type/status, non-canonical generic-only IDs, reserved
> aliases, non-lowercase/non-portable agent IDs, case-only and whitespace-padded
> namespace aliases, Windows reserved device basenames,
> template/concrete namespace collisions, direct adapter provenance and empty/invalid
> JSONL all fail closed. The owner change map now
> explicitly labels its unfinished-route prose as the S05-P1-T3 historical snapshot.
> Fourteen registry tests, 103 focused tests,
> sync 6/6, fast 4/4 and 346 full Python tests passed. No public raw, source data,
> state, manifest, chunk or restore artifact changed.
> `S06-P1-T2` adds `config/data_sources/public_raw_layout.json` and the
> `atlasctl audit --check public-raw-layout` gate. The existing tree is now bounded to
> five shallow directories and 513 tracked files: one control README plus 512 raw
> files split across ChatGPT 379, Codex 132 and Codex reviewer 1. The audit reads no
> raw bodies, rejects unknown/deep/symlink paths, and preserves config-only sources
> before their first sync. Real Vite resolution keeps publicDir and server allow on
> derived/app paths; a six-file production dist has no symlink or public_raw path, and the real
> startup route returns zero raw sources. Only the public-raw control README changed;
> no raw data file changed. T3 credential exclusions and P2 ledger/chunk/restore remain
> unimplemented. Ten layout tests, 99 focused tests, sync 7/7, fast 4/4, ui 14/14,
> 356 full Python tests, frontend build, script-hash governance and dual-runtime
> deterministic render passed; audit safety remained raw mutation=false and remote
> push=false. Historical source/release/recovery evidence remains unchanged. The next
> Task is only `S06-P1-T3`; it has not started.
>
> The only public validator profiles are `validate:fast`, `validate:sync`,
> `validate:ui`, and `validate:release`. Commands in the older "Verified Commands"
> section are historical evidence, not current package aliases. Use
> `docs/remediation/memory_atlas_v1_2_1/S04_P3_T3_COMMAND_MIGRATION.md` for old-command
> lookup. No v1.2.1 work has been pushed or deployed; do not create a branch or PR,
> and do not clean TaskPack, recovery evidence, raw/derived data, or machine caches.

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
