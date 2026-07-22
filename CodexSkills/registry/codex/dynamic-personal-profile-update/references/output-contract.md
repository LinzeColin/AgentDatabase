# Dynamic Profile Output Contract

## Canonical file

`OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md`

This is a derived view. It must not be treated as the canonical stable profile.

## Machine layer

The file starts with YAML front matter containing:

- `schema_version`
- `artifact`
- `artifact_status`
- `skill_version`
- `generated_at`
- `input_mode`
- `source_snapshot_sha256`
- `semantic_snapshot_sha256`
- `source_files`
- `time_windows`
- `entry_count`
- `entries`

Each entry contains:

`id`, `type`, `status`, `statement`, `evidence`, `counterevidence`, `confidence`, `observed_window`, `valid_until`, `agent_action`, and `asset_candidate`.

## Human layer

After the front matter, render:

1. `# Dynamic Personal Profile`
2. `## 先看结论`
3. `## 变化条目`
4. `## 可立即试用的 Agent 行为`
5. `## Recurring Asset 候选`
6. `## 边界与不确定性`

The human layer is a projection of the machine entries. It must not contain facts absent from the machine layer.

## Size and evidence rules

- Keep the total file below 80 KiB in v0.0.0.1.
- Keep at most 24 entries; prefer high-confidence and cross-source entries.
- Evidence references must be repository-relative and point only to allowlisted derived files.
- Do not include full source text, transcript excerpts, credentials, raw paths, or personal secrets.
- Do not synthesize exact timestamps when the source has no timestamp; say `source timestamp unavailable`.
