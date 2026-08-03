#!/usr/bin/env node
// v0.0.0.32 T05 rollback proof: with the feature flag off the panel is gone,
// no live-snapshot request is made at all, and the original ten views still
// render. Mode "runtime" sets the global before the bundle runs (no rebuild);
// mode "build" expects a bundle already built with the flag off.
//
// usage: verify_live_snapshot_rollback_v32.mjs <url> <output.json> <runtime|build>
import fs from "node:fs/promises";
import process from "node:process";
import { chromium } from "playwright";

const [url, output, mode = "runtime"] = process.argv.slice(2);
if (!url || !output) {
  console.error("usage: verify_live_snapshot_rollback_v32.mjs <url> <output.json> <runtime|build>");
  process.exit(2);
}

const TEN = ["home", "galaxy", "notion", "roi", "obsidian", "timeline", "contribution", "wordcloud", "search", "summary"];
const checks = [];
const record = (id, pass, evidence) => checks.push({ id, pass: Boolean(pass), evidence });

const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  if (mode === "runtime") {
    await context.addInitScript(() => { window.__MEMORY_ATLAS_LIVE_SNAPSHOT__ = "0"; });
  }
  const page = await context.newPage();
  const apiRequests = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname === "/api/v31/live-snapshot") apiRequests.push(request.url());
  });
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text().slice(0, 300)); });

  await page.goto(url, { waitUntil: "networkidle" });
  await page.locator(".app-shell").waitFor({ state: "visible" });
  record("panel_is_absent", (await page.locator(".ma-reality-panel").count()) === 0, { count: await page.locator(".ma-reality-panel").count() });
  record("no_live_snapshot_request", apiRequests.length === 0, { requests: apiRequests.length });
  record("default_entry_is_home", await page.locator('[data-view="home"]').isVisible(), {});

  for (const key of TEN) {
    await page.locator(`[data-nav-view="${key}"]`).click();
    await page.locator(`[data-view="${key}"]`).waitFor({ state: "visible", timeout: 20_000 });
    record(`view_${key}_still_renders`, await page.locator(`[data-view="${key}"]`).isVisible(), {});
  }
  record("no_console_errors", consoleErrors.length === 0, { errors: consoleErrors.slice(0, 5) });
  await context.close();
} finally {
  await browser.close();
}

const report = {
  schema_version: "memory_atlas.live_snapshot_rollback.v1",
  captured_at: new Date().toISOString(),
  page_url: url,
  mode,
  verdict: checks.every((row) => row.pass) ? "PASS" : "FAIL",
  failure_count: checks.filter((row) => !row.pass).length,
  checks,
};
await fs.writeFile(output, JSON.stringify(report, null, 2) + "\n", { encoding: "utf8", mode: 0o600 });
console.log(`${report.verdict} — ${checks.length - report.failure_count}/${checks.length} (${mode})`);
process.exit(report.verdict === "PASS" ? 0 : 1);
