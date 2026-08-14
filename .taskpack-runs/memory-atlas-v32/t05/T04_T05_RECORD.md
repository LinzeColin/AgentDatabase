# v0.0.0.32 — T04 protected API and T05 home-page wiring

Executed 2026-08-04 on `main`. Authorization exercised: **A1/A2** (isolated,
reversible, preview only). No production surface was touched by this slice.

## Correction: T04 was not closed when I said it was

The previous commit (`cd8bfafc`) applied `api_live_snapshot.py` and its tests,
and I marked T04 done. It was not: `api_server.py` had **no route**, so nothing
could ever reach the module. T04's own wording is "将 api_live_snapshot.py 语义接
入现有 BaseHTTPRequestHandler" — applying the file is not the wiring. Reopened,
wired, and tested before T05 was started.

## T04 — classification `apply`

`Handler.do_GET` now serves `/api/v31/live-snapshot` **after** the existing
Cloudflare Access gate that already covers every `/api/v31/` path. No second
authentication path was introduced; `authorized=True` is passed only because an
unauthenticated request has already returned 403 above it. A `_raw` writer emits
the helper's own headers verbatim, because `_json` would rebuild them and drop
the ETag and the four identity headers the browser cross-checks.

`OpenAIDatabase/tests/test_memory_atlas_live_snapshot_api_v32.py`, 6 tests:

| Test | Proves |
|---|---|
| `…never_anonymously_readable` | 403 with no assertion **and** with a forged one |
| `…without_a_published_snapshot_is_404` | 404 `live_snapshot_not_available` |
| `…invalid_current_snapshot_is_503_not_a_partial_200` | authority-evidence mismatch never renders |
| `…served_with_matching_identity_headers` | 200; header run/trace/release/deployment == body; `no-store`; ETag |
| `…unverified_release_identity_is_reported_not_omitted` | `UNVERIFIED`, not a missing header |
| `…served_body_carries_the_privacy_contract` | privacy flags false; no object keys or private paths |

## T05 — classification `apply`

- `LiveSnapshotProvider` mounts inside the **existing** `AppProviders` stack.
  `App.tsx` is still byte-identical to the frozen baseline; there is still one
  Shell and one Router; `V31App` is still unmounted.
- `RealityCalibrationPanel` renders as the **first** block of the existing
  `HomeOverviewView`, above the historical graph sections
  (`live_panel_precedes_historical_views` in the audit receipt).
- `liveSnapshotFeature.tsx` is the rollback switch. Off ⇒ the provider never
  mounts, so no request is made at all, and the panel is absent.

### Two adaptations, both recorded rather than silent

1. **Truth Ribbon moved below the four conclusions.** As shipped, the ribbon sat
   between the header and the answer grid and pushed the conclusions to y=906 on
   a 1440×900 screen — off the first screen, which
   `UI_UX_VISUAL_CONTRACT.md` ("四个现实结论在上") forbids. The ribbon still
   renders on every render, in full, immediately under the conclusions.
2. **First-screen budget CSS.** An appended block in
   `RealityCalibrationPanel.css` compacts only `.ma-reality-panel`, and makes the
   answers 4-across at panel widths > 1060px. The shipped rules are unchanged
   above it.

### Measured first-screen fit

The pre-existing v0.0.0.31 chrome consumes **435px** before `.view-surface`
begins (topbar 56 + controls 36 + interaction lens 45 + command palette 152 +
spacing). That is the dominant cost, not the panel.

| Viewport | Conclusions top → bottom | All four fully visible |
|---|---|---|
| 1920×1080 | 651 → 801 | yes |
| 1512×945 | 651 → 818 | yes |
| 1440×900 | 650 → 814 | yes |
| 1280×800 | 638 → 798 | yes |
| **1366×768** | **634 → 796** | **no — 28px short** |

1366×768 is reported, not hidden. Closing it needs the shared chrome above the
view surface to shrink, which is outside "只在现有 AppProviders 与
HomeOverviewView 第一屏接入" and would touch all ten original views.

### Regression found and fixed while auditing mobile

