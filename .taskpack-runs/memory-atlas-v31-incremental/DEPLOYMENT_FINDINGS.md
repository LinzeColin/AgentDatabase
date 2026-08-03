# Deployment and data-spine findings (measured 2026-08-03)

Measured directly against Cloudflare, R2 and GitHub. No credential value appears
in this file, in any tool output, or in any commit — per the vault's own rule and
the 2026-08-02 exposure incident recorded in it.

## 1. Production is stale, orphaned and unreproducible

| Fact | Value |
|---|---|
| Pages project | `openai-memory-atlas` (created 2026-07-10) |
| Live production deployment | `2026-07-11T23:23:33Z` |
| Built from commit | `12734c10bf37ee7afc86d62f72e70369a1bcd732` |
| That commit in `LinzeColin/AgentDatabase` | **does not exist** — GitHub API returns `422 No commit found for SHA` |
| Working tree at upload | `commit_dirty: true` |
| Project git source | `source: null` — **direct upload only, no repo connection** |

Three consequences:

1. Production has been serving a build from a commit that was never pushed. It
   cannot be reproduced from the repository, and it cannot be code-reviewed.
2. **Pushing to `main` does not deploy anything.** There is no build hook. Every
   deployment on this project is an ad-hoc `wrangler pages deploy`.
3. The rollback target is that same orphan build. Rolling back after a bad
   promotion would restore something unreproducible — which is why promotion was
   left to the owner rather than done unattended.

`build_config.destination_dir` is `apps/memory-atlas/dist`, a path that does not
exist in this repository (`MemoryAtlas/dist`). Vestigial from an older layout;
harmless for direct upload, misleading for anyone reading the project config.

## 2. The production custom domain is deactivated

`memoryatlas.linzezhang.com` is attached to the project but reports
`status: deactivated` (`validation_data.status: active`, method `http`;
`verification_data.status: deactivated`).

DNS still points at it — `memoryatlas.linzezhang.com` → CNAME
`openai-memory-atlas.pages.dev`, proxied — and Cloudflare Access still guards it.
An unauthenticated request correctly gets `302` to the Access login, so the
deactivation is invisible from outside. **The owner should check whether the
production site actually loads after signing in**; a deactivated custom domain
normally stops Pages from serving that hostname.

## 3. Candidate deployed, production untouched

| | |
|---|---|
| Deployment id | `dfe20d84-977c-422e-8f31-df4791d498c5` |
| Environment | `preview` — takes no production traffic |
| URL | `https://dfe20d84.openai-memory-atlas.pages.dev` |
| Alias | `https://candidate-5526528c.openai-memory-atlas.pages.dev` |
| Commit | `5526528c552c64bd3894800d16a2aadd3fa145c3`, `commit_dirty: false` |
| Uploaded tree | 6 files, 2.3 MB, sha256 of the sorted file digest list `320b40fc2a1698e13b85cd6e34caeba75708220c836578b7eea3ad5d8efb8c4f` |
| Production after this run | unchanged, still `12734c10bf37` |

This is the taskpack's blue/candidate step. Promotion is deliberately not done.

## 4. AC-018 remains not self-verifiable — one gate, named

Cloudflare Access protects all three surfaces:

- `memoryatlas.linzezhang.com`
- `openai-memory-atlas.pages.dev`
- `*.openai-memory-atlas.pages.dev` (so the candidate too)

Every one returns `302` to the Access login for me. The vault does contain an
Access admin token, and it would technically allow minting a service token and
adding it to the preview app's policy. That is a change to an owner-only access
control, so it was not done. Verification stays with the owner:

```bash
MEMORY_ATLAS_BASE_URL=https://candidate-5526528c.openai-memory-atlas.pages.dev npm run validate:v31:browser
```

## 5. Data spine verified live (AC-011, AC-012, AC-017)

The R2 configuration is one bucket with prefixes, not separate buckets — the
`primary-objects` and `backups` top-level buckets exist but are **not** what
Memory Atlas uses, and 403 for these credentials. That is correct scoping, not a
gap:

- bucket `weread-port-private`
- raw prefix `primary-objects/memory-atlas/` — 9 normalized objects, 3.21 GB
- fact prefix `backups/private-database/memory-atlas/` — 6 bundles, dated
  2026-08-02 and 2026-08-03

**Read-back, 6/6 verified.** Each object downloaded in full; remote `ETag`
equals locally computed MD5; locally computed SHA-256 matches the
content-addressed filename (`private-facts-<sha256 prefix>.json`); every bundle
parses as `memory_atlas.private_fact_bundle.v1`.

**Raw objects, 9/9 readable.** Ranged reads confirm well-formed JSONL with a
consistent 13-field record schema.

**Isolated restore.** Everything was written only to a scratch directory outside
the repository. No source path was written, moved or deleted.

**Private-Database fact commits are live**, roughly every 15 minutes; most recent
`a107e5bb` at `2026-08-03T12:11:13Z` on
`Private-AgentDatabase/memory-atlas/failure-compound/latest`.

So the capture → R2 → fact-commit chain is running and remotely verifiable. It is
being driven by the existing Codex automation, which the owner confirmed is
healthy and which was left untouched.
