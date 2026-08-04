#!/usr/bin/env node
// v0.0.0.32 #20 — the page must be Chinese (UI_UX_VISUAL_CONTRACT).
//
//   audit_chinese_ui_v32.mjs <url> <output.json>
//
// Walks every route and reports visible text nodes that carry no Chinese. The
// contract keeps protocol fields, code identifiers and third-party names in
// their native form, so those are allowlisted explicitly — by exact token or by
// living inside a machine-field section, never by pattern-matching "looks
// technical", which would excuse the leaks this exists to catch.
import fs from "node:fs/promises";
import process from "node:process";
import { chromium } from "playwright";

const [url, output] = process.argv.slice(2);
if (!url || !output) {
  console.error("usage: audit_chinese_ui_v32.mjs <url> <output.json>");
  process.exit(2);
}

const VIEWS = [
  "home", "galaxy", "notion", "roi", "obsidian", "timeline", "contribution",
  "wordcloud", "search", "summary", "failureCompound", "behaviorEconomy", "runtime",
];

// Native by contract: product names, third-party names, protocol/format words.
const ALLOWED = new Set([
  "Memory Atlas", "Codex", "ChatGPT", "OpenAI", "Notion", "Obsidian", "GitHub",
  "Cloudflare", "ROI", "Three.js", "GSAP", "API", "JSON", "URL", "ID", "Agent",
  "Meta", "Data", "R2", "OVH", "PDB", "Tier A", "Tier B", "PASS", "FAIL",
  "FRESH", "STALE", "DEGRADED", "UNKNOWN", "UNVERIFIED", "OBSERVED", "VERIFIED",
  "GRID", "TREND", "HEATMAP", "Time-to-Truth", "true", "false",
]);

// Sections that exist to show machine fields; they are collapsed by default and
// the contract explicitly permits raw identifiers there.
const MACHINE_CONTEXTS = [
  ".machine-field-details", "[data-machine-fields]", ".ma-limitations",
  ".ma-evidence-grid", ".ma-truth-ribbon", "code", "pre",
];

const browser = await chromium.launch({ headless: true });
const findings = [];
try {
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90_000 });
  await page.locator(".app-shell").waitFor({ state: "visible", timeout: 60_000 });

  for (const view of VIEWS) {
    try {
      await page.locator(`[data-nav-view="${view}"]`).click();
      await page.locator(`[data-view="${view}"]`).waitFor({ state: "visible", timeout: 20_000 });
      await page.waitForTimeout(600);
    } catch {
      findings.push({ view, kind: "unreachable", text: "" });
      continue;
    }
    const rows = await page.locator(`[data-view="${view}"]`).evaluateAll(
      (nodes, contexts) => {
        const out = [];
        const walk = (el) => {
          if (contexts.some((selector) => el.closest?.(selector))) return;
          for (const child of el.childNodes) {
            if (child.nodeType === 3) {
              const text = child.textContent.trim();
              if (text && !/[一-鿿]/.test(text) && /[A-Za-z_]{2,}/.test(text)) {
                out.push(text.slice(0, 90));
              }
            } else if (child.nodeType === 1 && getComputedStyle(child).display !== "none") {
              walk(child);
            }
          }
        };
        nodes.forEach(walk);
        return [...new Set(out)];
      },
      MACHINE_CONTEXTS,
    );
    for (const text of rows) {
      if (ALLOWED.has(text)) continue;
      // A line built only from allowed names and separators is still native by
      // contract, e.g. "Codex / Memory Atlas".
      const residue = text.split(/[\s/·,、|:()]+/).filter((part) => part && !ALLOWED.has(part));
      if (residue.length === 0) continue;
      findings.push({
        view,
        kind: /:edge:|mem_[0-9a-f]{8}|_[a-z]+\.v\d|[a-z]+_[a-z]+/.test(text)
          ? "machine_identifier"
          : "untranslated",
        text,
      });
    }
  }
} finally {
  await browser.close();
}

const report = {
  schema_version: "memory_atlas.chinese_ui_audit.v1",
  captured_at: new Date().toISOString(),
  page_url: url,
  verdict: findings.length === 0 ? "PASS" : "FAIL",
  finding_count: findings.length,
  by_view: Object.fromEntries(
    VIEWS.map((view) => [view, findings.filter((row) => row.view === view).length]).filter(([, n]) => n),
  ),
  findings,
};
await fs.writeFile(output, JSON.stringify(report, null, 2) + "\n", { encoding: "utf8", mode: 0o600 });
console.log(`${report.verdict} — ${findings.length} findings across ${Object.keys(report.by_view).length} views`);
process.exit(report.verdict === "PASS" ? 0 : 1);
