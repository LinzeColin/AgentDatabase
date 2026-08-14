import type { PropsWithChildren } from "react";
import { LiveSnapshotProvider } from "./LiveSnapshotProvider";
import { RealityCalibrationPanel } from "./RealityCalibrationPanel";

declare global {
  interface Window {
    __MEMORY_ATLAS_LIVE_SNAPSHOT__?: boolean | string;
  }
}

/**
 * v0.0.0.32 T05 rollback switch.
 *
 * Off means the panel never renders and the provider never mounts, so no
 * request is made and the original ten views behave exactly as before. Two
 * ways to turn it off, in priority order:
 *
 *   1. `window.__MEMORY_ATLAS_LIVE_SNAPSHOT__ = "0"` — set before the bundle
 *      runs. This is the no-rebuild escape hatch for a live release.
 *   2. `VITE_MEMORY_ATLAS_LIVE_SNAPSHOT=0` at build time.
 */
export function liveSnapshotEnabled(): boolean {
  const runtime = typeof window === "undefined" ? undefined : window.__MEMORY_ATLAS_LIVE_SNAPSHOT__;
  if (runtime !== undefined) return String(runtime) !== "0" && String(runtime) !== "false";
  return import.meta.env.VITE_MEMORY_ATLAS_LIVE_SNAPSHOT !== "0";
}

/** Mounts the live snapshot inside the one existing provider stack. */
export function LiveSnapshotBoundary({ children }: PropsWithChildren) {
  if (!liveSnapshotEnabled()) return <>{children}</>;
  return <LiveSnapshotProvider>{children}</LiveSnapshotProvider>;
}

/** Renders the first-screen panel, or nothing at all when the flag is off. */
export function RealityCalibrationSection() {
  if (!liveSnapshotEnabled()) return null;
  return <RealityCalibrationPanel />;
}
