# Runtime Adapters

Teleiosis keeps model, Agent runtime, judge, sandbox, source and Registry integrations outside the thin kernel. An adapter declares its version, authority, capabilities, isolation, cost, failure modes and evidence format; missing capability yields `BLOCKED` or a non-promotional diagnostic run.

## Adapter classes

- model/Agent invocation with token, latency and cost counters;
- trigger and task execution;
- blind outcome judges and process-trace evaluators;
- genuinely isolated SubAgent spawning and read-only final verification;
- disposable dynamic-evaluation sandbox;
- source discovery beyond GitHub;
- Registry, run-log, signing and provenance storage.

## Independent-review attestation adapter

A formal 2×6 review requires an **external, frozen adapter contract** supplied at `init-run`:

```json
{
  "schema_version": "1.0",
  "adapter_path": "/trusted/runtime/review-attestor",
  "adapter_sha256": "<sha256>",
  "receipt_root": "/trusted/runtime/receipts/run-id",
  "capabilities": ["independent-subagents", "read-only-verifier"],
  "provider": "<provider>",
  "runtime": "<runtime>"
}
```

The exact schema is validated by the stable runner. Paths must be absolute and outside the workspace, target and optimizer roots. The adapter is hash-pinned in the run seal and called without shell expansion. Candidate code cannot replace it, write the external receipts or change the contract after the run starts.

## Openness without silent trust

Adapters may be replaced or extended in future runs; their names, providers and protocols are not Genesis. Replacement does not mean implicit trust: every formal run freezes the selected adapter and records capability, raw output, hash, authority, cost and failure evidence. A future runtime can add stronger signatures, hardware attestation or independent storage without changing the core Skill.
