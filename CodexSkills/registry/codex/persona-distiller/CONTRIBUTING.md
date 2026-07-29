# Contributing

Changes must preserve the two-input build contract, twelve-family unique registry (single primary identity; weighted multi-identity was removed in v0.0.0.6), automatic internal runtime identity routing, unversioned invocations, per-person product releases `0.0.0.1` through `0.0.0.999`, provenance, privacy minimization and rollback. Add a regression test for every defect. Do not edit generated manifests by hand; run `scripts/build_manifest.py` when present or the release helper documented in `handoff.md`.
