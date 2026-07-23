# CodexSkills Auto Contract

This subtree is Auto-owned. It defines adapters' public/private transport
schemas, deterministic schema materialization, and Auto contract tests.

Do not define or reinterpret Skill Identity, Instance, Version, Eval,
Promotion, retention-policy, notification-policy, or bundle semantics here.
Those remain Mechanism-owned under `CodexSkills/governance/`.

Public schemas in `schemas/public/` are candidates for the shared 29-schema
bundle. Private schemas in `schemas/private/` are operational state contracts
and must never enter that bundle. Every object layer is closed, every public
string is bounded by enum/pattern/length, and all references resolve through
the repository's offline Registry. Network schema resolution and runtime
dependency installation are forbidden.

`DRAFT_NON_ACTIVE` files must not create or update `CodexSkills/VERSION`, an
active/candidate bundle manifest, canonical data, an automation prompt, or a
runtime watermark. A later coordinated activation is required.

Never invoke the verifier during development. The Owner selects a fresh
verifier only after both planes finish integration.
