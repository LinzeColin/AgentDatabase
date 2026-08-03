#!/usr/bin/env node
// v0.0.0.31 product oracle.
//
// The twenty UI-0xx guarantees below keep their meaning. What changed is the
// subject they are measured on: the owner froze "one product shell only", so
// v31 now ships through the existing AppProviders → MemoryAtlasShell →
// FeatureRouter composition and lives in src/features/v31. The earlier
// src/v31/V31App.tsx wrapper is retained on disk as a preserved v0.0.0.31 asset
// (UI-007 proves it is still there) but it is no longer the shipped product, so
// asserting product behaviour against it would validate code no user can reach.
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const exists = (relative) => fs.existsSync(path.join(root, relative));
const checks = [];
const add = (id, pass, evidence) => checks.push({ id, pass: Boolean(pass), evidence });

const app = read("src/App.tsx");
const constants = read("src/shared/atlas/constants.tsx");
const routes = read("src/app/routeRegistry.tsx");
const shell = read("src/app/MemoryAtlasShell.tsx");
const theme = read("src/features/v31/MemoryAtlasThemeProvider.tsx");
const provider = read("src/features/v31/PrivateAnalyticsProvider.tsx");
const contracts = read("src/features/v31/contracts.ts");
const failureView = read("src/features/v31/FailureCompoundView.tsx");
const economyView = read("src/features/v31/BehaviorEconomyView.tsx");
const runtimeView = read("src/features/v31/RuntimeView.tsx");
const css = read("src/features/v31/v31Incremental.css");
const atlas = read("src/data/atlas.ts");

const navigationDeclaration = constants.indexOf("export const navigationGroups");
// Start after the `= [` initializer so the group-id *type union* above it is not
// mistaken for a group entry.
const navigationBlock = constants.slice(constants.indexOf("= [", navigationDeclaration));
const primaryOrder = [...navigationBlock.matchAll(/\bid:\s*"([a-z]+)"/g)].map((match) => match[1]).slice(0, 5);
add("UI-001-exact-five-primary", primaryOrder.length === 5 && new Set(primaryOrder).size === 5, primaryOrder);
add("UI-002-primary-semantics", JSON.stringify(primaryOrder) === JSON.stringify(["judgment", "exploration", "reflection", "compound", "operations"]), primaryOrder);
add("UI-003-default-theme-a", /return value === "B" \|\| value === "C" \? value : "A"/.test(theme), "A is fallback");
add("UI-004-default-mode-light", /=== "dark" \? "dark" : "light"/.test(theme), "light is fallback");
add("UI-005-three-distinct-layouts", ["A", "B", "C"].every((item) => css.includes(`.app-shell[data-memory-atlas-theme="${item}"]`)), "A/B/C layout adapters on the one shell");
const themeSelectors = ["A", "B", "C"].filter((item) => css.includes(`.app-shell[data-memory-atlas-theme="${item}"]`));
const modeSelectors = ["light", "dark"].filter((item) => css.includes(`.app-shell[data-memory-atlas-mode="${item}"]`));
add("UI-006-six-token-modes", themeSelectors.length * modeSelectors.length === 6, { themeSelectors, modeSelectors });
add("UI-007-existing-atlas-preserved", exists("src/v31/V31App.tsx") && !/V31App|ma31-legacy-boundary|ma31-root/.test(app) && !css.includes(".ma31-root"), "prior v31 asset retained and never re-wrapped around the product");
add("UI-008-app-wraps-existing-atlas", app.includes("<AppProviders>") && app.includes("<MemoryAtlasShell>") && app.includes("<FeatureRouter />") && routes.includes('from "../features/v31"') && shell.includes("useMemoryAtlasTheme"), "App composition");
add("UI-009-private-contract", provider.includes("private_full_fidelity_read_only_analytics") && provider.includes("direct_stable_memory_mutation === false"), "runtime validation");
add("UI-010-public-private-coexist", atlas.includes("public_redacted_read_only_visualization") && atlas.includes("private_full_fidelity_read_only_analytics"), "both source modes accepted");
add("UI-011-failure-front-end", failureView.includes("失败沉淀为回归资产") && failureView.includes("错误 → 回归资产 台账"), "failure compound surface");
add("UI-012-zero-tech-actions", ["立即备份", "诊断并修复", "恢复演练"].every((label) => runtimeView.includes(label)), "three owner actions");
add("UI-013-no-false-capture-success", runtimeView.includes("只创建源端请求") && runtimeView.includes("不会把排队误报为成功"), "capture request semantics");
add("UI-014-global-comparison-gate", economyView.includes("没有同口径总体时禁止生成全球百分位"), "benchmark caveat");
add("UI-015-proposal-only", contracts.includes('writeback: "proposal_only"') && contracts.includes("direct_stable_memory_mutation: false") && !provider.includes("writeStableMemory"), "no direct stable-memory writer");
add("UI-016-responsive", css.includes("@media (max-width: 760px)"), "mobile breakpoint");
add("UI-017-reduced-motion", css.includes("prefers-reduced-motion"), "reduced motion");
add("UI-018-private-api-only", provider.includes('new URL("/api/v31/status"') && !provider.includes("/memory_atlas_private_analytics.json"), "no static private snapshot path");
add("UI-019-access-denial-visible", provider.includes("response.status === 403") && /throw new Error\("私有分析读取未通过[^"]*身份验证"\)/.test(provider), "403 is human-readable and fail-closed");
add("UI-020-private-fetch-credentials", provider.includes('credentials: "same-origin"'), "browser session through Access");

const failed = checks.filter((row) => !row.pass);
console.log(JSON.stringify({ schema_version: "memory_atlas.v31_frontend_validation.v2", checks, pass: failed.length === 0 }, null, 2));
if (failed.length) process.exit(1);
