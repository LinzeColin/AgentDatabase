---
name: dynamic-personal-profile-update
description: Read allowlisted redacted derived data and produce one human-readable and machine-readable dynamic personal profile Markdown file. Use when updating a time-aware user profile, detecting meaningful behavior or preference changes, turning profile changes into temporary agent actions, or mining recurring Prompt/Workflow/Skill candidates. Never read raw/private data, write stable memory, modify Custom Instructions, or create a second persistent state store.
metadata:
  version: "0.0.0.1"
  owner: "Linze"
  stage: "1"
  output_contract: "one Markdown file"
  input_mode: "derived_only"
  compatibility: "Python 3.11+; local filesystem or GitHub Actions runner; no network, API key, LLM call, database, vector index, or external service required."
---

# Dynamic Personal Profile Update

## Purpose

Turn existing redacted derived reports into a compact, time-aware profile delta that any human, LLM, Agent, or Memory Atlas reader can use immediately.

This Skill is a generated-view tool. It is not the canonical stable profile and it is not a memory writer.

## Hard boundaries

- v0.0.0.1 reads only the explicit allowlist under `OpenAIDatabase/data/derived/`.
- Never read `data/raw`, `data/public_raw`, private imports, session archives, cookies, browser state, secrets, or local absolute paths.
- Never overwrite `CORE_PROFILE.md`, active memory, Custom Instructions, AGENTS.md, or any stable rule.
- Never call an LLM or external API in the deterministic update path.
- The only persistent data output is `OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md`.
- Temporary files must be deleted after atomic replacement; no database, ledger, JSON state file, vector index, or run artifact is added.
- `hypothesis` and `emerging` entries remain candidates. They cannot become stable facts without explicit human review.
- A scheduled run that detects no material change must exit successfully without changing or committing the profile.

## Standard workflow

1. Read the repository's route and governance instructions relevant to derived personalization.
2. Run `scripts/update_dynamic_profile.py` with the repository root as `--database-dir`.
3. Run `scripts/validate_dynamic_profile.py` against the single output file.
4. Inspect the generated Profile Delta. Separate observed evidence from inference, counterevidence, confidence, validity, and proposed agent action.
5. When a change affects the next task, use `references/profile-to-agent-action-prompt.md` to create a temporary action instruction. Do not promote it automatically.
6. When repeated behavior may be reusable, use `references/recurring-asset-miner.md` to classify it as Prompt Template, Workflow, Skill, Schedule/Recurring Prompt, or observation. Require one real trial before promotion.

## Running the deterministic processor

```bash
python3 scripts/update_dynamic_profile.py \
  --database-dir . \
  --output OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md

python3 scripts/validate_dynamic_profile.py \
  --profile OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md
```

The processor prints a small JSON status object. `NO_CHANGE` is a successful result, not an error.

## What the output means

- `current`: repeated supported signal in the current derived sources; still not a stable memory write.
- `emerging`: repeated or cross-source candidate that deserves one controlled trial.
- `hypothesis`: plausible signal with insufficient independent evidence.
- v0.0.0.1 emits only these three statuses; `declining` and `retired` require a later authorized temporal-state contract.

The output's YAML front matter is the machine contract. The Markdown sections are its human-readable projection. They are generated from the same data in one pass.

## Stop conditions

Stop without writing when no allowlisted source exists, source validation fails, an input path escapes the allowlist, the output exceeds its size limit, forbidden content is detected, or the processor cannot preserve the previous output on failure.

See [output-contract.md](references/output-contract.md), [profile-to-agent-action-prompt.md](references/profile-to-agent-action-prompt.md), and [recurring-asset-miner.md](references/recurring-asset-miner.md) for the contracts used after activation.
