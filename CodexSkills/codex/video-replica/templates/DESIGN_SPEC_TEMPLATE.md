ACTION: STOP

# <project> evidence-backed experience specification v<N>

- Status: `BLOCKED_OWNER_REVIEW`
- Reference: `<source path/hash>`
- Evidence route: `<SOURCE_INSTRUMENTED|URL_INSTRUMENTED|VIDEO_ONLY|OFFLINE_CONCEPT>`
- Coverage: `<exhaustive whole clip|exhaustive windows|balanced>`
- Target: `<runtime/device/viewport>`
- Evidence labels: `[O] observed | [M] measured | [I] inferred | [D] decided | [U] unobservable`
- Truth statement: `<what this pack proves and explicitly does not prove>`

## 0. Gate summary

| Gate | Status | Evidence/blocker |
|---|---|---|
| Encoded source hash | | |
| Decoded timeline ↔ extracted frames | | |
| Full-resolution review coverage | | |
| Presentation/color context | | |
| Critical interactions evidenced | | |
| Owner decisions | | |
| Validation environment defined | | |

Downstream builder may start only when every critical gate passes and package status is
`OWNER_CONFIRMED`.

## 1. Capture and evidence coverage

### 1.1 Source/presentation facts

Link `capture_context.yaml`, `probe_summary.json`, `frame_timeline.csv` and
`EVIDENCE_MANIFEST.sha256`. Record decoder/tool versions.

### 1.2 Coverage ledger

| Scope | Decoded | Extracted | Unique hashes | Reviewed | Unresolved |
|---|---:|---:|---:|---:|---:|
| Whole clip / window | | | | | |

### 1.3 Known ceilings

- `[U]` `<hidden state, source asset, haptic, HDR presentation, off-screen branch, etc.>`

## 2. Owner plain-language check

Write 8–15 observable statements without implementation jargon. Cover start, main states,
critical transitions, input feedback, audio, ending/loop and overall feel.

| # | Observation | Evidence | Confirm | Correct/notes |
|---|---|---|---|---|
| 1 | | | ☐ | |

## 3. Reference role → target role mapping `[D]`

| Reference role/state | Evidence | Proposed target mapping | Owner decision |
|---|---|---|---|
| | | | ☐ accept / change: |

## 4. Scene graph and state model

### 4.1 Stable element hierarchy

```yaml
elements: []
occlusion_and_z_order: []
unknowns: []
```

### 4.2 State graph

```text
<state> --<input/condition>--> <feedback> --> <transition> --> <state>
```

Include loading, error, cancellation, reduced-motion and responsive variants only when
evidenced or explicitly selected as product requirements.

## 5. Design tokens

Keep the canonical machine copy in `design_tokens.yaml`.

```yaml
color: {}
typography: {}
spacing: {}
shape: {}
shadow_blur_material: {}
assets_fonts: {}
```

Record sampling method, source frame/region, color pipeline and uncertainty. Compression
colors are observations of the decoded reference, not necessarily authored tokens.

## 6. Motion registry

Keep the canonical machine copy in `motion_registry.yaml`.

| id | target | clock | trigger | start/duration | trajectory/properties | easing/spring | evidence/method | uncertainty |
|---|---|---|---|---|---|---|---|---|
| | | time/scroll/input/audio/physics | | | | | | |

For each critical motion include delay, hold, stagger, loop/yoyo, overshoot, settle,
interrupt/cancel behavior and reduced-motion alternative. Do not report aggregate
whole-frame easing as per-element fact.

## 7. Interaction registry

Keep the canonical machine copy in `interaction_registry.yaml`.

| id | pre-state | input | immediate feedback | transition | post-state | latency | modalities | evidence |
|---|---|---|---|---|---|---|---|---|
| | | | | | | first/settle | pointer/touch/key | |

## 8. Audio and sensory registry

Keep the canonical machine copy in `audio_registry.yaml`.

| id | channel/cue | onset/offset | synchronized visual/input event | evidence | status |
|---|---|---|---|---|---|
| | | | | | |

- Physical haptic waveform: `<telemetry evidence or [U]>`
- Visual/timing “feel” drivers: `<measured drivers>`

## 9. Technical route and ceiling `[D]`

| Requirement | Candidate substrate | Why | Ceiling/risk | Fallback |
|---|---|---|---|---|
| | CSS/WAAPI/GSAP/Motion/Lottie/Rive/Canvas/WebGL/native | | | |

Include performance, accessibility, asset/license, responsive and device constraints.

## 10. Validation contract

Keep the canonical machine copy in `validation_contract.yaml`.

### 10.1 Deterministic replay

- Runtime/browser/device and versions:
- Viewport, DPR, refresh/capture FPS and color pipeline:
- Fonts/assets/data/network/clock controls:
- Ordered input script:
- Reference/candidate alignment rule:
- Self-recapture calibration runs:

### 10.2 Fidelity gates

| Dimension | Metric/evidence | Calibration/threshold | Mean | Worst | Pass |
|---|---|---|---:|---:|---|
| Coverage | | | | | |
| Static visual | pixel/SSIM/optional LPIPS | | | | |
| Temporal | onset/duration/phase | | | | |
| Motion | trajectory/velocity/settle | | | | |
| Interaction | critical transition coverage | 100% critical | | | |
| Runtime | dropped/duplicated/jank/error | | | | |
| Audio | sync/onset | | | | |
| Human | blinded A/B + residual list | Owner | | | |

### 10.3 Surpass contract `[D]`

| Selected improvement axis | Baseline | Minimum meaningful change | No-regression gates | Owner decision |
|---|---|---|---|---|
| | | | | ☐ |

Do not claim surpass until all reference-critical gates pass.

## 11. Residual differences and decisions

| id | Difference/unknown | Severity | Evidence | Decision/owner | Status |
|---|---|---|---|---|---|
| | | | | | |

## 12. Runner card for the builder

```text
Role: implement only the OWNER_CONFIRMED spec.
Inputs: this pack and declared target repo/runtime.
Non-goals: reinterpret Owner decisions; invent missing motion/haptics; relax gates.
Loop: implement one bounded state/transition -> deterministic capture -> verifier diff -> fix.
Stop: critical evidence gap, environment drift, gate regression, or selected run complete.
Handoff: implementation artifacts plus raw validation evidence to an independent verifier.
```
