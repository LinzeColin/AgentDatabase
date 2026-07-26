# Codex Task Pack — 白箱迭代Skill / Teleiosis v0.0.0.2

Codex is the landing operator, not the product developer. The engineering package may be installable while formal promotion remains blocked. Do not redesign or regenerate this Skill.

## Inputs

- archive: `White-Box-Iteration-Skill-Teleiosis-v0.0.0.2-final.zip`
- base Genesis SHA-256: `14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086`
- effective Genesis SHA-256: `fe80c467f8ecbe8343ef0c09ef5e6f9fd9683803c8260c9188998c7e3dfca0a2`
- archive SHA-256: obtain from the external `SHA256SUMS.txt` in the final delivery root

## Required actions

1. Verify all three external anchors.
2. Extract to a temporary directory and run strict verification plus the full self-test.
3. Install with `--verification-level release`; use `--replace` only when upgrading an existing Teleiosis.
4. Read the durable install receipt and run `install-status --verify-installed`.
5. Preserve the predecessor backup and rollback command.
6. Copy the accepted tree to `AgentDatabase/CodexSkills/registry/codex/teleiosis/` and update registry metadata only after user authorization.
7. Do not convert `OUTCOME_NOT_PROVEN`, `INDEPENDENT_REVIEW_UNAVAILABLE`, `CURRENT_ENVIRONMENT_STRENGTH_NOT_PROVEN` or `FORMAL_PROMOTION_BLOCKED` into PASS.

Exact commands are in `delivery/INSTALL.md`.
