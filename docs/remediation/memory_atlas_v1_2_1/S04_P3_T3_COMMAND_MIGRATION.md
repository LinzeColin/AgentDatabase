# Memory Atlas v1.2.1 S04-P3-T3 Command Migration

## Task Contract

- Task: `S04-P3-T3`
- Goal: migrate every historical public validator command to the four stable profiles without restoring the 178 aliases.
- Scope: validator command metadata, retained validator registration checks, focused tests, and governance evidence.
- Non-scope: product features, raw or derived data, deployment, push, branch/PR work, and cache cleanup.

## Function List

| Capability | Canonical interface | Behavior |
| --- | --- | --- |
| Fast regression | `npm run validate:fast` | CLI/core structure, typecheck, mounts, and command migration audit |
| Sync regression | `npm run validate:sync` | Source dry-runs, raw integrity, and credential scan |
| UI regression | `npm run validate:ui` | Build and real browser/user-workflow gates |
| Release regression | `npm run validate:release` | Canonical final audit |
| Legacy lookup | `python3 scripts/memory_atlas_legacy_commands.py --lookup <alias>` | Returns migration metadata only; never executes the old or replacement command |
| Migration audit | `python3 scripts/memory_atlas_legacy_commands.py --audit` | Fails closed on source, count, profile, expiry, target-state, caller, or public-surface drift |

## Migration Facts

- Historical source: commit `f22f2d336e3b5154a68fbabeec33b13be646a56c`, `OpenAIDatabase/apps/memory-atlas/package.json`.
- Source package SHA-256: `06268d65a3db20919a94860a7f2a41c3408204e8aa5276d83f25ca8c8ce29c01`.
- Sorted alias manifest SHA-256: `aa3134c05c436f2645052dc6dc8866521df4906a9996dc25fe20b1d2bfcc0689`.
- Rows: 178 total; 39 retained internal targets and 139 targets retired in `S04-P3-T2`.
- Replacements: fast 2, sync 0, ui 11, release 165.
- Public `package.json` contract remains exactly `validate:fast`, `validate:sync`, `validate:ui`, and `validate:release`.

The complete per-command mapping is machine-readable in
`config/memory_atlas_legacy_command_migrations.json`. Historical files may retain old
command text as evidence; current executable callers must use the map or a canonical profile.

## Compatibility Parameters

| Parameter | Value | Reason |
| --- | --- | --- |
| `mode` | `lookup_only` | Helps operators find replacements without extending the executable command surface |
| `execution_supported` | `false` | Prevents hidden shell behavior and accidental reliance on removed aliases |
| `introduced_version` | `v1.2.1` | This consolidation release |
| `removal_version` | `v1.2.2` | Enforces a one-release migration window |
| `maximum_supported_releases` | `1` | Prevents permanent compatibility debt |

No model formula, business threshold, weighting, or user-facing behavior changed. The only
parameter change is the technical release-gate alias `PARAM-095`, now `validate:release`.

## Validation And Rollback

Required checks:

```text
python3 scripts/memory_atlas_legacy_commands.py --audit
python3 -m unittest tests.test_memory_atlas_legacy_command_migrations tests.test_memory_atlas_validator_profiles tests.test_atlasctl_script_consolidation tests.test_memory_atlas_test_value_audit -q
npm run validate:fast
npm run validate:sync
npm run validate:ui
npm run validate:release -- --plan
python3 -m unittest discover -s OpenAIDatabase/tests -p 'test_*.py' -q
```

Rollback is `git revert` of the local Task commit. Do not restore 178 package aliases. If a
single old check must be inspected during rollback, use its `previous_package_command` from
the map or restore its target from the recorded Git source without exposing it publicly.
