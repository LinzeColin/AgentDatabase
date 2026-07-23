# Handoff — 人物蒸馏 Skill / Persona Distiller v0.0.0.3

## 1. Final product contract

This package is the **builder/orchestrator Skill**. After installation, it accepts only:

- target person's name;
- identity: one of six primary identities or a weighted multi-identity selection.

Scenario is optional. The builder performs evidence research, synthesis, evaluation, refinement, and produces one directly installable target-person Skill ZIP.

Identity menu:

1. 技术工程师
2. 创业经营家
3. 投资资本家
4. 开发设计家
5. 思想教育家
6. 政治法律家
7. 多重身份（at least two weighted primary identities）

Private/self/fictional/historical are routed through multi-identity but remain separate `subject_origin` governance modes. Private/self data cannot pass the consent gate merely because an identity was selected.

## 2. Target-person runtime contract

Every substantive invocation of a generated person Skill must first receive a fresh identity/weight selection. A same-message selection is sufficient; `沿用上次身份` is an explicit selection. Merely displaying the menu consumes no serial.

After identity selection, `invocation_manager.py begin` atomically allocates one immutable artifact/run version:

```text
0.0.0.1 ... 0.0.0.999 ... 0.0.0.N
```

- completed and failed calls both keep their number;
- numbers are never reused;
- explicit skips require user instruction plus an audited override flag;
- crash recovery closes stale started calls as failed;
- state/history reconciliation prevents reuse after a process dies between commits;
- each run has `run.json` and `artifact-manifest.json` with identity, status, hashes, and logical versioned output names;
- task text is not stored by default—only its SHA-256; content storage is opt-in.

## 3. Person model

A generated target model separates:

- verifiable facts and time/role scope;
- Cognitive OS;
- decision policy;
- strategy and resource allocation;
- demonstrated/limited/unavailable capabilities;
- Work system, tools, quality standards, and delivery behavior;
- Persona, values, temperament, conflict, and voice;
- identity facets and weighted conflict routing;
- negative capability, refusals, stop/escalation rules;
- divergence map across periods, roles, speech, behavior, and sources;
- quarantined psychological/existential hypotheses.

Priority is: law/safety/user constraints → boundaries → accepted corrections → facts → evidenced capability/decision patterns → bounded inference → style → quarantined hypotheses.

## 4. Research and evaluation

Research uses six base lanes plus identity-specific source topology. “As complete as practical” is operationalized as source universe, coverage cube, canonical-origin/near-duplicate clustering, gap-driven expansion, and two consecutive rounds without new high-impact Claims. It never claims literal exhaustion of all public/private material.

The package contains 16 evaluation suites, including Holdout replay, boundary, voice, trajectory, contrast, fact preservation, style decoy, task completion, planning fidelity, tool use, capability calibration, refusal/stop, long horizon, identity routing, anonymous fidelity, and token efficiency.

Architect proposes minimal patches. Skeptic attacks provenance, overfit, privacy, capability hallucination, and regression. Stable model changes require snapshot, evidence/Claim impact analysis, targeted plus global regression, and promotion or rollback.

## 5. Memory and lifecycle

Three version axes are independent:

- builder release: `v0.0.0.3`;
- target semantic model version;
- per-invocation artifact version: `0.0.0.N`.

Stable model, procedural memory, episodic runs, user overlay, correction ledger, and promotion queue are separated. Runtime success or user convenience cannot silently rewrite the person.

## 6. Packaging and installation

Builder default install root: `~/.codex/skills/persona-distiller`. Do not keep a
second installation under `~/.agents/skills/persona-distiller`.

Released target-person ZIPs must be registered exactly once under
Skill 根级
`<技术工程|企业领导|金融投资|软开设计|思想教育|政治法律|多重身份>/`.
Multi-identity targets use only `多重身份`; later model versions remain under
the same subject registration.

The builder ZIP has one top-level `persona-distiller/`, no symlinks, no caches, and a checksum manifest. Installation verifies source checksums, copies/links, verifies the installed copy, executes a post-install self-check, and restores the backup on failure.

Generated target-person ZIPs also have one top-level directory, checksums, installer, package manifest, sanitized source/Claim ledger, empty runtime counter/history, and no raw corpus or Holdout bodies by default.

## 7. Verification completed

- 43 offline unit/integration/concurrency tests passed; final checksum-aware self-check also passed.
- Seven identity registration folders, cross-folder uniqueness, full target ZIP retention, generated index consistency, idempotence, and public-registry privacy refusal are executable gates.
- Two reviewer rounds passed: six isolated roles; Round 1 has 24 checks, Round 2 has 39 adversarial checks.
- First, failed, 999th, explicit override, recovery, reconciliation, concurrent allocation, and artifact hashing tested.
- Source/Claim/Holdout separation, corrections, snapshots, diff, verification, rollback, deterministic target ZIP, checksum tamper rejection, root installation, and runtime reset tested.
- A fresh extracted candidate passed checksum verification, clean install, weighted target initialization, automatic scenario routing, `0.0.0.1` allocation, result hashing, runtime verification, and uninstall.
- A real initialization defect caused by cached Python files in templates was found during dynamic testing and fixed by excluding `__pycache__`, `.pyc`, and `.pyo`.

The environment did not expose an independent SubAgent orchestration interface. The six roles are isolated checklists and tests, not falsely described as six independent models.

## 8. Residual risks and next upgrades

- Target-specific fidelity is unproven until lawful target research, frozen Holdout material, and independent judging are completed.
- Dependency-free semantic near-duplicate detection relies on canonical origins, hashes, and host-assisted semantic review; an embedding/MinHash plugin remains a future enhancement.
- The filesystem counter is safe for concurrent processes sharing one installation, not for distributed multi-machine writers; those need a transactional external allocator.
- Host models and tools differ. Cross-host behavioral portability must be evaluated separately from installation portability.
- Deletion, paywalls, private archives, oral history, and undigitized sources prevent proof of absolute global completeness.

## 9. Surprise retained in the architecture

The most important long-term artifact is not a prose persona but a **versioned decision operating system plus divergence map**. High fidelity comes from preserving where the target changed, contradicted themselves, stopped, refused, lacked capability, or behaved differently under another role—not from smoothing all evidence into one confident voice.

## 10. Repository-verification boundary

The research pass accessed the public profile/root pages and relevant visible subdirectories of the seven public repositories shown under `LinzeColin`. The container could not resolve `github.com` for recursive cloning, so this handoff does not claim execution of every historical commit, release asset, submodule, nested external dependency, or private repository.
