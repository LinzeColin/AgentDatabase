#!/usr/bin/env node
import fs from "node:fs/promises";
import process from "node:process";
import { chromium } from "playwright";

const [url, storageState, output] = process.argv.slice(2);
if (!url || !storageState || !output) {
  console.error("usage: capture_browser_receipt.mjs <url> <storage-state.json> <output.json>");
  process.exit(2);
}
const browser = await chromium.launch({ headless: true });
try {
  const consoleErrors = [];
  const networkErrors = [];
  const context = await browser.newContext({ storageState });
  const page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text().slice(0, 500)); });
  page.on("requestfailed", (request) => networkErrors.push(`${request.method()} ${new URL(request.url()).pathname}: ${request.failure()?.errorText ?? "failed"}`));
  await page.goto(url, { waitUntil: "networkidle" });
  const panel = page.locator(".ma-reality-panel[data-run-id]");
  await panel.waitFor({ state: "visible" });
  const panelIdentity = await panel.evaluate((node) => ({
    run_id: node.getAttribute("data-run-id"),
    trace_id: node.getAttribute("data-trace-id"),
    release_id: node.getAttribute("data-release-id"),
    deployment_revision: node.getAttribute("data-deployment-revision"),
  }));
  const oracleRows = await page.locator("[data-oracle]").evaluateAll((nodes) => Object.fromEntries(nodes.map((node) => {
    const raw = node.getAttribute("data-oracle-value");
    const numeric = raw !== null && raw !== "null" && raw.trim() !== "" && Number.isFinite(Number(raw));
    return [node.getAttribute("data-oracle"), numeric ? Number(raw) : raw];
  })));
  const response = await page.request.get(new URL("/api/v31/live-snapshot", url).toString(), { headers: { Accept: "application/json" } });
  if (response.status() !== 200) throw new Error(`live snapshot API returned HTTP ${response.status()}`);
  const cacheControl = response.headers()["cache-control"] ?? "";
  if (!cacheControl.toLowerCase().includes("no-store")) throw new Error("live snapshot API is missing no-store");
  const api = await response.json();
  const headers = response.headers();
  const apiIdentity = {
    run_id: headers["x-memory-atlas-run-id"] ?? null,
    trace_id: headers["x-memory-atlas-trace-id"] ?? null,
    release_id: headers["x-memory-atlas-release-id"] ?? null,
    deployment_revision: headers["x-memory-atlas-deployment-revision"] ?? null,
  };
  const bodyIdentity = {
    run_id: api.run?.run_id ?? null,
    trace_id: api.run?.trace_id ?? null,
    release_id: api.release?.release_id ?? "UNVERIFIED",
    deployment_revision: api.release?.deployment_revision ?? "UNVERIFIED",
  };
  for (const key of Object.keys(bodyIdentity)) {
    if (apiIdentity[key] !== bodyIdentity[key] || panelIdentity[key] !== bodyIdentity[key]) throw new Error(`identity mismatch: ${key}`);
  }
  const values = {
    ...oracleRows,
    top_action_recommendation_id: api.decision?.top_action?.recommendation_id ?? null,
    freshness_state: api.freshness?.state ?? null,
    benchmark_state: oracleRows.benchmark_state ?? null,
    source_completed_at: api.run?.source_completed_at ?? null,
    deployment_revision: api.release?.deployment_revision ?? null,
  };
  const receipt = {
    schema_version: "memory_atlas.browser_receipt.v1",
    captured_at: new Date().toISOString(),
    page_url: url,
    ...bodyIdentity,
    panel_identity: panelIdentity,
    api_status: response.status(),
    api_cache_control: cacheControl,
    api_identity: apiIdentity,
    values,
    console_error_count: consoleErrors.length,
    network_error_count: networkErrors.length,
    console_error_summaries: consoleErrors.slice(0, 20),
    network_error_summaries: networkErrors.slice(0, 20),
  };
  await fs.writeFile(output, JSON.stringify(receipt, null, 2) + "\n", { encoding: "utf8", mode: 0o600 });
} finally {
  await browser.close();
}
