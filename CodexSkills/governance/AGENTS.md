# CodexSkills Governance Contract

This subtree is Mechanism-owned. It defines versioned entity, evaluation,
promotion, policy, canonicalization, validation, and bundle contracts.

Do not place Auto adapters, raw storage, queues, sanitizers, state, locks,
publishers, notifier transports, retention executors, automation prompts, or
sync implementations here. Auto-owned schemas live outside this subtree and
are consumed only through a versioned schema bundle.

All JSON is UTF-8 and must pass the repository canonicalization and offline
validator entrypoints. Network schema resolution, implicit format checking,
unknown fields, duplicate keys, non-finite numbers, lone surrogates, and
untrusted bundle selection fail closed.

`DRAFT_NON_ACTIVE` material must not create or update `CodexSkills/VERSION`,
an active manifest, a canonical publication, or a runtime watermark. Only a
later coordinated activation transaction may make these contracts active.

Never invoke the verifier during development. A fresh verifier is selected by
the Owner only after Mechanism and Auto integration is complete.
