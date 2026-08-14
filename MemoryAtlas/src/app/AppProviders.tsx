import type { PropsWithChildren } from "react";
import { AtlasDataProvider } from "../providers/AtlasDataProvider";
import { AtlasRuntimeProvider } from "../providers/AtlasRuntimeProvider";
import { AtlasWorkspaceProvider } from "../providers/AtlasWorkspaceProvider";
import { LiveSnapshotBoundary, MemoryAtlasThemeProvider, PrivateAnalyticsProvider } from "../features/v31";

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <MemoryAtlasThemeProvider>
      <PrivateAnalyticsProvider>
        <LiveSnapshotBoundary>
          <AtlasDataProvider>
            <AtlasWorkspaceProvider>
              <AtlasRuntimeProvider>{children}</AtlasRuntimeProvider>
            </AtlasWorkspaceProvider>
          </AtlasDataProvider>
        </LiveSnapshotBoundary>
      </PrivateAnalyticsProvider>
    </MemoryAtlasThemeProvider>
  );
}
