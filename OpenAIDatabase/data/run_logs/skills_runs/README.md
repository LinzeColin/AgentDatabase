# Skill Run Logs

Canonical runtime location: `OpenAIDatabase/data/run_logs/skills_runs/`.

Final physical layout:

```text
YYYY/MM/DD/part-NNNN.jsonl
YYYY/MM/DD/index-NNNN.jsonl
YYYY/MM/DD/manifest-NNNN.json
YYYY/MM/DD/retention-receipt-NNNN.json
```

Every non-empty line must be the exact RFC 8785 JCS UTF-8 representation of
one `urn:linzecolin:agentdatabase:skillops:schema:public-run-event:v2`
instance, framed by a single LF. Each index line is the corresponding
`run-event-index-entry:v1` record. Daily manifests and retention receipts are
single RFC 8785 JCS objects with no BOM or trailing LF.

The shard date uses `Australia/Sydney`. Logical part numbers start at 1 and
remain gapless in every manifest revision. A pruned part may be physically
absent only when its immutable index remains and the latest append-only
manifest links the exact retention receipt. Parts and indexes are each capped
at 20 MiB; manifests and receipts are capped at 1 MiB.

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
rejects every repository ledger artifact even if a complete synthetic day
passes schema, canonical-byte, event/index, manifest-chain, retention, and
physical-digest closure.

Never store prompts, outputs, reasoning, tool or command arguments, stdout,
stderr, raw source text, secrets, PII, local absolute paths, full transcripts,
or generated profile copies here. `UNKNOWN` is an explicit binding state, not
permission to infer a Skill/version.
