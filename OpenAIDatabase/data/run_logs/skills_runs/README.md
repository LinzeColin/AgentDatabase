# Skill Run Logs

Canonical runtime location: `OpenAIDatabase/data/run_logs/skills_runs/`.

Final physical layout:

```text
YYYY/MM/DD/part-NNNN.jsonl
```

Every non-empty line must be the exact RFC 8785 JCS UTF-8 representation of
one `urn:linzecolin:agentdatabase:skillops:schema:public-run-event:v2`
instance, framed by a single LF. The shard date uses `Australia/Sydney`.
Parts start at `part-0001.jsonl`, remain gapless per day, and are at most
20 MiB.

The sibling task-run directories continue to use
`config/evaluation/task_run.schema.json`; that schema never applies here.
Run:

```bash
python3 -B OpenAIDatabase/scripts/validate_skill_run_logs.py \
  --database-dir OpenAIDatabase --repo-root .
```

Current state is `DRAFT_NON_ACTIVE_CONSUMER_READY`. This directory must remain
empty except for this README until all three gates are independently complete:
ACTIVE repo-external trust, Auto AU-040 daily shard/manifest implementation,
and the Mechanism BOUND reference resolver. The current validator therefore
rejects every repository shard even if an individual synthetic record passes
the schema.

Never store prompts, outputs, reasoning, tool or command arguments, stdout,
stderr, raw source text, secrets, PII, local absolute paths, full transcripts,
or generated profile copies here. `UNKNOWN` is an explicit binding state, not
permission to infer a Skill/version.
