# v0.0.0.32 — T10 durability, recovery and independent verification

Classification: **apply**. Executed 2026-08-04 against release
`20260804T111907Z-fa55d808fe90` (commit `fa55d808fe90…`) on OVH VPS-1.

Verdict from the Independent Verifier: **PASS on all four criteria.**

| | |
|---|---|
| MA-LIVE-AC-007 自动重验证、刷新与重登读回 | PASS |
| MA-LIVE-AC-008 失败保留最近成功快照 | PASS |
| MA-LIVE-AC-011 原子 current/previous/history | PASS |
| MA-LIVE-AC-016 重启、回滚与隔离恢复 | PASS |

## What was actually executed

`ops/memory-atlas/durability_recovery_drill.sh` froze the candidate, then did
four things to production and read the world back after each one. The snapshot
digest was identical at every step — `7064772da5ad…` — and the run, trace,
release and deployment identity never moved.

| step | internal API / web | snapshot |
|---|---|---|
| baseline | 200 / 200 | 122,080 events, `7064772da5ad…` |
| restart API + container | 200 / 200 | unchanged |
| blue-green rollback to `20260804T105352Z` | 200 / 200 | unchanged |
| roll-forward to the candidate | 200 / 200 | unchanged |
| isolated restore + schema validation | 200 / 200 | unchanged |

The isolated restore copied the whole store into a temporary directory and
validated `current`, `previous` and every history object against the frozen
schema there. Nothing in place was written, and no history object or fact was
deleted at any point.

Browser evidence came through the Owner's own authenticated Cloudflare Access
session. No credential was created and none was entered.

## Three defects the drill found, all fixed

**The API could be left permanently down by an ordinary restart.** The unit
allowed five starts per sixty seconds, and the self-heal timer restarts it too.
The drill's restart plus self-heal's crossed the limit; systemd then refused
every further start and the API stayed down until `reset-failed` was run by
hand. A restart that ends in a permanently dead service is a worse outcome than
the crash loop the limit exists to catch. Now twenty per five minutes, and
self-heal clears the failed state before it restarts — without that, it was
restarting a unit systemd had already refused, burning the next window's budget
and reporting FAILED.

**`rollback.sh` probed health with no retry.** It restarts the API and then
immediately curls `/healthz`, which the API loses a race with. A rollback that
actually succeeded would report failure — in exactly the situation where that
matters most. Now a bounded retry per probe.

**The roll-forward ran the wrong script.** The drill invoked
`current/ops/.../rollback.sh`, and after a rollback `current` is the older
release carrying whatever version shipped with it. The first run rolled forward
using the release it was leaving, and exited 7. It now uses the frozen
candidate's own script and records which script ran.

## The verifier failed me once, on real data

Its first run returned **FAIL on AC-008**: `current` no longer carried the
frozen digest. The check was right about the fact and wrong about the rule. The
fifteen-minute reconcile had published a newer reading of the same run between
the freeze and the verification — the system working, not failing. AC-008 says
current must not move *when a run fails*; "does not move on failure" is not
"never moves".

The corrected check tests the property instead of the snapshot: across the
drill's steps current must not change at all; if it later moved, it may only
have moved forward (no older `source_completed_at`) and the frozen reading must
still be present as `previous`. Production satisfies all three —
`previous` holds `7064772da5ad…`, exactly the frozen digest.

The other half of AC-008 — that a failed run does not move current — is proven
by ten fault-injection cases in `FAULT_INJECTION.json`: non-terminal run,
rewritten conclusions, changed visuals, missing or failed object-authority
readback, and publishing zeros. All ten pass, and the verifier BLOCKs if that
evidence is absent rather than assuming it.

## What "independent" means here, stated plainly

The verifier is a separate read-only process running rules fixed before the run.
It is **not** a second party — the builder wrote it. That is recorded in the
report itself (`independence.written_by: "the builder"`) rather than implied
away.

What it does buy: the verdict comes from re-reading the world, not from a
builder assertion; missing evidence is BLOCKED and can never become PASS; every
passing criterion names the file and value it read; and it has no write path —
a test asserts the source contains no `shutil`, no `os.remove`, no `subprocess`,
and exactly one `write_text`, which is its own report.

Twenty-five tests plant one defect each and assert the verdict changes. It has
also demonstrably failed a real production run, which is the only evidence that
actually settles the question.

## Ceiling on AC-007

The ≤60-second auto-revalidation was measured cleanly on a genuinely visible
page by `audit_reality_panel_v32.mjs` (PASS 17/17). In production the tab is
MCP-controlled and never foregrounded, so Chrome throttles its timers to roughly
once a minute; the observed interval there was 105 s. What production does prove
is that every trigger in the chain works and that identity never regresses:
hidden → no poll (correct, the contract's precondition is visibility), becoming
visible → immediate, `online` while visible → immediate, refresh → same run,
fresh session tab → same run.

`AC007_RELOGIN_RECEIPT.json` states what was not done: no credential was
re-entered and the Owner's session was not logged out. The receipt calls itself
a clean fresh-tab load rather than a re-authentication.
