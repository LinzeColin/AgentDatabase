# Public/private artifact boundary

## Three planes

| Plane | Purpose | Git policy |
| --- | --- | --- |
| `PUBLIC_SAFE` | Code, schemas, empty templates, governance records, synthetic tests | May be tracked after scanner passes |
| `PRIVATE_RUNTIME` | Decisions, reference baselines, cached parsing results, run evidence | Must remain ignored and local |
| `RAW_SOURCE` | Original finance, payroll, contract, image, archive, and exported system files | Read-only source; must never be copied into this module's tracked plane |

Unclassified paths fail closed. Public files must be UTF-8 text within the configured size ceiling, must not be symbolic links, and must not contain configured sensitive path or identifier signatures.

## Private runtime layout

The initializer creates these ignored directories without placeholder files:

- `private_runtime/cache/`
- `private_runtime/runs/`
- `private_runtime/decisions/`
- `private_runtime/reference_baseline/`

Public synthetic fixtures belong under `tests/synthetic/`. Private regression fixtures belong under `private_runtime/reference_baseline/`. Moving data between these planes requires explicit sanitization, a policy update, and regression tests; renaming alone is never sufficient.

## Operator checks

Before a later release stages changes:

```bash
python3 scripts/scan_private_boundary.py --working-tree
python3 scripts/scan_private_boundary.py --staged
```

Any finding blocks staging, release, global installation, and claims of completion.
