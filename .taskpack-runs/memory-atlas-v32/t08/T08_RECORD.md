# v0.0.0.32 — T08 preview then reversible blue-green production deployment

Executed 2026-08-04. Authorization: **A2/A3** — reversible production, existing
blue-green script, no A4, no data-authority change, no access widened.

**Deployed release: `20260804T013334Z-fe2113d81a57`** (commit
`fe2113d81a57f8d134658c2197a9809f10ddc6d8`, CI green before every promotion).
Rollback target: `previous` → `20260804T010055Z-60d0b611a1f1`.

## The preview was already done

T05 and T06 ran the full chain against a preview whose origin is the **real**
`api_server.Handler` behind an edge that mirrors the production nginx config:
19/19 a11y and auto-revalidation, 28/28 API-to-chart, 8/8 degraded paths
including the 503 last-good case, 14/14 rollback both runtime and build-time.
Negative paths, auto-revalidation and time-regression refusal were all exercised
there, so T08 is the promotion itself.

## Five defects only a real deployment could find

Every one of them failed closed. Production was never left broken by a promotion
— the first attempt aborted before promoting, and the rest were correct at the
origin — but two of them meant the product was not actually working.

**1. `ModuleNotFoundError: jsonschema`.** `live_snapshot_store` imports it at
module load and `api_server` imports that, so the private API could not have
started. CI installed jsonschema in its own pip step, so the requirements file
being silent about it was invisible everywhere except a real host. Fixed, plus a
checker that walks every module in the serving package and requires each
non-stdlib import to be declared — with a test that removes `jsonschema` from
the declared set and asserts the checker flags it.

**2. The R2 dedup had broken the reconcile 2.5 hours earlier.** The OVH
reconcile had been FAILED since 21:35, the moment task 1 deleted the ten
whole-history rollups: the latest source manifest still names one of them, so
the reconcile saw a missing object and correctly opened a P0 incident. I proved
the union and the read-back before deleting but never re-ran the consumer. The
reconcile now tells *superseded* from *lost*, and only on evidence — the
canonical `MANIFEST.json` written at deletion time names all ten keys, and the
replacement must verify byte-for-byte first.

**3. The canonical object had no `sha256` metadata.** The dedup uploaded it with
a raw PUT; `exists_with_hash` checks user metadata before hashing, so the
replacement could never verify. Fixed with a server-side metadata rewrite: same
key, same 389,413,637 bytes, and a full download-and-hash then confirmed
`7b34a3d8…83bfa`.

**4. The first published snapshot had `event_count: 0`** while the same run had
counted 122,080. `build_behavior_analytics` deliberately keeps no raw payloads,
and the publisher was reading events from exactly there. A zero presented as the
current reading is the one thing the failure contract forbids. Both callers now
hand over the events they have, and the publisher raises rather than publishing
zeros. Handing over the real events then raised
`event[0].activity_type is required` — this repository says `activity`, the
v0.0.0.32 contract says `activity_type`, and `model_tool` does not exist here —
so events are projected explicitly, which also keeps `object_sha256`,
`relative_path` and `payload` away from the browser.

**5. The browser had been served a 2026-08-03T20:16 build through every
promotion since.** The web container bind-mounts `$APP_ROOT/current/dist` and
Docker resolves that symlink to an inode at container start; `docker compose up
-d` left the running container alone. Measured: the release directory held
`index-dYZiJt-h.js` while the container answered with `index-D64YPfUn.js`, a
bundle containing none of the v0.0.0.32 panel. This is the same shape as the
index.html caching bug fixed in v0.0.0.31 — correct at the origin, invisible to
the user — so it got the same treatment: promotion forces recreation, and
post-promote compares released asset names against served asset names and exits
7 when they differ.

**Also:** the fifth promotion died mid-rsync with "No space left on device".
Each agent release is a ~770 MB copy and nothing pruned them; eight had
accumulated on a 38 GB disk. Promotion now prunes everything the rollback
contract cannot reach — before copying, so the space is free when it is needed —
with `current` and `previous` exempt by name.

## What is true in production right now

`live-snapshot/current.json`, published by the OVH reconcile from the
authorities:

| | |
|---|---|
| run | `marun_5bd5fa6104b034eaf65bdee3`, `REBUILT_FROM_AUTHORITIES` |
| events | **122,080** |
| window | 2025-11-24T11:38:42Z → 2026-08-03T17:02:30Z |
| freshness | **STALE** — source capture last succeeded 2026-08-03T17:31, past the 1800s target |
| product | **DEGRADED** |
| 主要用途 | 开发与部署 — 50,430 events, 41.3% |
| 现实结果 | 0 已验证结果 — event basis 0%, denominator 122,080 |
| 最大缺口 | 验证债务代理 100.0% |
| visuals | contribution 7 rows, debt trend 112 rows, heatmap 67 rows |

The verified-outcome rate of 0 is not a bug — no captured event carries a
verified outcome state. That is precisely the gap the panel exists to show, and
it is the honest reading.

## Deployment identity and rollback

`DEPLOYMENT_RECEIPT.json` records the promoted release, its commit, both
`current` and `previous` for the app and agent trees, the released asset names,
the asset names the container actually answers with, and the post-promote probe.
Rollback is the existing `ops/memory-atlas/rollback.sh` against `previous`.

## What is NOT claimed

`live_snapshot_probe: NOT_RUN`. The origin sits behind Cloudflare Access and
there is no service-token pair here, so the authenticated end-to-end read has
not been performed. Through an SSH tunnel that bypasses Access the deployed page
loads with 13 nav items and the panel present, showing
`实时快照读取失败（HTTP 403）` — the correct fail-closed state for an
unauthenticated caller, not the Owner's view.

**The authenticated golden transaction is T09 and it needs the Owner's
Cloudflare Access session.** It is not marked done here.
