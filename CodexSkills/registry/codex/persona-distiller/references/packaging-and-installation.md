# Packaging and installation

Meta-skill installation defaults to `$HOME/.codex/skills/persona-distiller`;
project scope uses `<repo>/.codex/skills/persona-distiller`. `agents` remains
an explicit alternate host target, but the installer refuses simultaneous
`~/.codex/skills/persona-distiller` and `~/.agents/skills/persona-distiller`
sources.

A target ZIP contains exactly one top-level directory whose name equals `SKILL.md.name`. Runtime package excludes raw data, Holdout answers, full private source text, secrets, build versions and prior run history. It includes model files, identity catalog, router, invocation counter, active corrections, sanitized source/Claim metadata, installer, manifest and checksums.

Release sequence: strict quality gate → secret scan → deterministic package →
inspect ZIP paths → fresh extract → checksum verify → temp install → invoke
menu/router/counter smoke test → delete temp install → register the full ZIP
exactly once under one of the seven root-level identity directories → validate
the complete registry → publish checksum.
