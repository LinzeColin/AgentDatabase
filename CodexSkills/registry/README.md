# CodexSkills Registry

This registry is the canonical home for mirrored Skill content and its compact
registration records.

## Source namespaces

- `agents/`
- `claude/`
- `codex-system/`
- `codex/`

Each registered Skill uses one compact five-layer entity: `identity`, `provenance`, `capability_contract`, `verification`, and `controlled_iteration`. Each layer must have a real consumer; empty ceremonial records are rejected.

## Governance locations

- Registration: `CodexSkills/registry/`
- Evaluation records: `CodexSkills/skill_log_evals/`
- Controlled patch iteration: `CodexSkills/skill_controlled_iterate/`
- Runtime records: `OpenAIDatabase/data/run_logs/skills_runs/`

`sync_skills.py` writes every mirrored Skill to
`registry/<source>/<slug>/`. The root `CodexSkills/README.md` and `index.json`
remain compatibility entry points and point to those canonical paths.

The non-Skill Auto contract package and the sync regression tests also live
under `registry/auto/` and `registry/tests/`. They are excluded from Skill
deletion propagation.

`codex/persona-distiller` is routed directly to
`registry/codex/persona-distiller`. Its generated target-person ZIPs use the
seven identity folders directly under the Skill root; each subject has one canonical registration
across all categories, and the `CodexSkills/README.md` product list is generated
from `persona-registry-index.json`.
