# Evaluation

## Separate dimensions

Trigger accuracy, task effectiveness, safety, evidence truthfulness, cost, latency, installability, compatibility, cross-model transfer, maintainability and future adaptability remain separate. Process trajectories and outcomes are both required.

## Data split

- dev: visible failures and design feedback;
- validation: opened after a candidate is proposed;
- sealed holdout: external ID/hash only; prompt content is hidden from candidates;
- adversarial: injection, malformed data, neighboring triggers, authority traps and recovery.

Changing holdout closes the run and creates a new dataset version.

## Comparison

Freeze baseline, candidate and no-skill systems where meaningful. Randomize/blind outputs, repeat stochastic trials, retain raw results and report subgroup distributions. The modifier cannot be the final judge.

Decision order:

1. Genesis/safety/truthfulness/install/rollback/holdout hard gates;
2. no protected task-family negative transfer;
3. evidence-backed improvement;
4. Pareto frontier across quality, cost, time and maintenance.

No weighted average can offset a hard regression. User-approved trade-offs must be explicit rather than hidden in weights.

A stable Baseline may itself be defective. Baseline hard-gate failures are therefore preserved as named defects and do not prevent a Candidate from being evaluated as a repair. This is not a waiver: the Baseline still must be bound to one exact tree hash, the Candidate must satisfy every frozen hard gate, and the comparison must show no protected-family regression. Evidence-integrity failures remain blocking.

## Current research mechanisms

The design allows process-based coaching/evaluation, hierarchical capability and process views, multi-objective optimization, continual failure-driven refinement, cross-model adaptation and co-evolution adapters without making any one current paper or provider permanent.

## Identity binding

Every result must identify the frozen contract system, dataset ID/hash, split and the exact evaluated Skill tree hash. A candidate cannot be evaluated, modified afterward and then promoted under the old result. Every contracted baseline/candidate must cover every required split; a single global split observation is insufficient.
