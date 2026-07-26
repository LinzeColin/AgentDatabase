# External Verifier Bridge

## Boundary

Teleiosis may prepare evidence for the separate `verifier` Skill, but it cannot issue its own independent acceptance verdict. The bridge exports a read-only packet bound to the exact subject tree hash.

## Command

```bash
python3 scripts/wbi.py verifier-export \
  --subject /absolute/path/to/teleiosis \
  --valid-as-of 2026-07-26 \
  --acceptance-contract templates/verifier-acceptance-contract.json \
  --output /absolute/external/teleiosis-verifier-packet.zip
```

The output must be outside the subject tree. It contains:

- exact subject version, Genesis anchor and tree hash;
- evidence file hashes and byte sizes;
- critical acceptance items;
- isolated verification commands;
- fail-closed verdict policy;
- expected one-ZIP verifier output.

The bridge returns `PACKET_READY_REVIEW_PENDING`, never `VERIFIED`, `APPROVED`, or formal promotion.

## Acceptance chain

The separate verifier should trace:

```text
Requirement -> Acceptance item -> Oracle -> Test/inspection -> Evidence -> Subject hash -> Verdict
```

Critical failures cannot be compensated by an aggregate score. Missing or ambiguous evidence blocks.
