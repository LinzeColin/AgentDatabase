# Architecture

## Two planes

**Control plane** is frozen per run: locked Genesis hash, user contract, authority contract, research seal, evaluation contract, holdout identifiers, reviewer packets, budgets and promotion rules. Candidate files cannot write it.

**Experiment plane** contains one or more editable candidates, snapshots, exact diffs, raw results, rejected changes and rollback points. Strategies may be incremental, architecture, clean-slate, composition or runtime-specific.

## Open adapters

Core state and gates use JSON/JSONL and Python standard library. Model/runtime invocation, sandboxing, web research and judges are adapters. No provider, model, API or directory layout is Genesis.

## Two timescales

- Fast loop: improve a target Skill inside one bounded run.
- Slow loop: improve Teleiosis only from frozen cross-run evidence or an explicit self-evolution run.

The running stable version never rewrites itself in place. A new candidate may replace the whole implementation if it preserves Genesis hard requirements and passes external evaluation.

## Freedom invariant

Governance may restrict authority, evidence quality and irreversible actions. It must not prescribe a permanent prompt, file count, model, architecture, candidate count, scoring formula or technology stack.
