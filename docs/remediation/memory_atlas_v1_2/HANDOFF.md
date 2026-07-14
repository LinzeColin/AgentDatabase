# Memory Atlas v1.2 Remediation Handoff

> **Current v1.2.1 note (2026-07-14):** This file preserves the earlier v1.2 R7
> handoff below. Memory Atlas is executing the v1.2.1 Task Pack with one Task per run.
> S04 is complete locally. `S05-P1-T1` replaced 36 Stage-era human documents with the
> seven shallow Chinese files under `人类可读/`. `S05-P1-T2` has now compressed the
> deterministic `功能清单.md`, `开发记录.md`, and `模型参数文件.md` owner entries from
> 789 lines / 70,990 bytes to 130 lines / 7,007 bytes. Each entry presents current
> status and the next Task by lines 3 and 12; the contract is
> `config/memory_atlas_owner_entries.json` and the fail-closed audit/tests are
> `scripts/audit_memory_atlas_human_plane.py` and
> `tests/test_memory_atlas_human_plane.py`. Historical reviews and source packages
> remain unchanged. The next Task is only `S05-P1-T3`, which owns the v1.2.1 change
> and usage map; T3 has not started.
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
