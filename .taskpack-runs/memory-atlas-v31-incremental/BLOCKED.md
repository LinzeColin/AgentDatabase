# Not done, and why — Memory Atlas v0.0.0.31 incremental integration

Everything below is stated as the fact that was observed. Nothing here is
reported as PASS, and nothing was worked around.

## Discovered deployment chain (facts, no guessing)

| Fact | Evidence |
|---|---|
| Frontend platform | Cloudflare Pages project `openai-memory-atlas` |
| Production hostname | `memoryatlas.linzezhang.com` → CNAME `openai-memory-atlas.pages.dev`, proxied (`_protected/operate_discovery_20260718/domain_origin_map.csv`) |
| Edge auth | Cloudflare Access, team domain `tiny-scene-b867.cloudflareaccess.com` |
| Unauthenticated deny | `GET https://memoryatlas.linzezhang.com/` → **302** to the Access login. Same for `openai-memory-atlas.pages.dev` and `/api/v31/status`. Fail-closed confirmed. |
| Status projection | `https://status.linzezhang.com/` → 200 |

## BLOCKED-1 — post-promotion verification on the real user path (AC-018, P0)

`memoryatlas.linzezhang.com` sits behind Cloudflare Access. Reaching the
application requires the owner's identity; I have none, and bypassing Access is
not something I will attempt. The thirteen-route, six-theme-mode probe therefore
**cannot be executed against production by me**.

Because AC-018 is P0 and the contract is `fail_closed: true`, a positive release
verdict is not reachable from this session. Promoting anyway would mean writing
an unverified user path down as a production success, which the taskpack
forbids outright. **No deployment was performed.**

What is available for the owner to run after promotion: the same probe used
locally, pointed at the production origin —
`MEMORY_ATLAS_BASE_URL=https://memoryatlas.linzezhang.com npm run validate:v31:browser`
from an authenticated browser profile.

## BLOCKED-2 — source runner is SOURCE_RUNNER_UNBOUND, by owner decision (AC-013)

`crontab -l` → `no crontab for linzezhang`. The bounded 30-minute wake-up is
**not installed**, which by AC-013's own oracle is `SOURCE_RUNNER_UNBOUND`, not
a pass.

The taskpack assumed `codex_enabled: false` and treated the generic runner as the
replacement daily path. That assumption does not hold: the owner states the Codex
automation is running normally and instructed that no local scripts be run on the
machine. `manage_crontab.py install` was therefore **not** executed — binding it
would have added a second daily-capture scheduler beside a working one.

So this is a deliberate configuration choice, not an unmet gate: the live daily
path is the existing Codex automation, and the generic runner ships as a proven
but unbound alternative. Its logic is covered by seven regression tests
(`OpenAIDatabase/tests/test_memory_atlas_source_runner_v31.py`), including the
local-calendar-day semantics that the upstream taskpack suite got wrong.

No launchd agent was created; `~/Library/LaunchAgents` contains no Memory Atlas
entry, as required.

## BLOCKED-3 — private data spine cannot be exercised for real (AC-011, AC-012, AC-017, P0)

No R2 or GitHub credentials are present in this session:
`MEMORY_ATLAS_R2_ENDPOINT`, `MEMORY_ATLAS_R2_BUCKET`, `CLOUDFLARE_API_TOKEN`,
`CLOUDFLARE_ACCOUNT_ID`, `GH_TOKEN` and `GITHUB_TOKEN` are all unset, and
`~/.aws/credentials` does not exist. Only slot *names* were read; no value was
opened, copied or written anywhere.

Consequently there was **no** real source capture, **no** R2 upload/read-back,
**no** Private-Database fact commit and **no** isolated restore drill in this
session. Those four remain unproven on live infrastructure. The code paths are
covered by the 81 existing spine tests, which is a different and weaker claim.

## BLOCKED-4 — legacy Codex Automation retirement: withdrawn (AC-014)

`~/.codex/automations/memory-atlas-daily-source-capture/` exists
(`automation.toml`, `memory.md`; last modified 2026-08-03 18:56).

AC-014 assumed this automation had failed and should be retired. The owner
states it is running normally and instructed that it be left alone, so the
retirement objective is withdrawn rather than blocked. **Nothing was archived,
paused, moved or deleted**, and no local script was run against it.

Independently of that instruction the sequence could not have started: AC-014
permits removal only after archive → hash-verify → pause → six replacement gates,
and those gates depend on BLOCKED-2 and BLOCKED-3.

## Owner instructions honoured during this run

- Claude Code session memory was **not** uploaded, committed, or added to
  `ops/memory-atlas/source-registry.json`. The registry's source list is
  unchanged; only the additive `source_runner` policy line was added to it.
- No local script was run against the machine's configuration: no crontab
  install, no automation lifecycle command, no launchd, no deployment.

## Divergences found in the taskpack itself

1. `tests/test_source_runner.py::test_success_runs_at_most_once_per_local_calendar_day`
   **fails on this machine**. It feeds `2026-08-03T22:00:00+00:00` and expects a
   same-day skip, but the host is AEST (+10:00), where that instant is already
   2026-08-04 locally. `run_due.py` is correct — it follows the local calendar as
   documented — the test is timezone-fragile and only passes on a UTC runner.
   The taskpack's "每日源端调度 3/3 通过" therefore holds only under UTC. The
   repo's copy of these tests pins `TZ` per run and adds an explicit
   UTC-vs-Australia/Sydney case so the distinction cannot regress.
2. `tests/test_apply_incremental.py::test_apply_is_incremental_idempotent_and_preserves_data`
   fails because its synthetic fixture repo has no `node_modules`, so
   `require("typescript")` cannot resolve. Environmental; no bearing on this repo.
3. `MemoryAtlas/scripts/validate_memory_atlas_v31.cjs` was **already failing on
   `origin/main` before any of this work**: `UI-008` asserted
   `app.includes("V31App")`, the architecture the owner has since frozen as
   forbidden. It is not in CI, so the failure was invisible. It is now green
   against the shipped implementation.
4. `MemoryAtlas/public/` does not exist in this repository, although the taskpack
   lists it as a protected path. It is inventoried as absent before and after
   rather than created.
