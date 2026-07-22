---
name: video-replica
description: Evidence-backed video experience replication from local videos, screen recordings, prototype walkthroughs, live URLs, or runnable source, ending by default with one validated ZIP deliverable in the user's Downloads directory. Use when the user says “视频复刻skill”, “视频复刻 Skill”, invokes $video-replica, or asks Codex to reproduce or surpass a reference video's visual design, per-frame motion, interaction feel, audio synchronization, responsive behavior, or multimodal feedback with an implementation and independently reviewable validation loop.
---

# 视频复刻 Skill

Turn a reference experience into measured evidence, an implementable specification,
a bounded target implementation, and an independently reviewable fidelity report.
Do not confuse generated code, a plausible screenshot, or a high average score with a
successful replica.

## Operating contract

- Default to Chinese reports; preserve commands, code identifiers and raw errors.
- If the user supplies only a reference, produce an evidence/spec pack and stop at a
  ready-to-build handoff. If the user also supplies a target repository or runnable
  artifact, continue through implementation and replay validation.
- Keep four artifacts separate: `EVIDENCE`, `SPEC`, `IMPLEMENTATION`, `VERIFICATION`.
  The implementation pass may not silently edit the reference evidence or thresholds.
- Never claim “human identical”, “pixel perfect” or “surpassed” from compressed video
  alone. State exactly which fidelity axes passed and which remain unknown.
- Treat physical haptics as `UNOBSERVABLE` unless device telemetry or an on-device test
  is supplied. Pixels and audio are not proof of vibration strength or waveform.
- Separate `REFERENCE_FIDELITY` from `PRODUCT_SURPASS`. First pass the approved
  reference-critical gates; then test preselected improvements without regression.
- Keep original media local. Do not upload it or send it to an external service without
  explicit authorization.
- Finish by default with one validated ZIP of the declared replica output pack in
  `$HOME/Downloads`. Do not archive the whole target repository or silently add the
  original reference media.
- Before target-code edits, state a compact run contract: goal, minimum scope,
  non-goals, inspected/modified files, validation, risks/rollback and stop condition.

Use these labels for every material claim:

| Label | Meaning |
|---|---|
| `[O]` | directly observed in a decoded frame, audio sample, event or runtime trace |
| `[M]` | measured by a named method, with units and provenance |
| `[I:high/medium/low]` | inference with confidence and competing explanations |
| `[D]` | Owner/product decision, never silently selected by the Skill |
| `[U]` | unobservable or unrecoverable from supplied evidence |

Read `references/EVIDENCE_MODEL.md` before fidelity claims. Read
`references/TOOL_ROUTING.md` before selecting analyzers or implementation substrates.
Read `references/METRICS_AND_ACCEPTANCE.md` before defining gates. Read
`references/REPLICATION_LOOP.md` before target-code implementation.

## Select the strongest evidence route

Do not reduce a rich source to video-only evidence:

1. `SOURCE_INSTRUMENTED`: source/project plus runnable target. Capture rendered video
   and DOM/native hierarchy, computed styles, animation objects, events, state changes,
   assets, fonts, network and performance timestamps.
2. `URL_INSTRUMENTED`: controllable URL. Use deterministic browser replay, CDP/WAAPI
   facts and authorized rrweb-style event capture alongside the recording.
3. `VIDEO_ONLY`: preserve decoded pixels, PTS, audio, color metadata, visible pointer or
   touch evidence and uncertainty about hidden state.
4. `OFFLINE_CONCEPT`: describe visual/audio behavior while declaring production and
   interaction ceilings; do not invent a universal browser-fidelity percentage.

## Execute R0-R11

### R0 — Resolve intent, source and target

Record:

- reference path/URL/hash and privacy boundary;
- target repository/runtime, platform, viewport/device and expected output;
- requested mode: `SPEC_ONLY`, `REPLICA_BUILD`, or `REPLICA_THEN_SURPASS`;
- fidelity-critical states/transitions and any explicitly allowed adaptation.

Prefer a proposed default and one bounded Owner choice over a long free-text interview.
Unknown presentation facts remain `unknown`; do not assume 60 Hz, SDR, 1× playback,
desktop pointer, font availability or stable network data.

### R1 — Check executable capability

Resolve the directory containing this file as `SKILL_DIR`, then run:

```bash
python3 "$SKILL_DIR/scripts/video_evidence.py" doctor
```

