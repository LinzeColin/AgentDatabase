#!/usr/bin/env node
// v0.0.0.32 T06 — degraded-path browser receipts (MA-LIVE-AC-008/009).
//
// usage: capture_degraded_receipts_v32.mjs <url> <scenario-dir> <current.json> <output.json>
//
// Each scenario is installed as the origin's published snapshot, the page is
// reloaded, and what the reader actually sees is recorded. The last two steps
// additionally break the served snapshot to prove the browser keeps last-good
// rather than blanking, then restore it to prove recovery.
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { chromium } from "playwright";

const [url, scenarioDir, currentPath, output] = process.argv.slice(2);
if (!url || !scenarioDir || !currentPath || !output) {
  console.error("usage: capture_degraded_receipts_v32.mjs <url> <scenario-dir> <current.json> <output.json>");
  process.exit(2);
}

const index = JSON.parse(await fs.readFile(path.join(scenarioDir, "index.json"), "utf8"));
const receipts = [];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const panel = page.locator(".ma-reality-panel[data-run-id]");

  const read = async () => ({
    run_id: await panel.getAttribute("data-run-id"),
    warning: (await page.locator(".ma-warning").innerText().catch(() => "")).trim(),
    tier_a: (await page.locator(".ma-truth-ribbon span", { hasText: "Tier A" }).innerText().catch(() => "")).trim(),
    tier_b: (await page.locator(".ma-truth-ribbon span", { hasText: "Tier B" }).innerText().catch(() => "")).trim(),
    event_count: await page.locator("[data-oracle='event_count']").getAttribute("data-oracle-value"),
    answers: await page.locator(".ma-answer h3").allInnerTexts(),
  });

  for (const scenario of index.scenarios) {
    await fs.copyFile(path.join(scenarioDir, scenario.file), currentPath);
    await page.goto(url, { waitUntil: "networkidle" });
    await panel.waitFor({ state: "visible" });
    const seen = await read();
    const api = await page.request.get(new URL("/api/v31/live-snapshot", url).toString());
    const body = await api.json();
    receipts.push({
      scenario: scenario.scenario,
      expected_product_state: scenario.expected_product_state,
      actual_product_state: body.coverage?.product_state ?? null,
      expected_freshness_state: scenario.expected_freshness_state,
      actual_freshness_state: body.freshness?.state ?? null,
      reason_zh: body.freshness?.reason_zh ?? null,
      degraded_banner_shown: seen.warning.length > 0,
      four_answers_still_rendered: seen.answers.length === 4,
      seen,
      pass:
        body.coverage?.product_state === scenario.expected_product_state &&
        body.freshness?.state === scenario.expected_freshness_state &&
        seen.answers.length === 4 &&
        (scenario.expected_product_state === "PASS") === (seen.warning.length === 0),
    });
  }

  // Authority read-back failure: the served snapshot stops validating, so the
  // API answers 503. The reader must keep the last good numbers and be told,
  // never see an empty page or a fabricated zero.
  const healthy = JSON.parse(await fs.readFile(path.join(scenarioDir, "01-healthy.json"), "utf8"));
  await fs.writeFile(currentPath, JSON.stringify(healthy) + "\n", "utf8");
  await page.goto(url, { waitUntil: "networkidle" });
  await panel.waitFor({ state: "visible" });
  const beforeBreak = await read();

  const broken = JSON.parse(JSON.stringify(healthy));
  broken.truth.same_run_evidence.r2_readback.state = "FAIL";
  await fs.writeFile(currentPath, JSON.stringify(broken) + "\n", "utf8");
  const status = (await page.request.get(new URL("/api/v31/live-snapshot", url).toString())).status();
  await page.locator(".ma-refresh").click();
  await sleep(2000);
  const afterBreak = await read();
  receipts.push({
    scenario: "07-authority-readback-failure-keeps-last-good",
    api_status: status,
    pass:
      status === 503 &&
      afterBreak.run_id === beforeBreak.run_id &&
      afterBreak.event_count === beforeBreak.event_count &&
      afterBreak.answers.length === 4 &&
      afterBreak.warning.length > 0,
    seen: afterBreak,
    last_good: beforeBreak,
  });

  await fs.writeFile(currentPath, JSON.stringify(healthy) + "\n", "utf8");
  await page.locator(".ma-refresh").click();
  await sleep(2000);
  const recovered = await read();
  receipts.push({
    scenario: "08-recovers-after-the-authority-returns",
    pass: recovered.run_id === beforeBreak.run_id && recovered.warning.length === 0 && recovered.answers.length === 4,
    seen: recovered,
  });
  await context.close();
} finally {
  await browser.close();
}

const report = {
  schema_version: "memory_atlas.degraded_path_receipt.v1",
  captured_at: new Date().toISOString(),
  page_url: url,
  verdict: receipts.every((row) => row.pass) ? "PASS" : "FAIL",
  failure_count: receipts.filter((row) => !row.pass).length,
  receipts,
};
await fs.writeFile(output, JSON.stringify(report, null, 2) + "\n", { encoding: "utf8", mode: 0o600 });
console.log(`${report.verdict} — ${receipts.length - report.failure_count}/${receipts.length}`);
process.exit(report.verdict === "PASS" ? 0 : 1);
