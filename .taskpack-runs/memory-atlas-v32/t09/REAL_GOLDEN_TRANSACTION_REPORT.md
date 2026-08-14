# v0.0.0.32 — T09 real golden transaction

Executed 2026-08-04 through the Owner's own authenticated Cloudflare Access
session in their browser. **No credential was created, no Access policy was
changed, and no secret passed through the agent.**

## Why not a service token

The taskpack's action list says "使用干净 Cloudflare Access 会话登录真实入口". A
service token is one way to satisfy that; a real session is the thing itself.

It was also the only available route. All five Cloudflare tokens in the vault —
`cloudflare_token`, `cloudflare_access_token`, `cloudflare_ovh_vps1_sg_token`,
`cloudflare_r2d1_token`, `cloudflare_readonly_token` — plus
`cloudflare_access_admin_token` return `10000 Authentication error` on
`POST /accounts/{id}/access/service_tokens`. The admin token can *read* service
tokens and Access apps but not create them.

Creating one through the dashboard would have meant reading a live client
secret into the agent's context to move it to the origin. The taskpack forbids
凭据泄露, and a real session makes the credential unnecessary, so that path was
not taken. It also avoids adding a non-human principal to an app whose only
policy today is the Owner's email allowlist.

## What was read, unmodified

`GET https://memoryatlas.linzezhang.com/api/v31/live-snapshot` → **HTTP 200**

| | |
|---|---|
| `run.run_id` / `trace_id` | `marun_5bd5fa6104b034eaf65bdee3` (identical) |
| `run.source_state` | `REBUILT_FROM_AUTHORITIES` |
| `run.source_completed_at` | 2026-08-03T17:31:57Z |
| `run.reconciled_at` | 2026-08-04T01:14:29Z |
| `analysis.event_count` | **122,080** |
| `analysis.event_window` | 2025-11-24T11:38:42Z → 2026-08-03T17:02:30Z |
| `visuals` | exactly 3: GRID, TREND, HEATMAP |
| `freshness.state` | STALE, age 27,753s against a 1,800s target |
| `coverage.product_state` | DEGRADED |

**Same-run evidence — all four PASS, all four carrying the same run and trace
id as the snapshot itself:** `r2_readback`, `private_database_readback`,
`ovh_reconcile`, `status_projection`, each referencing
`private-db://memory-atlas/runs/2026/08/03/marun_5bd5fa6104b034eaf65bdee3/manifest.json`.

**Privacy contract:** `raw_content_included`, `secret_values_included`,
`private_paths_included`, `object_keys_included` — all `false`. The served body
carries no object key, no absolute path and no digest other than the release
one.

**Tier accounting behaved as T06 specified:** Tier A 3/4 ready with
`github_private_release` FAILED, and because that row is
`required_for_product: false` the product degrades rather than failing. Tier B
5 ready / 2 failed / 3 missing, none of which is required for the product.

## The browser rendered the same run

`GET https://memoryatlas.linzezhang.com/` in the same session renders 记忆星图
with the panel showing the verification-debt trend over 118 days from
2025-11-24 to 2026-08-03 — the same window the API reports — with 债务 100.0%
and TTT 证据不足 per day, matching `verification_debt_proxy_event: 1.0` and
`time_to_truth_hours: null` in the payload.

## Verdict: PASS with one identity gap, now fixed

Everything the oracle checks about **run and trace** identity holds. What did
not hold is release identity: the snapshot reported
`release.identity_state: UNVERIFIED` with `release_id`, `repository_commit`,
`artifact_digest` and `deployment_revision` all null, so
`api_to_chart_oracle` and `same_run_oracle` had nothing to bind the release or
the deployment to.

That was a real omission rather than a data problem: the reconcile systemd unit
had no source for those values. `deploy-blue-green.sh` now writes
`shared/release-identity.env` at promotion and the unit reads it, so the next
promotion produces a snapshot that names its own release. Until that promotion
lands, `UNVERIFIED` is the honest value and the panel shows 未验证.

**T09 is therefore PASS on run/trace/privacy/visual/coverage and BLOCKED on
release identity until the next promotion.** It is not marked complete here.

## Update 2026-08-04 11:32 — the release identity gap is closed

Read through the Owner's own Access session, `GET /api/v31/live-snapshot` → 200:

| | |
|---|---|
| `release.identity_state` | **OBSERVED** |
| `release.release_id` | `20260804T111907Z-fa55d808fe90` |
| `release.repository_commit` | `fa55d808fe906a418c239a33183d44fa6c03a3e7` |
| `release.artifact_digest` | `e9eaaee962b2d88f300e9df5aa5cf0f1d2cffac109766d1effa0b5081992c37d` |
| `release.deployment_revision` | `20260804T111907Z-fa55d808fe90` |

The panel renders the same four values in its truth ribbon, so
`api_to_chart_oracle` and `same_run_oracle` now have a release and a deployment
to bind. **T09 is PASS, no longer BLOCKED.**

Closing it took two more defects beyond the missing unit source recorded above.
`MEMORY_ATLAS_ARTIFACT_DIGEST` was only ever read from the environment and
nothing ever set it, so every promotion wrote an empty value; it is now computed
over the promoted `dist`. And the promotion wrote `release-identity.env` *after*
restarting the services that read it, so every service a promotion started saw
the previous release — the snapshot named a release one promotion behind,
permanently. The identity file is now written before anything restarts.

The authority evidence also changed shape, because the data did:

```
canonical_source_readback  PASS
private_database_readback  PASS
ovh_reconcile              PASS
status_projection          PASS
r2_readback                NOT_RUN
```

R2 was drained on 2026-08-04 and the canonical event stream now lives in the
GitHub private repository, so `r2_readback` is honestly NOT_RUN and the
provider-neutral `canonical_source_readback` carries the gate. Tier A reads
4 ready / 1 failed of 5, the failure being `r2_primary_objects`, which is not
required for the product — so the page degrades rather than failing, which is
what it should do.

Event count unchanged at **122,080**, and `/memory_atlas.json` served to the
browser was regenerated at 2026-08-04T11:37:33Z with **505 sessions, 544 nodes,
1,691 edges** — the ten original views are reading the join, not the snapshot
baked into the release.