If required binaries or FFmpeg capabilities are absent, report `ACTION: ESCALATE` with
the exact missing items. Do not install system packages automatically. Analysis based
only on manually supplied frames must be labelled partial and may not be called
exhaustive.

### R2 — Probe before sampling

For a local video:

```bash
python3 "$SKILL_DIR/scripts/video_evidence.py" probe \
  "/absolute/reference.mp4" "/absolute/evidence/probe"
```

Preserve source SHA-256, stream/container data, rotation and aspect ratio, nominal and
average rates, every decoded frame PTS, possible VFR, dimensions, pixel format,
color/HDR signals and audio streams. If HDR/PQ/HLG is detected without a declared
viewing pipeline, set `BLOCKED_COLOR_PIPELINE`; extracted PNGs do not prove display
equivalence.

### R3 — Extract coverage honestly

Choose one mode:

- `exhaustive`: every decoded frame at native dimensions with index-to-PTS mapping;
  required for short clips, critical micro-interactions or explicit “逐帧” requests.
- `balanced`: uniform overview, scene-change navigation, full-native-rate critical
  windows, audio and whole-frame motion signal; use for initial triage.
- `focused`: a known frame or native-rate time window.

```bash
python3 "$SKILL_DIR/scripts/video_evidence.py" extract \
  "/absolute/reference.mp4" "/absolute/evidence/run-001" --mode exhaustive

python3 "$SKILL_DIR/scripts/video_evidence.py" extract \
  "/absolute/reference.mp4" "/absolute/evidence/run-001" \
  --mode balanced --uniform 16 --window 1.20:2.10
```

Never describe `balanced` as whole-video frame coverage. For long videos, discover with
`balanced`, then exhaustively review lossless critical windows.

### R4 — Close the evidence ledger

Inspect the probe summary, capture context, PTS timeline, audio, motion signal, contact
sheets and all review batches. In exhaustive mode:

- review every unique decoded frame at full resolution in bounded batches;
- exact hash duplicates may share a reviewed representative only after verification;
- near-duplicates remain separate because they may encode motion or easing;
- mark each row `reviewed` or `duplicate_verified` in `FRAME_REVIEW_LEDGER.csv`;
- leave unreadable or ambiguous frames unresolved and stop on a critical gap.

```bash
python3 "$SKILL_DIR/scripts/video_evidence.py" validate \
  "/absolute/evidence/run-001" --require-reviewed
```

Do not proceed when decoded count, extracted count, PTS mapping, hashes or review
coverage disagree.

### R5 — Reconstruct states and behavior

Use `templates/DESIGN_SPEC_TEMPLATE.md` to create:

- `scene_graph` and state transitions;
- design tokens with sampling provenance and uncertainty;
- `motion_registry`: target, clock, trigger, delay, duration, trajectory, properties,
  easing/spring, overshoot, settle, interruption and loop;
- `interaction_registry`: pre-state → input → immediate feedback → transition →
  post-state, including cancellation/error variants when evidenced;
- `audio_registry` and sensory limitations;
- target substrate, performance/accessibility ceiling and fallback.

Whole-frame motion is navigation evidence, never a per-element easing fact. Critical
per-element values require runtime telemetry or two independent tracking estimates.
Treat scroll-driven motion as a function of scroll position, not recorder seconds.

### R6 — Resolve only build-changing decisions

Ask the Owner to confirm, preferably as numbered defaults:

1. the plain-language observation checklist;
2. reference-role to target-role mapping;
3. high-impact ambiguous inferences;
4. fidelity-critical axes and allowed adaptations;
5. any separate “surpass” axis and no-regression gates.

Keep status `BLOCKED_OWNER_REVIEW` until these decisions are recorded. If no target
repository/runtime exists, package `SPEC_ONLY` and report `ACTION: ACT` with the single
highest-ROI next input.

### R7 — Freeze deterministic replay and thresholds

Before implementation, define runtime/browser/device versions, viewport/DPR, fonts,
assets, data/network stubs, clock, ordered inputs, capture points and alignment rules.
Capture the same source/runtime at least twice to estimate the noise floor. Use a
vector of gates rather than one score: coverage, static visual, temporal, motion,
interaction, responsiveness, runtime, audio, accessibility and blinded human review.

Thresholds must be frozen before candidate results are viewed. Do not relax a gate to
obtain a pass.

### R8 — Implement one bounded replica loop

Only an `OWNER_CONFIRMED` spec may enter the build. Follow
`references/REPLICATION_LOOP.md`:

