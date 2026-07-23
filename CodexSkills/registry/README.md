# CodexSkills Registry

This registry is the governance surface for Skill records. It is separate from the mirrored Skill content.

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

The current Skill mirror migration must update `sync_skills.py` so the four source namespaces are under `registry/`. The root `CodexSkills/README.md` and `index.json` remain compatibility entry points and must point to `registry/<source>/<slug>/SKILL.md`.

`codex/persona-distiller` is routed directly to
`registry/codex/persona-distiller`. Its generated target-person ZIPs use the
seven folders under `产物登记/`; each subject has one canonical registration
across all categories, and the `CodexSkills/README.md` product list is generated
from that registry.
