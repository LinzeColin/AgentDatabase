import { AppProviders } from "./app/AppProviders";
import { FeatureRouter } from "./app/FeatureRouter";
import { MemoryAtlasShell } from "./app/MemoryAtlasShell";
import { V31App } from "./v31";

export function App() {
  const existingMemoryAtlas = (
    <MemoryAtlasShell>
      <FeatureRouter />
    </MemoryAtlasShell>
  );
  return (
    <AppProviders>
      <V31App legacy={existingMemoryAtlas} />
    </AppProviders>
  );
}
