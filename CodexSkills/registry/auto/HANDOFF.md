# Auto M0c activation-handshake corrective handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_M0C_ACTIVATION_HANDSHAKE_CORRECTIVE`
- Protocol: `urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1`
- Verified M0c-A Git object:
  `sha1:3a0b8222cf52d6a35f31986c411ac98daed06c5c`
- M0c-A control interface:
  `CodexSkills/governance/activation/control-interface.json`
- Control interface raw SHA-256:
  `70b4e8c8ab47db541c90bbc6ebf092a483ca776c07b84b939b5a9b0be783e5c2`
- Candidate bundle digest:
  `2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5`
- Candidate Git object:
  `sha1:899a4374bc02f5e18444fea7404864df7b118adf`
- Auto runtime interface:
  `CodexSkills/registry/auto/runtime-interface.json`
- Runtime interface raw SHA-256:
  `7a6047fd84d4ced5fde022980a28276f654db3839ca44726a70a3aa325581bfa`

## Completed in this corrective

- Runtime activation control requires two independent external tuples:
  candidate Git object/bundle/manifest/mode and M0c-A Git
  object/control-interface digest/path/mode. The checkout cannot promote its
  own interface into a trust root.
- The local Mechanism activation runtime is byte-compared with the externally
  selected M0c-A Git object before import. The exact control interface and two
  bootstrap schemas then compose the pinned 29-schema/five-policy candidate
  into a 31-schema/five-policy offline validation closure.
- Intent, receipt, settlement, and every settlement artifact are read through
  descriptor-relative `O_NOFOLLOW` traversal. Public activation JSON must be
  exact RFC 8785 JCS UTF-8 without a BOM or trailing newline.
- Gmail metadata is derived only from a verified intent. Before any send, Auto
  verifies the live remote head still equals the intent baseline. The generic
  notification CLI rejects `planned_action=ACTIVATE`, so activation cannot
  bypass the verified-intent entrypoint.
- The publisher no longer accepts caller `activation_envelope_verified`,
  caller artifact-digest maps, caller `SENT` strings, or caller shared-gate
  maps. It validates the real settlement, recomputes all four physical
  artifacts plus the distinguished settlement, proves a live exact
  single-flight lock, rejects Git metadata paths, checks the changed-path set,
  performs only an expected-head ordinary FF push, and remotely reads every
  byte back.
- `activation_handshake_cli.py` exposes exactly two production operations:
  `notify-intent` and `publish-settlement`. Neither was invoked in this
  corrective.

## Validation evidence

- Auto unittest: `102/102 PASS`.
- Mechanism unittest: `42/42 PASS`.
- Seeded fault/privacy: `88/88 PASS` for seed `271828`; `88/88 PASS` for seed
  `314159`.
- Mechanism draft, candidate bundle, activation control, Auto schemas, and
  Auto runtime interface are byte-equivalent.
- Trusted candidate bundle: `29 schemas / 5 policies PASS`.
- External activation control closure: `31 schemas / 5 policies PASS`.
- Candidate runtime preflight: Python/dependency/vendor/offline Registry
  `PASS`.
- Python 3.9 AST, diff-check, no-VERSION, path-boundary, secret-pattern, and
  email-literal checks: `PASS`.
- Immutable Task Packs were not historically rerun in this corrective, per
  run constraint. M0c-A's remote-readback evidence remains the prior immutable
  package evidence.

## Explicitly not done

This corrective did not create `CodexSkills/VERSION`, an activation intent,
notification receipt, settlement, ACTIVE manifest, canonical data, production
state root, watermark, or automation change. It did not send email, run a real
source migration, call the verifier, restart the App, extend a time window, or
touch any paused automation.

The Mechanism-owned consumer-first gate is complete. AU-040 remains
incomplete: the immutable Task Pack still requires bounded daily JSONL shards
and a manifest under
`OpenAIDatabase/data/run_logs/skills_runs/YYYY/MM/DD/part-NNNN.jsonl`.

## Next exact action

An independent capability gate must prove the repo-external state root,
recipient mapping, Gmail OAuth scopes, authenticated-recipient binding, and
provider lookup/readback are ready. Only after that gate is READY may a new
Mechanism M0c-B run create the intent, obtain a real `PRE_WRITE` provider
`SENT` receipt, settle, publish, and establish the external ACTIVE trust tuple.
