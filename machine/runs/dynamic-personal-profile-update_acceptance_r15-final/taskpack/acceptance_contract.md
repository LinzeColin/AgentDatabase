---
doc_id: "P01-ACCEPTANCE"
doc_type: "acceptance_contract"
version: "0.0.0.1"
status: "frozen_for_acceptance"
---

# Acceptance Contract

| Requirement | Oracle | Method | Threshold | Evidence |
|---|---|---|---|---|
| AC-01 Skill format | Agent Skills validator | `skills-ref validate` or equivalent frontmatter check | PASS; name ≤64 chars; valid description | validator output |
| AC-02 Registry mapping | Registry record and path check | inspect source namespace and five layers | exactly one `codex` record for this version | registry YAML |
| AC-03 Derived-only input | Allowlist audit | run positive/negative fixture | zero raw/private reads | test output |
| AC-04 One output | Git diff allowlist | run processor and Action | only `DYNAMIC_PROFILE.md` can change during scheduled update | diff |
| AC-05 Dual plane | Structural validator + human review | inspect one generated file | all required machine fields and six human sections present | profile file |
| AC-06 Evidence | Path validator | inspect every entry | evidence path is allowlisted derived path | validator output |
| AC-07 No stable write | before/after path audit | run Action | `CORE_PROFILE.md`, memory, instructions unchanged | diff |
| AC-08 Idempotence | Repeat-run oracle | run identical input twice | second run `NO_CHANGE`; bytes unchanged | command output + hash |
| AC-09 Failure safety | Failure fixture | remove/invalid source after a valid output | nonzero stop; old output unchanged | test output |
| AC-10 Cost gate | no-change workflow run | trigger with same inputs | no commit and no extra artifact | Action run |
| AC-11 Profile action | real-task trial | apply reference prompt once | explicit action, scope, expiry, verification produced | trial note |
| AC-12 Asset miner | recurring trial | classify one repeated behavior | one candidate with evidence and `pending` promotion | trial note |
| AC-13 Patch control | version check | inspect registry/control record | only `0.0.0.N` versions allowed | control record |
| AC-14 Route discovery | route oracle | resolve `dynamic_profile` intent | points only to `DYNAMIC_PROFILE.md`; marks it derived/read-only; does not replace startup or canonical routes | route JSON diff + read-back |

## Verification and pass gate

The package passes only if AC-01 through AC-10 and AC-14 are PASS and AC-11/AC-12 are either PASS or explicitly `UNKNOWN` with a recorded reason. Any privacy, write-boundary, data-loss, route, or rollback failure is a hard stop.

## Kill criteria

Kill or revert if the output is only a longer report, if facts cannot be traced to evidence, if the script needs an LLM/API to run, if repeated runs create meaningless commits, if a second persistence layer appears, or if maintenance cost exceeds the measured reduction in context reconstruction or rework.
