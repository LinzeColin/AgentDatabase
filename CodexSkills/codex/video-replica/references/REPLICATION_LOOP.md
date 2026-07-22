# Replication build and verification loop

## Contents

1. Artifact and role separation
2. Build routing
3. Bounded implementation loop
4. Difference ledger
5. Verification and stop conditions

## 1. Artifact and role separation

Keep these boundaries explicit:

| Plane | Mutable by | Must not change |
|---|---|---|
| Evidence | capture/analyzer pass | source media, decoded timeline and immutable hashes after freeze |
| Specification | analyzer plus recorded Owner decisions | evidence provenance and unresolved unknowns |
| Implementation | builder pass | frozen evidence, Owner decisions and validation thresholds |
| Verification | read-only verifier pass | candidate code, evidence or thresholds during scoring |

The same Codex task may execute multiple planes, but each plane needs a separate log and
fresh inputs. Independent verification means another authorized agent or process when
available. A same-context recheck is only process-separated and must be labelled so.

## 2. Build routing

Select the least complex substrate that meets the measured requirement:

- CSS/WAAPI: simple composited transitions and native timing.
- GSAP: complex timelines, custom easing, ScrollTrigger, SVG paths and orchestration.
- Motion/Framer Motion: React state/gesture-driven transitions.
- Lottie/SVG: authored vector timelines with available vector assets.
- Rive/native state machines: interactive animation with explicit states.
- Canvas/WebGL/shaders: particles, fields, 3D or filter effects that DOM transforms
  cannot reproduce within the performance budget.

Do not force a preferred framework onto the reference. Record capability ceilings,
asset/license constraints, accessibility alternatives and fallbacks.

## 3. Bounded implementation loop

For each iteration:

1. Choose one critical state/transition group from the frozen spec.
2. List its evidence IDs and current residual differences.
3. Define the smallest target files and tests that can close it.
4. Implement using existing project patterns and assets where lawful.
5. Run target functional tests before visual capture.
6. Replay identical inputs in the frozen environment.
7. Align candidate/reference by declared event anchors, not by manually convenient
   frames.
8. Measure the complete fidelity vector for the selected group.
9. Update the difference ledger and stop, fix, or advance based on hard gates.

Default to a maximum of three candidate-fix iterations per selected group unless the
run contract sets a different budget. Stop earlier when two iterations do not reduce
the critical residual, because that usually signals a wrong model, evidence gap or
environment mismatch rather than a need for more parameter nudging.

## 4. Difference ledger

Use one entry per independently actionable mismatch:

```yaml
- id: DIFF-001
  evidence_ids: [frame_00124, motion_nav_open]
  axis: temporal
  severity: critical
  confidence: high
  reference: {onset_ms: 420}
  candidate: {onset_ms: 505}
  uncertainty_ms: 17
  likely_cause: "transition starts after async state commit"
  next_action: "move visual feedback before network-bound state update"
  status: open
```

Prioritize critical functional/state failures, then wrong clock/trigger, timing and
trajectory, layout/color/assets, polish and optional surpass changes. A beautiful
anchor screenshot cannot compensate for a failed interaction or wrong motion clock.

## 5. Verification and stop conditions

Require raw replay commands, environment versions, candidate captures, measurements
and target test output. Verification fails closed when:

- candidate and reference environments cannot be made comparable;
- a critical evidence ID or deterministic input is missing;
- the candidate passes only after thresholds or alignment rules are changed;
- worst critical frames/regions fail despite an acceptable mean;
- functional state, timing or interaction fails even if static visuals pass;
- a claimed physical haptic has no device evidence;
- selected surpass changes regress reference-critical or accessibility gates.

Final pass language must name the passed axes. Reserve `SURPASS_PASS` for a measured
Pareto improvement plus Owner acceptance, not an aesthetic assertion.
