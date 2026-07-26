# Genesis/Baseline Change Benefit–Cost Decision — v0.0.0.2

## Decision

The byte-preserved base Genesis remains unchanged. The user explicitly authorized one append-only amendment under WBI-GB-026; therefore WBI-GB-028 is added without rewriting WBI-GB-001—027 or overwriting v0.0.0.1.

| Proposed action | Benefit | Cost / risk | Benefit greater than cost? | Decision |
|---|---|---|---:|---|
| Rewrite WBI-GB-001/024 wording | Could make time validity more explicit in two old clauses | Breaks byte identity, audit history and rollback; opens reinterpretation risk | No | Reject |
| Add WBI-GB-028 as append-only Amendment | Makes every final output carry current-environment snapshot, evidence lease, strength state and automatic expiry; closes a real enforcement gap | One new requirement, schemas, tests and migration of release commands | **Yes** | **Adopt** |
| Externally anchor only the base Genesis | Simpler command line | Coordinated rewrite of Amendment + internal lock could evade detection | No | Reject |
| Require external base + effective Genesis + archive hashes for release/deep | Detects base drift, Amendment drift and artifact substitution independently | One additional 64-character anchor and CLI flag | **Yes** | **Adopt** |
| Fix current models/vendors/tools in Genesis | Makes today’s environment explicit | Rapid obsolescence and direct conflict with WBI-GB-027 | No | Keep in dated snapshot/adapters |
| Permanently require Wilson intervals or current thresholds | Standardizes one statistical method | Freezes an implementation choice and can be inferior for future tasks | No | Keep as replaceable default adapter |
| Lower external 2×6+1 requirement | Enables a green formal status now | Destroys independence and accountability | Severe negative | Prohibited |
| Overwrite v0.0.0.1 in place | Simpler directory history | Breaks provenance and exact rollback | Severe negative | Release v0.0.0.2 separately |

## Anchors

```text
Base locked Genesis: 14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086
Effective Genesis v0.0.0.2: fe80c467f8ecbe8343ef0c09ef5e6f9fd9683803c8260c9188998c7e3dfca0a2
Requirements: 27 base + 1 authorized amendment = 28 effective
```

The Amendment increases evidence obligations but does not add a long runtime Prompt, freeze a model/vendor/tool or limit future architecture. Net benefit is positive because the same mechanism prevents stale or unbounded “current strongest” claims across every future implementation.
