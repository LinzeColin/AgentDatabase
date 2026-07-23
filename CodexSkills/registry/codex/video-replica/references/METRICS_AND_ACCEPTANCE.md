# Metrics and acceptance

## Contents

1. Calibration first
2. Fidelity vector
3. Temporal and motion formulas
4. Interaction and multimodal gates
5. Surpass gate
6. Stop conditions

## 1. Calibration first

Do not use universal SSIM, LPIPS, pixel-diff or VMAF thresholds as truth. First
capture the same reference/runtime at least twice under the declared environment.
The resulting distribution is the measurement noise floor from font rasterization,
video decode, scheduling, capture and platform variance.

For an error metric where lower is better, define a project threshold from the
self-recapture baseline:

```text
threshold_error = max(engineering_floor, baseline_error_q95 × noise_multiplier)
```

Start `noise_multiplier` at `1.5` only as a provisional calibration parameter. For
a similarity metric where higher is better:

```text
threshold_similarity = baseline_similarity_q05 - allowed_margin
```

Record all raw values and the chosen margin. Never tune a threshold after seeing a
candidate merely to make it pass.

## 2. Fidelity vector

Keep these dimensions separate:

| Dimension | Minimum evidence | Gate shape |
|---|---|---|
| Coverage | decoded/extracted/reviewed counts and hashes | all critical evidence accounted for |
| Static visual | pixel diff, SSIM and optional LPIPS on aligned anchors | mean plus worst frame/region |
| Temporal | onset, duration, hold, stagger, loop and phase | per critical event |
| Motion | position/transform trajectory, velocity, acceleration, settle/overshoot | per element, not whole-frame aggregate |
| Interaction | state/transition coverage and functional replay | 100% of critical transitions |
| Responsiveness | input-to-feedback and input-to-settle latency | distribution plus worst critical case |
| Runtime | dropped/duplicated frames, long tasks/jank, errors | no unexplained critical failure |
| Audio | onset/offset, event sync, channel presence, loudness relation | per critical cue |
| Accessibility | focus, keyboard, reduced motion, readable state | selected product requirements |
| Human | blinded A/B or synchronized side-by-side review | Owner acceptance with residual list |

Never compress the table into a single pass score. A product may have excellent
static similarity and still fail interaction or motion.

## 3. Temporal and motion formulas

Use the coarser observable frame interval as the default timing uncertainty:

```text
frame_uncertainty_ms = max(1000 / source_effective_fps,
                           1000 / target_capture_fps)
onset_error_ms       = abs(candidate_onset_ms - reference_onset_ms)
duration_error_ratio = abs(candidate_duration - reference_duration)
                       / max(reference_duration, epsilon)
```

For critical events, begin with an onset tolerance of one
`frame_uncertainty_ms`; tighten only when runtime telemetry provides sub-frame
timestamps. Do not claim 5 ms accuracy from a 30 fps recording.

For an element track sampled at aligned times `i = 1..N`:

```text
trajectory_nrmse = sqrt(mean((p_candidate_i - p_reference_i)^2))
                   / max(reference_path_length, 1 px)
velocity_rmse    = sqrt(mean((v_candidate_i - v_reference_i)^2))
phase_drift_ms   = max_i abs(t_candidate_feature_i - t_reference_feature_i)
```

Report x/y/scale/rotation/opacity/filter channels separately when they drive the
perception. Include overshoot amplitude, time-to-peak and settle time for springs.
Only fit easing after a stable element/region is tracked and a second method agrees.

## 4. Interaction and multimodal gates

For every critical interaction, require:

1. declared precondition and deterministic input;
2. immediate feedback state;
3. intermediate transition states;
4. final state and cancellation/error variants when demonstrated;
5. input-to-first-feedback and input-to-settle latency;
6. pointer/touch/keyboard/focus coverage appropriate to the target;
7. audio cue alignment when present;
8. `UNOBSERVABLE` for physical haptics without telemetry.

Use a state-transition table, not prose alone. A transition passes only when both
functional state and declared visual/motion gates pass.

For audio-video sync:

```text
av_sync_error_ms = abs(candidate_audio_event_ms - candidate_visual_event_ms
                       - reference_audio_visual_offset_ms)
```

Calibrate the capture/audio pipeline before applying a threshold.

## 5. Surpass gate

Treat “surpass” as Pareto improvement, not aesthetic assertion:

1. Pass every Owner-selected reference-critical fidelity gate.
2. Select at least one improvement axis before implementation, such as lower input
   latency, smoother low-end performance, responsive adaptation, accessibility,
   clearer error recovery, reduced motion alternative or lower asset cost.
3. Define a measurement and minimum meaningful change for that axis.
4. Demonstrate no unacceptable regression on fidelity, function or accessibility.
5. Record Owner preference/acceptance separately from automated metrics.

Do not call extra particles, stronger easing, more blur or longer animation an
improvement unless it passes the selected product outcome.

## 6. Stop conditions

Stop and label the pack instead of guessing when:

- source/frame/hash/timeline coverage disagrees;
- HDR or color-managed material lacks a declared viewing pipeline;
- playback speed or time-vs-scroll clock changes critical implementation choices;
- per-element estimates disagree beyond one observable frame or the calibrated
  spatial noise floor;
- a critical state/interaction is not present in the evidence;
- haptic fidelity is requested without device telemetry/on-device testing;
- reference and candidate cannot be rendered in a controlled comparable setup;
- Owner decisions remain unresolved.
