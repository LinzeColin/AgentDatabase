#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
let ts;
try { ts = require(path.resolve(__dirname, "../node_modules/typescript")); }
catch { ts = require("typescript"); }
const root = path.resolve(__dirname, "..");
const fixed = [
  "src/types.ts",
  "src/shared/atlas/constants.tsx",
  "src/app/routeRegistry.tsx",
  "src/app/AppProviders.tsx",
  "src/app/MemoryAtlasShell.tsx",
];
const featureRoot = path.join(root, "src/features/v31");
const features = fs.readdirSync(featureRoot)
  .filter(name => /\.(ts|tsx)$/.test(name))
  .map(name => path.join("src/features/v31", name));
const files = [...fixed, ...features];
const failures = [];
for (const relative of files) {
  const file = path.join(root, relative);
  const source = fs.readFileSync(file, "utf8");
  const result = ts.transpileModule(source, {
    fileName: file,
    reportDiagnostics: true,
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ESNext,
      jsx: ts.JsxEmit.ReactJSX,
      isolatedModules: true,
    },
  });
  for (const diagnostic of result.diagnostics || []) {
    if (diagnostic.category !== ts.DiagnosticCategory.Error) continue;
    const position = diagnostic.file && diagnostic.start != null
      ? diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start)
      : null;
    failures.push({
      file: relative,
      line: position ? position.line + 1 : null,
      column: position ? position.character + 1 : null,
      code: diagnostic.code,
      message: ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n"),
    });
  }
}
const report = {
  schema_version: "memory_atlas.incremental_typescript_syntax.v1",
  pass: failures.length === 0,
  checked_files: files.length,
  failures,
};
console.log(JSON.stringify(report, null, 2));
if (failures.length) process.exit(1);
