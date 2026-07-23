# Evaluation and refinement

Core suites: known Holdout, boundary, voice, trajectory, contrast, fact preservation, style decoy. Holdout leakage is a hard failure.

Agentic suites: task completion, planning fidelity, tool-use correctness, capability calibration, refusal/stop, long horizon, identity-weight routing, anonymous-name fidelity and token efficiency.

Use no-Skill baseline, blind judging, neighboring-person foil and anonymous target condition. Decision/behavior evidence outranks verbal resemblance. Long answers need sentence-level out-of-character checks; long conversations need 20/50/100-turn drift checks where feasible.

Roles must be isolated: Researcher, Builder, Generator, Judge, Architect and Skeptic. If the host cannot start independent subagents, run serialized contexts with sealed inputs and disclose that independence is weaker. Never describe same-context role-play as independent model evidence.

Ratchet rule: apply the smallest patch that addresses a measured failure. Keep only if critical suites do not regress, facts remain intact, identity routing remains deterministic and package/install checks pass.