1. map evidence IDs to target components and states;
2. choose the simplest substrate that can faithfully express the behavior;
3. implement one bounded critical state/transition group;
4. run functional checks and deterministic replay;
5. capture the candidate with the same declared presentation context;
6. write raw measurements and residual differences without changing reference data;
7. fix the highest-severity, highest-confidence mismatch first.

Do not widen into unrelated redesign, production deployment or publishing. Preserve
existing user changes and use the target repository's own tests and conventions.

### R9 — Verify without self-certification

Verification must be a separate read-only pass over immutable evidence, frozen gates
and candidate captures. If `$verifier` is available, use it for final review. Otherwise
perform a fresh verification pass and state that it is process-separated rather than
agent-independent.

A critical transition passes only when its functional state and declared visual,
timing, motion and multimodal gates all pass. Report mean and worst-frame/region values.
Unexplained critical differences keep status `REPLICA_PARTIAL` or `BLOCKED`.

### R10 — Test “surpass” separately

Start only after all reference-critical gates pass. A valid improvement must:

1. target an axis selected before implementation;
2. exceed a declared meaningful-change threshold;
3. preserve every no-regression fidelity/function/accessibility gate;
4. pass Owner preference/acceptance separately from automated metrics.

Extra particles, stronger easing, blur or longer motion are not improvements by
default.

### R11 — Create the final Downloads ZIP

After the pack reaches any truthful terminal status, package that declared output pack
as the final execution step unless the Owner explicitly requests no archive. A ZIP may
contain `BLOCKED` or `REPLICA_PARTIAL` status; its existence is not a fidelity pass.

Package only `<project>_video_replica_pack_v<N>/`. Do not point the script at the target
repository, home directory or Downloads root. Do not copy the original reference media
into the pack unless the Owner explicitly selected it as a deliverable.

Run:

```bash
python3 "$SKILL_DIR/scripts/package_replica.py" \
  "/absolute/<project>_video_replica_pack_v<N>"
```

The default destination is `$HOME/Downloads`. The script must:

- require a root `MANIFEST.txt`;
- reject symlinks and likely credential/private-key files;
- exclude `.DS_Store`, `__MACOSX`, `.git` and Python caches;
- add `PACKAGE_MANIFEST.sha256` inside the ZIP;
- never overwrite an existing archive;
- create through a temporary file, run ZIP integrity/member/hash checks and atomically
  publish without replacing an existing path;
- print the absolute archive path, SHA-256 and entry count.

Use `--allow-sensitive` only after explicit Owner authorization naming the sensitive
files. Use `--downloads` only for controlled tests or an explicit alternate-destination
decision. If Downloads is absent/unwritable or packaging fails, report
`ACTION: ESCALATE`; do not claim final delivery.

## Minimum output pack

```text
<project>_video_replica_pack_v<N>/
├── MANIFEST.txt
├── DESIGN_SPEC.md
├── capture_context.yaml
├── design_tokens.yaml
├── motion_registry.yaml
├── interaction_registry.yaml
├── audio_registry.yaml
├── validation_contract.yaml
├── DIFFERENCE_LEDGER.yaml
├── IMPLEMENTATION_LOG.md
├── VERIFICATION_REPORT.md
├── evidence/
│   ├── probe_summary.json
│   ├── frame_timeline.csv
│   ├── FRAME_REVIEW_LEDGER.csv
│   ├── EVIDENCE_MANIFEST.sha256
│   ├── frames/
│   ├── windows/
│   ├── audio/
│   └── motion/
└── ANALYZER_LOG.md
```

R11 adds `PACKAGE_MANIFEST.sha256` inside the archive without mutating the source pack.

Valid terminal statuses are `SPEC_READY`, `BLOCKED_OWNER_REVIEW`,
`BLOCKED_EVIDENCE_GAP`, `REPLICA_PARTIAL`, `REFERENCE_FIDELITY_PASS`, and
`SURPASS_PASS`. Never translate partial progress into a pass.

## Report

Begin every report with exactly one of:

- `ACTION: NONE` — requested bounded outcome is complete with evidence.
- `ACTION: ACT` — one bounded review or next run is ready.
- `ACTION: STOP` — a fail-closed gate intentionally prevents downstream work.
- `ACTION: ESCALATE` — dependency, evidence, permission or decision is missing.

Then report route, mode, decoded/extracted/reviewed counts, implementation scope,
per-axis gate status, unresolved evidence, changed artifacts, final ZIP absolute path
and SHA-256, progress percentage, remaining iterations/time/confidence and the single
highest-ROI next action.
