# Packaging and installation

The v0.0.0.5 release bundle contains both sibling Skills and installs only to:

- `$HOME/.codex/skills/persona-distiller`
- `$HOME/.codex/skills/persona-distiller-group`

Do not keep duplicate sources under `$HOME/.agents/skills`. The bundle installer verifies every member, stages both Skills, replaces old versions atomically, and rolls back both if either post-install check fails.

Each person release emits exactly one outer full-delivery ZIP and no sidecar. The outer ZIP has one top-level delivery directory and embeds exactly one immutable runtime Skill ZIP. It also contains installers, delivery manifest, complete internal checksums, portable registration, team card, verification, provenance, source coverage, evaluation summary, review record, handoff, and optional human reports.

Release sequence:

strict quality gate → complete team card → secret scan → deterministic runtime ZIP → deterministic full-delivery ZIP → all-member checksum verification → fresh outer install → runtime router/unnumbered-recorder smoke test → unique registration in the sibling group → rebuild group index/README/route → validate both hashes and all seven categories.

Packaging derives the next per-person product version; the number is officially consumed only after registration succeeds. Historical normalization may preserve a v0.0.0.4 runtime byte-for-byte inside a v0.0.0.5 outer delivery without consuming a new person-product version, but every missing historical audit item must be marked unavailable rather than fabricated.
