# LinzeColin Integration

Recommended physical mapping when the public repositories contain these paths:

```text
AgentDatabase/CodexSkills/registry/codex/teleiosis/
AgentDatabase/CodexSkills/skill_controlled_iterate/<skill-id>/<run-id>/
AgentDatabase/CodexSkills/skill_log_evals/<skill-id>/<run-id>/
AgentDatabase/OpenAIDatabase/data/run_logs/skills_runs/<skill-id>/<run-id>/
```

Registry stores only formal releases and external Genesis/release hashes. Candidate workspaces and failed evidence never overwrite it. This package performs no branch, PR, remote push, merge, tag or deployment without separate authorization.
