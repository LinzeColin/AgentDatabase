# Build workflow

## Input contract

Required before build: `name`; `identity` is parsed only after the namesake gate passes. Optional: scenario, subject origin, consent, time scope, profile. The orchestration Agent first normalizes aliases, translations, transliterations and abbreviations, then searches the canonical registry and authoritative public sources. Every result must be classified before continuing: one candidate is bound internally regardless of evidence strength, while multiple candidates are a hard stop requiring user selection.

The namesake gate must run before identity parsing, workspace initialization, research acquisition, or packaging:

1. No candidate: continue with the normal input contract.
2. One candidate, including a low-evidence candidate: bind `chosen_subject_uid` and continue without asking the user to confirm.
3. Multiple candidates: list every candidate with letters A, B, C, D … (then AA, AB … as needed), stop immediately, and wait for a letter or a disambiguating identifier.

Every candidate is exactly four lines and does not display confidence:

```text
A. 人物与身份：姓名、身份分类、职业或主要职务。
   专业背景：组织、时代、地区与核心专业经历。
   应用价值：可蒸馏的应用场景与关键能力。
   区分依据：权威证据与其区别于其他同名者的关键特征。
```

If the subject is private or self, do not expand beyond authorized material. A namesake collision is resolved before the identity menu; identity categories remain internal build metadata and never become a runtime user requirement.

The machine gate is `scripts/namesake_gate.py`. It writes a schema 1.0 result containing the normalized name, all candidate cards, the resolution state and the selected subject UID. `scripts/init_target.py --namesake-gate GATE.json` refuses blocked or mismatched gates before parsing identity or creating/deleting a workspace.

## Gates

G0 namesake disambiguation → G1 input/consent → G2 identity resolution → G3 route plan → G4 source universe → G5 acquisition/normalization → G6 origin clustering → G7 coverage/saturation → G8 six-lane + identity research → G9 Claim adjudication → G10 executable model → G11 independent evaluation → G12 Architect/Skeptic ratchet → G13 package/install test → G14 incremental update.

Each gate writes a machine-readable artifact and blocks downstream promotion on critical failure. Research can remain `provisional`; packaging cannot silently waive failed release gates.

## Primary/secondary depth

The selected identity receives deep evidence collection and scenario benchmarks. The other eleven identities receive screening so runtime can state readiness rather than hallucinate cross-domain competence. Each persona has exactly one primary identity; multi-identity selection has been removed.
