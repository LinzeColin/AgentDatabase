#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");
const checks = [];
const add = (id, pass, evidence) => checks.push({ id, pass: Boolean(pass), evidence });

const app = read("src/App.tsx");
const types = read("src/types.ts");
const constants = read("src/shared/atlas/constants.tsx");
const routes = read("src/app/routeRegistry.tsx");
const shell = read("src/app/MemoryAtlasShell.tsx");
const providers = read("src/app/AppProviders.tsx");
const packageJson = JSON.parse(read("package.json"));
const css = read("src/features/v31/v31Incremental.css");
const privateProvider = read("src/features/v31/PrivateAnalyticsProvider.tsx");
const themeProvider = read("src/features/v31/MemoryAtlasThemeProvider.tsx");
const contracts = read("src/features/v31/contracts.ts");
const failureView = read("src/features/v31/FailureCompoundView.tsx");
const economyView = read("src/features/v31/BehaviorEconomyView.tsx");
const runtimeView = read("src/features/v31/RuntimeView.tsx");

const original = ["home","galaxy","notion","roi","obsidian","timeline","contribution","wordcloud","search","summary"];
const added = ["failureCompound","behaviorEconomy","runtime"];
const hasGroup = (id) => new RegExp(`id\\s*:\\s*["']${id}["']`).test(constants);
const baseJudgment = hasGroup("judgment") ? "judgment" : (hasGroup("judgement") ? "judgement" : null);

add("INC-001-original-root", app.includes("<AppProviders>") && app.includes("<MemoryAtlasShell>") && app.includes("<FeatureRouter />"), "existing root composition");
add("INC-002-no-parallel-root", !/V31App|legacy\s*=|ma31-legacy-boundary|ma31-root/.test(app), "no second shell");
add("INC-003-default-home", /DEFAULT_MEMORY_ATLAS_VIEW\s*:\s*ViewKey\s*=\s*["']home["']/.test(constants), "home");
for (const key of original) {
  add(`INC-004-type-${key}`, new RegExp(`["']${key}["']`).test(types), key);
  add(`INC-005-route-${key}`, new RegExp(`\\b${key}\\s*:`).test(routes), key);
  add(`INC-006-view-${key}`, new RegExp(`key:\\s*["']${key}["']`).test(constants), key);
}
for (const key of added) {
  add(`INC-007-type-${key}`, new RegExp(`["']${key}["']`).test(types), key);
  add(`INC-008-route-${key}`, new RegExp(`\\b${key}\\s*:`).test(routes), key);
  add(`INC-009-view-${key}`, new RegExp(`key:\\s*["']${key}["']`).test(constants), key);
}
const critical = ["InteractionLens","CommandPalettePanel","OwnerDailyEntry","OwnerDailyWorkspace","NodeInspector","ContributionPeriodInspector","ProposalWorkspace","WritebackProposalPanel","MemoryAtlasHelpPanel"];
for (const token of critical) add(`INC-010-shell-${token}`, shell.includes(token), token);
for (const token of ["AtlasDataProvider","AtlasWorkspaceProvider","AtlasRuntimeProvider","MemoryAtlasThemeProvider","PrivateAnalyticsProvider"])
  add(`INC-011-provider-${token}`, providers.includes(token), token);
add("INC-012-five-groups", Boolean(baseJudgment) && ["exploration","reflection","compound","operations"].every(hasGroup), { baseJudgment });
add("INC-013-theme-default-A", /return value === "B" \|\| value === "C" \? value : "A"/.test(themeProvider), "A");
add("INC-014-mode-default-light", /=== "dark" \? "dark" : "light"/.test(themeProvider), "light");
add("INC-015-theme-controls", shell.includes("ThemeControls") && shell.includes("data-memory-atlas-theme") && shell.includes("data-memory-atlas-mode"), "existing shell themed");
for (const theme of ["A", "B", "C"]) {
  add(`INC-016-layout-${theme}`, css.includes(`data-memory-atlas-theme="${theme}"`), theme);
}
add("INC-017-light-mode-existing-shell", css.includes('data-memory-atlas-mode="light"') && css.includes(".sidebar") && css.includes(".interaction-lens") && css.includes(".command-palette"), "light applies to original shell primitives");
add("INC-018-dark-mode", css.includes('data-memory-atlas-mode="dark"'), "dark token mode");
add("INC-019-api-404-degrades", privateProvider.includes("response.status === 404") && privateProvider.includes("return null"), "404 -> unknown");
add("INC-020-provider-never-blocks-children", privateProvider.includes("<Context.Provider value={value}>{children}</Context.Provider>"), "children render in loading/unknown/error states");
add("INC-021-proposal-only", contracts.includes('writeback: "proposal_only"') && contracts.includes("direct_stable_memory_mutation: false"), "writeback boundary");
add("INC-022-validation-scripts", packageJson.scripts?.["validate:v31:incremental"] && packageJson.scripts?.["validate:v31:typescript"] && packageJson.scripts?.["validate:v31:browser"], packageJson.scripts);
add("INC-023-no-fixture-success", !/const\s+(mock|demoData|fixtureData)|state\s*:\s*["']SUCCESS["']/i.test(failureView + economyView + runtimeView), "no fabricated production success");
add("INC-024-no-app-css-root", !css.includes(".ma31-root") && !css.includes(".ma31-legacy-boundary"), "CSS does not create parallel root contract");
add("INC-025-shared-business-runtime", !fs.existsSync(path.join(root, "src/themes/A/App.tsx")) && !fs.existsSync(path.join(root, "src/themes/B/App.tsx")) && !fs.existsSync(path.join(root, "src/themes/C/App.tsx")), "no duplicated apps");

const failed = checks.filter(x => !x.pass);
const report = { schema_version: "memory_atlas.incremental_static_validation.v2", pass: failed.length === 0, check_count: checks.length, failed, checks };
console.log(JSON.stringify(report, null, 2));
if (failed.length) process.exit(1);
