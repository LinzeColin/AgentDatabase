#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const checks = [];
const add = (id, pass, evidence) => checks.push({ id, pass: Boolean(pass), evidence });

const app = read("src/App.tsx");
const nav = read("src/v31/PrimaryNavigation.tsx");
const theme = read("src/v31/ThemeContext.tsx");
const shell = read("src/v31/V31App.tsx");
const provider = read("src/v31/PrivateAnalyticsProvider.tsx");
const views = read("src/v31/V31Views.tsx");
const css = read("src/v31/v31.css");
const atlas = read("src/data/atlas.ts");

const primaryOrder = nav.match(/const order: V31PrimaryView\[\] = \[([^\]]+)\]/s)?.[1]
  ?.split(",").map((value) => value.replace(/[\s"]/g, "")).filter(Boolean) ?? [];
add("UI-001-exact-five-primary", primaryOrder.length === 5 && new Set(primaryOrder).size === 5, primaryOrder);
add("UI-002-primary-semantics", JSON.stringify(primaryOrder) === JSON.stringify(["today","universe","compound","economy","runtime"]), primaryOrder);
add("UI-003-default-theme-a", /return value === "B" \|\| value === "C" \? value : "A"/.test(theme), "A is fallback");
add("UI-004-default-mode-light", /=== "dark" \? "dark" : "light"/.test(theme), "light is fallback");
add("UI-005-three-distinct-layouts", ["data-layout-adapter=\"A\"","data-layout-adapter=\"B\"","data-layout-adapter=\"C\""].every((token) => shell.includes(token)), "A/B/C layout adapters");
add("UI-006-six-token-modes", ["theme-a[data-color-mode=\"light\"]","theme-a[data-color-mode=\"dark\"]","theme-b[data-color-mode=\"light\"]","theme-b[data-color-mode=\"dark\"]","theme-c[data-color-mode=\"light\"]","theme-c[data-color-mode=\"dark\"]"].every((token) => css.includes(token)), "3 themes × 2 modes");
add("UI-007-existing-atlas-preserved", shell.includes("MemoryAtlasShell") === false && shell.includes("data-existing-memory-atlas-preserved"), "legacy passed as ReactNode and preserved");
add("UI-008-app-wraps-existing-atlas", app.includes("V31App") && app.includes("MemoryAtlasShell") && app.includes("FeatureRouter"), "App composition");
add("UI-009-private-contract", provider.includes("private_full_fidelity_read_only_analytics") && provider.includes("direct_stable_memory_mutation === false"), "runtime validation");
add("UI-010-public-private-coexist", atlas.includes("public_redacted_read_only_visualization") && atlas.includes("private_full_fidelity_read_only_analytics"), "both source modes accepted");
add("UI-011-failure-front-end", views.includes("Failure-to-Regression Compound Engine") && views.includes("Incident → Regression Asset"), "failure compound surface");
add("UI-012-zero-tech-actions", ["立即备份","诊断并修复","恢复演练"].every((label) => views.includes(label)), "three owner actions");
add("UI-013-no-false-capture-success", views.includes("只创建源端请求") && views.includes("不会把排队误报为成功"), "capture request semantics");
add("UI-014-global-comparison-gate", views.includes("没有同口径总体时禁止生成全球百分位"), "benchmark caveat");
add("UI-015-proposal-only", provider.includes("direct_stable_memory_mutation") && !provider.includes("writeStableMemory"), "no direct stable-memory writer");
add("UI-016-responsive", css.includes("@media (max-width: 760px)"), "mobile breakpoint");
add("UI-017-reduced-motion", css.includes("prefers-reduced-motion"), "reduced motion");
add("UI-018-private-api-only", provider.includes('new URL("/api/v31/status"') && !provider.includes('/data/') && !provider.includes('/memory_atlas_private_analytics.json'), "no static private snapshot path");
add("UI-019-access-denial-visible", provider.includes("Cloudflare Access 身份验证"), "403 is human-readable and fail-closed");
add("UI-020-private-fetch-credentials", provider.includes('credentials: "same-origin"'), "browser session through Access");

const failed = checks.filter((row) => !row.pass);
console.log(JSON.stringify({ schema_version: "memory_atlas.v31_frontend_validation.v1", checks, pass: failed.length === 0 }, null, 2));
if (failed.length) process.exit(1);
