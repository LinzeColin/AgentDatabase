# Persona-Distiller-Group Expert Panel Bridge

## Purpose

A list of role labels is not an expert team, and multiple prompts in one builder context are not independent reviewers. `expert-panel-export` creates a routing contract for `persona-distiller-group` without inventing people or declaring review completion.

## Formal responsibility shape

The bridge now mirrors Teleiosis' exact separation contract:

```text
Persona Distiller Group: Panel A (6) + Panel B (6)
Separate Verifier Skill: final read-only acceptance verdict (1)
Total formal shape: 2x6 + 1
```

The Persona team does **not** contain the final verifier and cannot grant formal promotion. The separate `verifier-export` packet supplies the exact subject and acceptance contract to the verifier Skill.

## Two panels

Panel A covers architecture, evaluation, competitive intelligence, security, release/recovery and operator UX. Panel B covers cost/efficiency, runtime portability, failure mechanisms, evidence provenance, productization/adoption and an isolated counterevidence red team.

Both panels must contain six ready personas, preserve individual findings before synthesis, and remain identity/context isolated. The counterevidence seat is a control role. Same-context role simulation remains useful only as design coverage, never independent evidence.

## Command

```bash
python3 scripts/wbi.py expert-panel-export \
  --task "Adversarially review Teleiosis v0.0.0.2" \
  --valid-as-of 2026-07-26 \
  --persona-index /absolute/path/to/team-index.json \
  --output /absolute/external/expert-panel-request.json
```

Without a real team index, the packet reports `ROSTER_INPUT_REQUIRED`. With an index, it reports only `READY_FOR_PERSONA_DISTILLER`; it still does not claim that experts were selected, executed, independent, or that the verifier completed acceptance.
