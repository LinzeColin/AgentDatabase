# Research Sources and Mechanism Ledger

**Valid as of:** 2026-07-26
**Method:** primary repositories, official specifications, and primary papers. Search-result snippets, articles, Issues, stars, and marketing claims are discovery signals only; they cannot by themselves prove superiority or satisfy the five-peer gate.

| Source | Peer/evidence role | Mechanism adopted | Deliberately not frozen into Genesis |
|---|---|---|---|
| https://github.com/alchaincyf/darwin-skill | direct peer | read-only baseline, real experiment, keep/revert ratchet, independent judge, early stop; Darwin 2.0 also points to trajectory and process analysis | one-change-only, one score, or one model/runtime as universal law |
| https://github.com/LearnPrompt/luban-skill/blob/master/skills/luban/SKILL.md | direct peer | challenge whether the Skill should exist; at least five peers; ecosystem position; live-artifact reconciliation; install, release, showcase and reheat | prose-only compliance, direct-push assumptions, or one showcase format for every Skill |
| https://github.com/microsoft/SkillOpt | method and implementation peer | trajectory-led bounded edits, validation-gated best artifact, rejected-edit evidence | its exact training stack, evaluator, budget, or repository structure |
| https://arxiv.org/abs/2605.23904 | primary SkillOpt paper | executive strategy for self-evolving agent skills and validation-gated updates | paper-reported gains without local reproduction |
| https://github.com/microsoft/SkillLens | evaluation infrastructure peer | end-to-end experience → extraction → consumption study, reproducible lifecycle evaluation | its benchmark set, provider configuration, or taxonomy as universal |
| https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md | craft peer | existing-Skill improvement, old/new comparison, quantitative and qualitative eval, variance and trigger-description work | provider-specific invocation and background-run assumptions |
| https://agentskills.io/specification | official portability specification | portable frontmatter, canonical Skill folder, progressive disclosure, references/scripts/assets separation, validation | current optional directories, wording, or line-count guidance as immutable Genesis |
| https://arxiv.org/abs/2604.09297 | primary SkillMOO paper | multi-objective candidate evolution, Pareto/NSGA-II selection, pruning and substitution rather than instruction accumulation | one benchmark family or fixed objective vector |
| https://arxiv.org/abs/2604.01687 | primary CoEvoSkills paper | generator/verifier co-evolution and feedback without exposing ground-truth test content | surrogate verifier claims as proof for this package |
| https://arxiv.org/abs/2603.02766 | primary EvoSkill paper | automated skill discovery for multi-agent systems | multi-agent architecture as mandatory |
| https://arxiv.org/abs/2507.19457 | primary GEPA paper | reflective textual evolution and Pareto-aware search inspiration | prompt evolution as a substitute for package, code, artifact and safety evaluation |
| https://arxiv.org/abs/2607.05297 | primary MetaSkill-Evolve paper | two-timescale task-skill/meta-skill evolution and bounded self-improvement | recursive self-invocation or paper-reported gains without independent reproduction |
| https://arxiv.org/abs/2606.10546 | primary SkillAxe paper | diagnose quality impact, trigger precision, instruction compliance with fault attribution and solution-path coverage as separate dimensions; use evaluation-guided briefs rather than blind rewriting | unsupervised judge output as a substitute for real task execution or holdout evidence |
| https://arxiv.org/abs/2605.08670 | primary MIND-Skill paper | test trajectory abstraction with reconstruction faithfulness, outcome correctness and documentation-rubric evidence on held-out tasks | TextGrad, multi-agent implementation or its benchmark claims as universal requirements |
| https://arxiv.org/abs/2605.08693 | primary SkillMaster paper | evaluate a candidate edit by counterfactual downstream utility on related probe tasks; retain/update/create are explicit decisions | RL training, its reward model or benchmark gains as prerequisites for ordinary Skill iteration |
| https://arxiv.org/abs/2606.16774 | primary OpenClaw-Skill paper | preserve diverse candidate branches, use multiple independent assessors when available and measure cross-model transfer rather than optimizing one model only | collective scores without hard-gate evidence, or mandatory tree search for every run |
| https://arxiv.org/abs/2605.27366 | primary MUSE-Autoskill paper | lifecycle memory, per-Skill experience, creation/refinement/reuse and retirement/reheat signals | automatic retirement without owner authority or unbounded lifelong mutation |
| https://arxiv.org/abs/2605.19604 | primary Formal Skill paper | move deterministic workflow state, policy and completion checks out of repeated prose into executable, observable control surfaces | one runtime, hook system or executable representation as the only valid Skill form |
| https://arxiv.org/abs/2604.24026 | primary SSL representation paper | keep invocation, execution structure and side-effect evidence machine-readable for discovery and risk review | the proposed representation as a fixed standard or replacement for source artifacts |
| https://agentskills.io/skill-creation/optimizing-descriptions | official trigger-optimization guidance | test should-trigger and should-not-trigger cases separately because frontmatter description carries activation responsibility | optimizing trigger text without measuring task quality and false positives |
| https://arxiv.org/abs/2606.14239 | primary SkillAudit paper | paired trajectory auditing when oracle ground truth is unavailable; use as a diagnostic adapter, not a release oracle | replacing hard safety, provenance or live-artifact gates with judge preference |
| https://arxiv.org/abs/2605.18401 | primary SkillsVote paper | lifecycle credit attribution and collective candidate selection for future multi-candidate governance | popularity voting or majority scores that can override hard gates |
| https://arxiv.org/abs/2607.01874 | primary SkillCoach paper | process-oriented rubrics for how a Skill is consumed, not only final-answer scoring | model coaching claims without local task evidence |
| https://arxiv.org/abs/2606.03143 | primary FederatedSkill paper | privacy-preserving semantic-diff aggregation as an optional cross-organization adapter | federated infrastructure as a mandatory default or proof of local improvement |

## Frontier delta applied in this release

The July 2026 scan changes the implementation in five ways without enlarging the runtime prompt: evaluation contracts can carry trigger, compliance, coverage, trajectory-faithfulness and counterfactual probe metrics; candidate search remains portfolio-based rather than one-path hill climbing; deterministic policy lives in scripts/Gates instead of repeated prose; process-use rubrics and paired trajectory audit remain optional adapters; and reheat is driven by real trajectory failures, stronger peers, runtime/standard changes and evidence expiry. These are adapters and evidence fields, not permanently frozen algorithms.

## Adoption discipline

Every run creates its own competitor and mechanism-adoption ledger with:

- canonical source identifier and access date;
- exact repository commit when a real pull succeeds;
- licence and reuse boundary;
- adopted abstraction, rejected part and reason;
- local evaluation evidence and residual unknowns;
- explicit `PULL_BLOCKED`, `DYNAMIC_EVAL_NOT_AUTHORIZED`, or `UNKNOWN` instead of fabricated evidence.

No third-party source code is copied into this package. Mechanisms are independently implemented abstractions. A source appearing in this registry does not automatically qualify as one of a run's five real peers; qualification is decided by the frozen peer contract and actual provenance evidence.
