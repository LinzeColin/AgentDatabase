# Skill Run Logs

Canonical runtime location: `OpenAIDatabase/data/run_logs/skills_runs/`.

Only redacted, compact JSONL run facts belong here. A run record may contain:

- `run_id`, `skill_id`, `skill_version`, `started_at`, `finished_at`
- `status`: `PASS`, `FAIL`, `NO_CHANGE`, or `UNKNOWN`
- `input_mode`, `source_snapshot_sha256`, `output_path`
- `tests_run`, `failure_recovery`, and `promotion_decision`

Do not store full stdout/stderr, transcripts, raw source text, secrets, local absolute paths, or generated profile copies in this directory.
