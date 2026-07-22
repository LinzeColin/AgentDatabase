# Evidence model

## Contents

1. Fidelity layers
2. Capture routes
3. Evidence labels
4. Exhaustive-frame protocol
5. Failure boundaries

## 1. Fidelity layers

“The agent sees the same thing as a person” is not one condition. Preserve five
separate layers and never substitute one for another.

| Layer | Evidence | What it proves | What it does not prove |
|---|---|---|---|
| Encoded source | original file, SHA-256, container/stream metadata | which bytes were analyzed | decoded pixels or playback behavior |
| Decoded timeline | every decoded frame, PTS/duration, color metadata, audio | pixels/samples emitted by a named decoder in presentation order | how a player/display rendered them |
| Presentation | player/runtime, compositor, viewport, scale, display refresh/profile, accessibility settings | the target viewing context | hidden interaction semantics or physical sensation |
| Interaction | input events, state transitions, DOM/native hierarchy, animation/runtime telemetry | trigger-to-state behavior and latency | unavailable source-side logic or device haptics |
| Human experience | calibrated A/B review, device test, preference/acceptance record | Owner-perceived fidelity in a declared setup | universal identity for every viewer/device |

Lossless PNG means “lossless after decode and color conversion performed by the
toolchain”. It does not recover information already removed by video compression and
does not guarantee the same HDR tone mapping as the original player.

## 2. Capture routes

### SOURCE_INSTRUMENTED

Use when source code and a runnable artifact are available. Capture video plus:

- element/native hierarchy and stable identifiers;
- computed style/layout and asset/font references;
- CSS/WAAPI/native animation keyframes, timing and current state;
- pointer, touch, keyboard, focus, scroll and drag events;
- application state transitions, network boundaries and performance timestamps;
- deterministic replay data and environment versions.

This is the strongest route because it records causes and rendered effects.

### URL_INSTRUMENTED

Use for a controllable webpage without source access. Prefer Playwright/CDP and an
authorized rrweb-style event stream. Record cross-origin, canvas, WebGL, video,
Shadow DOM and privacy limitations explicitly.

### VIDEO_ONLY

Use when the video is the only source. Recover observable states and timing; mark
these as unresolved unless independently evidenced:

- exact DOM/component hierarchy;
- the trigger behind visually similar changes;
- hover versus programmatic animation;
- scroll-position versus time-driven clocks;
- off-screen states and error/cancellation branches;
- exact font files, vector paths, shader source and 3D geometry;
- physical haptic waveforms.

### OFFLINE_CONCEPT

Use for concept/marketing/offline renders. Preserve the aesthetic reference while
declaring production ceilings. Do not assign a generic “70–85%” ceiling without an
actual target/runtime assessment; record per-axis feasible, risky and unobservable
items instead.

## 3. Evidence labels

Apply one label to every important statement or number:

- `[O] observed`: directly visible/audible or present in a runtime trace.
- `[M] measured`: include tool/method, units, evidence range and repeatability.
- `[I] inferred`: include confidence, competing explanations and impact if wrong.
- `[D] decided`: an Owner/product choice, even if the analyzer proposes a default.
- `[U] unobservable`: cannot be recovered from supplied evidence.

For computed quantities, retain provenance:

```yaml
duration_ms:
  value: 420
  label: M
  method: per_element_track_v2
  evidence: [frame_00124, frame_00149]
  estimator_agreement: [421, 417]
  uncertainty_ms: 17
```

## 4. Exhaustive-frame protocol

An exhaustive claim requires all conditions:

1. Hash the encoded source.
2. Decode one selected video stream without FPS resampling.
3. Export frames in decoded presentation order at native dimensions.
4. Record each frame's best available PTS and duration.
5. Require extracted count = decoded timeline count.
6. Hash every exported frame and map it to the timeline.
7. Review every unique exact frame in bounded batches.
8. Map exact duplicates by hash to an explicitly reviewed representative.
9. Leave near-duplicates separate; they may encode motion/easing.
10. Fail if any frame is missing, unreadable, unmapped or unreviewed.

Exhaustive extraction is expensive. For long references, use balanced discovery,
then losslessly clip critical windows and exhaustively review those windows. State
the exact temporal coverage; do not imply whole-video coverage.

## 5. Failure boundaries

- A scene-change sampler is not a coverage proof.
- A contact sheet is navigation, not full-resolution evidence.
- Whole-frame motion energy can locate activity but cannot identify the moving
  element or its individual easing.
- Aggregate mean scores can hide one catastrophic frame or interaction.
- A clean fit can still measure an occluder, page scroll, compression artifact or
  the wrong element. Require a second independent estimator for critical values.
- Playback speed is not reliably recoverable from ordinary stream metadata. Use
  visible player evidence, recording context or Owner confirmation.
- Actual haptics require device/API telemetry or an on-device test. Audio/visual
  cues are only proxies.
- “Surpass” is invalid unless the reference-critical gates still pass and the
  improvement axis is selected and measured separately.
