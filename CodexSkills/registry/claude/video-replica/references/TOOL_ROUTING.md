# Tool routing and prior art

Snapshot date: 2026-07-17. Re-check versions, licenses and project status before
installing or copying code. Do not auto-install optional tools.

## Directly similar systems

| Project | Useful pattern | Reuse decision |
|---|---|---|
| [motiscope](https://github.com/KumarSashank/motiscope) | dense motion-energy timing, curated frames, easing/beat/loop analysis, target adapters for GSAP/CSS/Framer/Lottie | Closest reference and MIT-licensed; use as an optional pinned analyzer or study its tested patterns. Still verify per-element claims independently because aggregate motion can mislead. |
| [video-to-ui](https://github.com/mmohajer9/video-to-ui) | multi-frame UI/design synthesis and bounded frame-analysis workflow | Useful product-flow reference; do not rely on sparse frame sampling as exhaustive evidence. |
| [mirrorframe](https://github.com/byte271/mirrorframe) | live-page computed-style/WAAPI capture, interaction state machines, per-node verification and explicit skip reasons | High-ROI route when a controllable URL exists; project is new, so validate against local fixtures before adoption. |
| [motion-replica](https://github.com/corazzione/motion-replica) | Playwright/CDP telemetry aligned with frames, sandbox render and iterative SSIM/pixel diff | Architecture reference only. Repository had no declared license in this snapshot; do not copy code. |
| [Interaction2Code](https://github.com/WebPAI/Interaction2Code) | benchmark/failure taxonomy for interactive webpage generation | Use its finding that subtle and complex interactions need explicit highlighting, textual descriptions and human/functional evaluation. |

Do not treat popularity, README claims or one demo as proof of fidelity. Check code,
tests, fixtures, license, commit history and reproduced output.

## Core route

### Required local-video substrate

- [FFmpeg / ffprobe](https://ffmpeg.org/): decoding, stream/color metadata,
  presentation timestamps, native-rate frame export, audio extraction and signal
  filters. Preserve commands and versions in evidence.
- Python 3 standard library: manifests, hashes, timelines, review batches and gates.

### Optional video analysis

- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect): content/adaptive
  scene boundaries. Use for navigation, not coverage proof.
- [CoTracker](https://github.com/facebookresearch/co-tracker): point tracking for
  element trajectories when compute/model dependencies are justified.
- [SAM 2](https://github.com/facebookresearch/sam2): promptable video segmentation
  and object-mask propagation, useful for occlusion-aware regions.
- [LPIPS](https://github.com/richzhang/PerceptualSimilarity): learned image-patch
  distance. Use on aligned frames/regions and pin model/version.
- [VMAF](https://github.com/Netflix/vmaf): full-reference video quality/compression
  assessment. It is not an interaction or motion-spec correctness metric.

Only add heavy ML dependencies when the element cannot be measured reliably with
runtime telemetry, region tracking or simpler deterministic tools.

### Instrumented web route

- [Playwright](https://playwright.dev/): deterministic browser input, screenshots,
  traces and repeatable viewport/runtime control.
- Chrome DevTools Protocol and Web Animations API: computed/runtime facts, animation
  timings/keyframes, performance and input alignment.
- [rrweb](https://github.com/rrweb-io/rrweb): DOM snapshots, mutations and user-event
  streams for authorized record/replay.
- [OpenReplay](https://github.com/openreplay/openreplay): broader session replay plus
  network, console, errors, state and performance context when its deployment/privacy
  cost is justified.

For a live page, prefer structured telemetry plus rendered capture. Video alone throws
away the causal information required for faithful interaction reconstruction.

## Reconstruction targets

Choose only after the spec is confirmed:

- CSS/WAAPI for simple composited transitions and deterministic browser-native timing.
- GSAP for complex timelines, custom easing, scroll orchestration and SVG paths.
- Motion/Framer Motion for React state-driven motion and gesture integration.
- Lottie/SVG for authored vector timelines when source/vector assets exist.
- Rive or a native engine for interactive state-machine animation when appropriate.
- Canvas/WebGL/shaders for particle/field/3D effects that cannot be represented
  faithfully in DOM transforms.

Do not force every reference into one framework. Record the capability ceiling,
performance budget, accessibility alternative and fallback.
