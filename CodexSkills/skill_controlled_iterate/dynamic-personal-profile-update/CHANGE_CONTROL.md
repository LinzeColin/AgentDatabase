# Controlled Iteration Contract｜dynamic-personal-profile-update

## Version rule

Only patch versions are allowed: `0.0.0.1`, `0.0.0.2`, `0.0.0.3`, and so on without a fixed upper limit.

## Allowed patch changes

- Correct an input parser without changing the output purpose.
- Improve evidence extraction, validation, size limits, or failure recovery.
- Clarify trigger wording or the temporary action prompt.
- Add a regression fixture for a discovered failure.

## Stop and review changes

Pause for explicit review if a change reads raw/private data, adds an LLM/API dependency, changes the sole output path, writes stable memory, adds a persistent store, changes source namespaces, changes repository visibility, or changes the promotion rule.

## Rollback

Disable the scheduled workflow, restore the previous Skill package and previous `DYNAMIC_PROFILE.md`, then rerun the validator. Never rewrite history or delete evidence.
