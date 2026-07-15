import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath, URL } from "node:url";

const appDir = fileURLToPath(new URL(".", import.meta.url));
const atlasDataDir = fileURLToPath(new URL("../../data/derived/visualization", import.meta.url));
const forbiddenRawDirs = [
  fileURLToPath(new URL("../../data/public_raw", import.meta.url)),
  fileURLToPath(new URL("../../data/raw_archives", import.meta.url)),
].map((value) => path.resolve(value));

function filesystemPath(id: string): string | null {
  const clean = id.split(/[?#]/, 1)[0];
  if (!clean || clean.startsWith("\0")) return null;
  if (clean.startsWith("file://")) return path.resolve(fileURLToPath(clean));
  if (clean.startsWith("/@fs/")) return path.resolve("/", clean.slice(5));
  return path.isAbsolute(clean) ? path.resolve(clean) : null;
}

export function assertRawIsolationPath(id: string): void {
  const candidate = filesystemPath(id);
  if (!candidate) return;
  for (const rawDir of forbiddenRawDirs) {
    if (candidate === rawDir || candidate.startsWith(`${rawDir}${path.sep}`)) {
      throw new Error("Memory Atlas frontend cannot load raw source roots.");
    }
  }
}

type RawIsolationPlugin = Plugin & {
  api: { assertPath: typeof assertRawIsolationPath };
};

function rawIsolationPlugin(): RawIsolationPlugin {
  return {
    name: "memory-atlas-raw-isolation",
    enforce: "pre",
    api: { assertPath: assertRawIsolationPath },
    resolveId(source, importer) {
      assertRawIsolationPath(source);
      if (importer && source.startsWith(".")) {
        const importerPath = filesystemPath(importer);
        if (importerPath) assertRawIsolationPath(path.resolve(path.dirname(importerPath), source));
      }
      return null;
    },
    load(id) {
      assertRawIsolationPath(id);
      return null;
    },
    transform(_code, id) {
      assertRawIsolationPath(id);
      return null;
    },
  };
}

export default defineConfig({
  plugins: [rawIsolationPlugin(), react()],
  publicDir: atlasDataDir,
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    fs: {
      strict: true,
      allow: [appDir, atlasDataDir],
    },
  },
  build: {
    sourcemap: process.env.VITE_SOURCEMAP === "1",
  },
});