At ≤720px the existing topbar declares
`.topbar-actions { display:grid; grid-template-columns: minmax(0,1fr) 32px }`,
written for two children. v0.0.0.31 added `ThemeControls` as a third child, so
`.stat-strip` fell into the 32px column: the four counters measured **32px wide
by 116px tall** — the vertical, clipped text the Owner reported as 乱码出格. The
controls now take their own row. After the fix, at 375px each counter is
**50×46** and horizontal overflow is 0.

## Evidence in this directory

| File | Verdict |
|---|---|
| `BROWSER_RECEIPT_PREVIEW.json` | 200, identities match across API header / API body / DOM, 0 console errors, 0 failed requests |
| `API_TO_CHART_PREVIEW.json` | **PASS**, 28 checks, 0 mismatches |
| `A11Y_AUDIT_PREVIEW.json` | **PASS**, 19/19 |
| `ROLLBACK_RUNTIME_FLAG.json` | **PASS**, 14/14 — panel absent, zero live-snapshot requests, ten views render |
| `ROLLBACK_BUILD_FLAG.json` | **PASS**, 14/14 — same, from a bundle built with `VITE_MEMORY_ATLAS_LIVE_SNAPSHOT=0` |
| `browser-v31/`, `browser-preservation/` | 13 routes and all ten original views still pass |
| `screens/` | first screen at 1440×900 and 375×812 |

### What the audit actually measured

`auto_revalidates_within_60s` waited a real 66 seconds and counted a second
request. `online_event_revalidates_immediately` dispatched a real `online` event
and saw a third. `older_run_is_refused` rewrote the origin's `current.json` to
run `regression-run-19700101T000000Z`, clicked 刷新事实, and confirmed the panel
still carried the newer run and surfaced 「服务器返回更旧快照，已拒绝时间倒退」.
`reduced_motion_is_honoured` read computed `transition-duration` under
`prefers-reduced-motion` (1e-05s). `mobile_has_no_horizontal_overflow` compared
`scrollWidth` to `clientWidth` at 375px and listed zero offending nodes.

## Preview shape, stated plainly

The preview origin is the **real** `api_server.Handler` with the Cloudflare
Access verifier swapped for a fixture, fronted by a node edge that mirrors
`ops/memory-atlas/nginx/default.conf` and injects the assertion the way Access +
Traefik do. Every other byte of the request path is production code. The
snapshot served is `fixtures/live_snapshot.synthetic.json`, which is labelled
synthetic and is **not** a production claim. The real golden transaction against
real events behind a real Access session is T09, and is not claimed here.

## Governance changes this slice required

- `verification_policy.json`: the new test file registered under the
  `integration` tier; the pinned `test_file_count` moved 83 → 84 in
  `test_verification_policy.py`.
- The oracles live in `OpenAIDatabase/scripts/memory_atlas_acceptance/` rather
  than a new top-level `acceptance/`: `directory_lifecycle` caps
  `current_top_level_count_including_root` at 15 and a new top level made it 16.
  Their `ROOT` was moved from `parents[1]` to `parents[2]` accordingly.
- `validate_existing_memory_atlas_preservation_browser.cjs` asserted
  `navCount === 10`. It was written before the Owner-approved v0.0.0.31
  integration added three views to the same nav, so a correct product now failed
  it. It asserts the ten originals are all present (`originalNavCount === 10`)
  with `navCount >= 10`; every one of the ten is still clicked and rendered
  individually.

## Known local-only failures, not caused by this slice

`test_old_automation_is_archived_verified_then_immediately_paused` and
`test_new_automation_install_and_retirement_gates` fail on this machine with
`ModuleNotFoundError: No module named 'tomllib'` — the system interpreter is
Python 3.9.6 and `tomllib` is 3.11+. `ops/memory-atlas/automation_lifecycle.py`
is untouched by this slice, CI pins Python 3.13, and the same three calls were
re-run here under Python 3.12 and returned
`ARCHIVED_VERIFIED_AND_PAUSED` / `PASS` / `True`.

Backend suite otherwise: **537 passed, 2 failed (both the above)**.
