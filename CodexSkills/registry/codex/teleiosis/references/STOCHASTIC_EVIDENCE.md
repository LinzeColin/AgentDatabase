# Stochastic Evidence

LLM and Agent runs are stochastic. `stochastic-compare` uses a predeclared minimum trial count, effect threshold and Wilson intervals. The only decisions are `SUPPORTED`, `REGRESSED` or `INCONCLUSIVE`.

Overlapping intervals or insufficient trials remain `INCONCLUSIVE`; repeated trials cannot be cherry-picked after seeing results. This implementation is a default adapter, not a permanent statistical method. A run may substitute a stronger predeclared sequential or Bayesian contract while preserving raw trials, budgets and hard gates.
