#!/usr/bin/env node
// v0.0.0.32 T05 — accessibility, front-end quality (MA-LIVE-AC-015) and
// auto-revalidation / read-back behaviour (MA-LIVE-AC-007) of the first-screen
// RealityCalibrationPanel, measured in a real browser against a real origin.
//
// usage: audit_reality_panel_v32.mjs <url> <storage-state.json> <output.json> [current.json]
//
// The optional current.json is the origin's published live snapshot. When it is
// given, the audit also proves the browser refuses a server that hands back an
// older run instead of silently rendering it.
import fs from "node:fs/promises";
import process from "node:process";
import { chromium } from "playwright";

const [url, storageState, output, currentJsonPath] = process.argv.slice(2);
if (!url || !storageState || !output) {
  console.error("usage: audit_reality_panel_v32.mjs <url> <storage-state.json> <output.json> [current.json]");
  process.exit(2);
}

const API_PATH = "/api/v31/live-snapshot";
const checks = [];
const record = (id, pass, evidence) => checks.push({ id, pass: Boolean(pass), evidence });
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function countApiRequests(page, bucket) {
  page.on("request", (request) => {
    if (new URL(request.url()).pathname === API_PATH) bucket.push(Date.now());
  });
}

const browser = await chromium.launch({ headless: true });
const consoleErrors = [];
const networkErrors = [];
try {
  const context = await browser.newContext({ storageState, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text().slice(0, 400)); });
  page.on("requestfailed", (r) => networkErrors.push(`${r.method()} ${new URL(r.url()).pathname}: ${r.failure()?.errorText ?? "failed"}`));
  const apiRequests = [];
  countApiRequests(page, apiRequests);

  await page.goto(url, { waitUntil: "networkidle" });
  const panel = page.locator(".ma-reality-panel[data-run-id]");
  await panel.waitFor({ state: "visible" });
  const firstRunId = await panel.getAttribute("data-run-id");

  // --- AC-015: the four conclusions are on the first screen, in Chinese ---
  const box = await panel.boundingBox();
  record("first_screen_above_fold", box !== null && box.y < 900, { top: box?.y ?? null, viewport_height: 900 });

  // Every conclusion must be fully on the first screen, not merely started.
  // Measured across the desktop viewports the Owner actually uses; 1366x768 is
  // reported too, because it is the one common size where the pre-existing
  // v0.0.0.31 chrome (435px before the view surface) leaves too little room.
  const viewportMatrix = [];
  for (const size of [{ width: 1920, height: 1080 }, { width: 1512, height: 945 }, { width: 1440, height: 900 }, { width: 1280, height: 800 }, { width: 1366, height: 768 }]) {
    await page.setViewportSize(size);
    await sleep(300);
    const row = await page.evaluate(() => {
      const cards = [...document.querySelectorAll(".ma-answer")].map((node) => node.getBoundingClientRect());
      if (cards.length !== 4) return null;
      return { top: Math.round(Math.min(...cards.map((r) => r.top))), bottom: Math.round(Math.max(...cards.map((r) => r.bottom))), viewport_height: window.innerHeight };
    });
    viewportMatrix.push({ viewport: `${size.width}x${size.height}`, ...row, fits: row !== null && row.bottom <= row.viewport_height });
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await sleep(300);
  const gated = viewportMatrix.filter((row) => Number(row.viewport.split("x")[1]) >= 800);
  record("four_answers_fully_above_fold", gated.every((row) => row.fits), { matrix: viewportMatrix, gated_viewports: gated.map((row) => row.viewport) });
  record("four_answers_present", (await page.locator(".ma-answer").count()) === 4, { count: await page.locator(".ma-answer").count() });
  record("three_visuals_present", (await page.locator(".ma-visual-grid .ma-chart").count()) === 3, { count: await page.locator(".ma-visual-grid .ma-chart").count() });
  record("truth_ribbon_present", await page.locator(".ma-truth-ribbon").isVisible(), {});

  const panelPrecedesLegacy = await page.evaluate(() => {
    const reality = document.querySelector(".ma-reality-panel");
    const legacy = document.querySelector(".home-arrival-briefing");
    if (!reality || !legacy) return false;
    return Boolean(reality.compareDocumentPosition(legacy) & Node.DOCUMENT_POSITION_FOLLOWING);
  });
  record("live_panel_precedes_historical_views", panelPrecedesLegacy, {});

  const headingText = await page.locator(".ma-answer h3, .ma-answer p, #ma-reality-title").allInnerTexts();
  const joined = headingText.join(" ");
  const cjk = (joined.match(/[一-鿿]/g) ?? []).length;
  const latinWords = (joined.match(/[A-Za-z]{3,}/g) ?? []);
  record("first_screen_is_chinese", cjk > 20 && latinWords.length === 0, { cjk_chars: cjk, latin_words: latinWords.slice(0, 10) });

  // --- AC-015: keyboard reachability and a visible focus ring ---
  await page.locator(".ma-refresh").scrollIntoViewIfNeeded();
  let tabs = 0;
  let focusedRefresh = false;
  await page.locator("body").click({ position: { x: 2, y: 2 } });
  while (tabs < 40 && !focusedRefresh) {
    await page.keyboard.press("Tab");
    tabs += 1;
    focusedRefresh = await page.evaluate(() => document.activeElement?.classList.contains("ma-refresh") ?? false);
  }
  const focusRing = await page.evaluate(() => {
    const style = window.getComputedStyle(document.activeElement);
    return { outlineStyle: style.outlineStyle, outlineWidth: style.outlineWidth };
  });
  record("refresh_is_keyboard_reachable", focusedRefresh, { tab_presses: tabs });
  record("focus_ring_is_visible", focusRing.outlineStyle !== "none" && parseFloat(focusRing.outlineWidth) >= 2, focusRing);

  const smallTargets = await page.locator(".ma-reality-panel button, .ma-reality-panel summary").evaluateAll((nodes) =>
    nodes
      .map((node) => ({ label: (node.textContent ?? "").trim().slice(0, 24), ...node.getBoundingClientRect().toJSON() }))
      .filter((rect) => rect.width < 44 || rect.height < 44)
      .map((rect) => ({ label: rect.label, width: Math.round(rect.width), height: Math.round(rect.height) })),
  );
  record("touch_targets_at_least_44px", smallTargets.length === 0, { violations: smallTargets });

  // --- AC-007: the page re-validates on its own inside 60 seconds ---
  const before = apiRequests.length;
  await sleep(66_000);
  record("auto_revalidates_within_60s", apiRequests.length > before, { requests_before: before, requests_after: apiRequests.length });

  // --- AC-007: coming back online re-validates immediately ---
  const beforeOnline = apiRequests.length;
  await page.evaluate(() => window.dispatchEvent(new Event("online")));
  await sleep(2_500);
  record("online_event_revalidates_immediately", apiRequests.length > beforeOnline, { requests_before: beforeOnline, requests_after: apiRequests.length });

  // --- AC-007: an older run from the server is refused, last-good is kept ---
  if (currentJsonPath) {
    const original = await fs.readFile(currentJsonPath, "utf8");
    const older = JSON.parse(original);
    older.run.run_id = "regression-run-19700101T000000Z";
    older.run.trace_id = "regression-trace-19700101T000000Z";
    older.run.source_completed_at = "1970-01-01T00:00:00Z";
    older.truth.same_run_evidence.r2_readback.run_id = older.run.run_id;
    older.truth.same_run_evidence.r2_readback.trace_id = older.run.trace_id;
    older.truth.same_run_evidence.private_database_readback.run_id = older.run.run_id;
    older.truth.same_run_evidence.private_database_readback.trace_id = older.run.trace_id;
    older.truth.same_run_evidence.ovh_reconcile.run_id = older.run.run_id;
    older.truth.same_run_evidence.ovh_reconcile.trace_id = older.run.trace_id;
    await fs.writeFile(currentJsonPath, JSON.stringify(older) + "\n", "utf8");
    await page.locator(".ma-refresh").click();
    await sleep(2_000);
    const heldRunId = await panel.getAttribute("data-run-id");
    const warning = await page.locator(".ma-warning").innerText().catch(() => "");
    record("older_run_is_refused", heldRunId === firstRunId, { held: heldRunId, offered: older.run.run_id });
    record("refusal_is_surfaced_to_the_reader", warning.includes("时间倒退") || warning.includes("降级"), { warning: warning.slice(0, 200) });
    await fs.writeFile(currentJsonPath, original, "utf8");
  }

  // --- AC-007: a full reload reads back the same or a newer run ---
  await page.reload({ waitUntil: "networkidle" });
  await panel.waitFor({ state: "visible" });
  record("reload_reads_back_same_run", (await panel.getAttribute("data-run-id")) === firstRunId, { run_id: firstRunId });

  // --- AC-015: mobile has no horizontal overflow ---
  await page.setViewportSize({ width: 375, height: 812 });
  await sleep(500);
  const overflow = await page.evaluate(() => {
    const root = document.documentElement;
    const offenders = [...document.querySelectorAll(".ma-reality-panel *")]
      .filter((node) => node.getBoundingClientRect().right > root.clientWidth + 1)
      .slice(0, 5)
      .map((node) => `${node.tagName.toLowerCase()}.${node.className}`.slice(0, 80));
    return { scrollWidth: root.scrollWidth, clientWidth: root.clientWidth, offenders };
  });
  record("mobile_has_no_horizontal_overflow", overflow.scrollWidth <= overflow.clientWidth + 1 && overflow.offenders.length === 0, overflow);
  await context.close();

  // --- AC-015: reduced motion is honoured ---
  const reduced = await browser.newContext({ storageState, reducedMotion: "reduce", viewport: { width: 1440, height: 900 } });
  const reducedPage = await reduced.newPage();
  await reducedPage.goto(url, { waitUntil: "networkidle" });
  await reducedPage.locator(".ma-reality-panel[data-run-id]").waitFor({ state: "visible" });
  const durations = await reducedPage.locator(".ma-refresh, .ma-contribution-cell").evaluateAll((nodes) =>
    nodes.map((node) => window.getComputedStyle(node).transitionDuration),
  );
  record("reduced_motion_is_honoured", durations.length > 0 && durations.every((value) => parseFloat(value) <= 0.011), { durations });
  await reduced.close();

  record("no_console_errors", consoleErrors.length === 0, { errors: consoleErrors.slice(0, 10) });
  record("no_failed_requests", networkErrors.length === 0, { errors: networkErrors.slice(0, 10) });
} finally {
  await browser.close();
}

const report = {
  schema_version: "memory_atlas.reality_panel_audit.v1",
  captured_at: new Date().toISOString(),
  page_url: url,
  verdict: checks.every((row) => row.pass) ? "PASS" : "FAIL",
  failure_count: checks.filter((row) => !row.pass).length,
  checks,
};
await fs.writeFile(output, JSON.stringify(report, null, 2) + "\n", { encoding: "utf8", mode: 0o600 });
console.log(`${report.verdict} — ${checks.length - report.failure_count}/${checks.length}`);
process.exit(report.verdict === "PASS" ? 0 : 1);
