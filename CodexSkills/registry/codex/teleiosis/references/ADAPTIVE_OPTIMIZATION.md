# Adaptive Optimization Profile

## Purpose

Teleiosis v0.0.0.2 does not assume that every Skill should be optimized by the same sequence, metric set, patch size or verification depth. `doctor` first performs a bounded, no-exec, no-follow diagnosis; `adaptive-plan` then selects an implementation profile while preserving the same Genesis and evidence hard gates.

The design borrows an engineering principle from `Curzibn/Luban`: classify the input, apply a strategy matched to its characteristics, defend extreme inputs, and fall back to the original when the transformed output is worse. It does not reuse Android code or image-specific thresholds.

## Target classes

| Class | Typical evidence | Default emphasis | Default verification |
|---|---|---|---|
| `text-and-reasoning` | SKILL.md and references, few/no scripts | trigger precision/recall, task quality, workflow and failure branches | fast for diagnosis; release before delivery |
| `tool-execution` | scripts or executable assets | task success, process bounds, runtime neutrality, failure recovery | release |
| `tool-and-artifact` | scripts plus generated files or UI | artifact correctness, reproducibility, install/recovery, task outcome | release or deep |
| `artifact-productization` | demos, reports, assets, showcase | real-artifact reconciliation, installability, clarity, reproducible showcase | release |
| `large-mixed-repository` | broad code/docs/assets surface | scope decomposition, representative sampling, portability, bounded execution | release/deep by risk |
| `high-risk-or-side-effecting` | deployment, deletion, privilege, network or production mutation signals | least privilege, reversibility, authority, sandbox, auditability | deep |

Classification is not a safety verdict. Static signals can be false positives; they are disclosed as evidence for review. Possible credentials and symlinks are blockers because copying or publishing them can create irreversible exposure.

## Bounded scan guarantees

`doctor`:

- does not import or execute target code;
- does not follow symlinks;
- caps file count, aggregate text bytes and per-file text bytes;
- reports truncation as `PARTIAL` evidence;
- records target tree hash, inventory, capabilities, risk signals, blockers, warnings and environment compatibility;
- states that static analysis cannot prove task outcome or safety.

Default limits are 5,000 files, 8 MiB aggregate text and 256 KiB per text file. Operators may change limits explicitly; a larger limit is not automatically better.

## Adaptive candidate portfolio

The plan chooses a small candidate portfolio rather than one universal hill-climb:

- `trigger-and-clarity`: smallest text-only changes for activation and workflow quality;
- `incremental`: smallest attributable repair to the strongest evidence bottleneck;
- `architecture`: move repeated policy into scripts, contracts or progressive references;
- `clean-slate`: bounded local-optimum escape while retaining the baseline fallback;
- `productization`: install, real-artifact check and reproducible showcase improvements.

High-risk targets omit `clean-slate` from the default portfolio because broad rewrites weaken attribution and increase review load. It remains possible only through an explicit, separately reviewed candidate contract.

## Negative-optimization guard

A candidate is retained only when all conditions hold:

1. mandatory metrics do not regress under the frozen equal-budget contract;
2. no hard gate fails;
3. evidence is complete enough for the claim;
4. candidate growth stays inside its declared ratio, or excess growth has measured outcome/maintainability benefit;
5. rollback remains valid.

Otherwise the decision is `REVERT`, `NO_CHANGE`, `BLOCKED` or `REHEAT_REQUIRED`. The fallback is the frozen baseline or last independently verified candidate. This is the Skill-equivalent of Luban's “compressed output grew, therefore pass through the original” rule.

## Runtime and platform adaptation

EasyDarwin demonstrates a different reusable pattern: a stable core with multiple protocol/platform adapters and visible operational state. Teleiosis applies that pattern by separating:

- stable evidence semantics and Genesis;
- runtime/model/provider adapters;
- package/install adapters;
- external review adapters;
- truthful operator-facing status.

An adapter may extend compatibility but cannot weaken evidence, permission, holdout or rollback requirements.

## Commands

```bash
python3 scripts/wbi.py doctor /path/to/skill \
  --valid-as-of 2026-07-26 \
  --output /external/path/target-diagnostic.json

python3 scripts/wbi.py adaptive-plan \
  --diagnostic /external/path/target-diagnostic.json \
  --run-mode engineering \
  --output /external/path/adaptive-plan.json
```

`optimize` runs both automatically and binds the outputs into `control/orchestration-state.json` without advancing the PREFLIGHT receipt.
