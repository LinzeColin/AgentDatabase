# Auto Gmail query-capability corrective handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_GMAIL_QUERY_CAPABILITY_CORRECTIVE`
- Implementation baseline:
  `sha1:cf7c5d25fb9093989190be9bf7cc66a02b2315ad`
- Candidate Git object:
  `sha1:899a4374bc02f5e18444fea7404864df7b118adf`
- Candidate bundle digest:
  `2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5`
- Verified M0c-A Git object:
  `sha1:3a0b8222cf52d6a35f31986c411ac98daed06c5c`
- M0c-A control interface raw SHA-256:
  `70b4e8c8ab47db541c90bbc6ebf092a483ca776c07b84b939b5a9b0be783e5c2`
- Auto runtime interface:
  `CodexSkills/registry/auto/runtime-interface.json`
- Runtime interface raw SHA-256:
  `43a30b67903e9f5284f607129b7e3830aa507449552190b5992db770c01299d4`

## Completed in this corrective

- The corrective was rebuilt from the independently fetched registry-layout
  baseline. The deleted `CodexSkills/auto/**` path and its old trust tuple were
  not reused.
- Gmail preflight still authenticates the profile and binds it to the
  owner-only recipient mapping. It now also performs a deterministic,
  no-send `users.messages.list` request with `maxResults=1` and the fixed
  public-safe query
  `in:sent rfc822msgid:<skillops-query-capability-v1@notification.skillops.invalid>`.
- The fixed query contains no recipient, credential, mailbox content, live
  provider message ID, or transaction identifier. The bounded response is
  shape-checked and discarded. Provider errors or malformed responses fail
  closed before any send or metadata read.
- Both the generic notification CLI and the activation intent path consume
  this same transport preflight. Public capability output states only that the
  query endpoint was verified, that no send occurred, and that real-message
  metadata readback is still pending.
- This probe does not claim provider receipt readback. A real M0c-B send must
  still read back and verify the exact Message-ID, correlation digest, and
  private payload digest before a receipt can become `SENT`.

## Consumer-first P0 drift

Registry relocation invalidated the current Mechanism-owned consumer
interface. Its raw SHA-256 remains
`94a5186aeaad6947eec19ef67539e3f03c0db06d47292d58088fdc4ee8bb53c6`,
but it still pins candidate object
`sha1:4b1e1a318c8f9e1014839a8a3a46e057679c4b6b` and bundle digest
`fd1df66e240695bd376803423bd09f9f341f7542f74a6ed92b0f79b0af4dc5e1`.
The relocated contract requires `899a4374...` / `2704ed79...`. The clean
baseline consumer validator therefore fails closed with
`skill_run_consumer_bootstrap_failed:TRUST_SCHEMA_PATH_OWNER_MISMATCH`.

The runtime interface consequently keeps
`consumer_first_gate_satisfied=false`,
`external_gmail_ready_gate_satisfied=false`, and `m0c_b_permitted=false`.
This Auto phase did not edit `OpenAIDatabase/**`; an independent Mechanism
phase owns the consumer trust-tuple repin.

## Validation evidence

- Targeted Gmail unittest: `20/20 PASS`.
- Relocated Auto unittest: `106/106 PASS`.
- Mechanism unittest: `42/42 PASS`.
- Seeded fault/privacy: `92/92 PASS` for seed `271828`; `92/92 PASS` for seed
  `314159`.
- Mechanism draft, candidate bundle, activation control, Auto schemas, and
  Auto runtime interface are byte-equivalent.
- Trusted candidate bundle: `29 schemas / 5 policies PASS`.
- Activation control: two bootstrap schemas over the pinned `29/5` candidate
  `PASS`.
- Candidate runtime preflight: Python/dependency/vendor/offline Registry
  `PASS`.
- Python 3.9 AST, diff-check, no-VERSION, and owner-path boundary checks:
  `PASS`.
- Immutable Task Packs were not historically rerun, per run constraint.

## Explicitly not done

This corrective did not create `CodexSkills/VERSION`, an activation intent,
notification receipt, settlement, ACTIVE manifest, canonical data, production
state root, watermark, daily shard, or automation change. It did not call the
real Gmail API, send email, read a real message, run M0c-B or A1c, call the
verifier, restart the App, extend a time window, or touch any paused
automation. `SKILLOPS_STATE_ROOT` was not provisioned in the controlled
environment, so recipient/config/OAuth/query readiness remains
`UNKNOWN/NOT_READY`. AU-040 remains false.

## Next exact action

Mechanism must independently repin and verify the consumer interface against
candidate `899a4374...` / `2704ed79...`. After that, the Owner must provision
the repo-external `0700` state root and exact `0600` private contracts, then
run the no-send Gmail capability gate in a controlled environment. Only after
both gates are independently READY may a new Mechanism M0c-B run create an
intent, send, perform real provider metadata readback, settle, or publish.
