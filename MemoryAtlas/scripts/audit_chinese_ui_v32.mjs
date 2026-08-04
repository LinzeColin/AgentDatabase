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

const [url, output, liveAtlas, liveSnapshot, liveStatus] = process.argv.slice(2);
if (!url || !output) {
  console.error("usage: audit_chinese_ui_v32.mjs <url> <output.json> [live-atlas.json] [live-snapshot.json] [live-status.json]");
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
  // Third-party product names, repository names, and real file/bucket paths.
  "GPT", "Claude Code", "Claude", "Private-Database", "Private-AgentDatabase",
  "config.toml", "AGENTS.md", "primary-objects/", "`primary-objects/`",
  "Playwright", "Vite", "React",
]);

// Sections that exist to show machine fields; they are collapsed by default and
// the contract explicitly permits raw identifiers there.
const MACHINE_CONTEXTS = [
  ".machine-field-details", "[data-machine-fields]", ".ma-limitations",
  ".ma-evidence-grid", ".ma-truth-ribbon", "code", "pre",
];

// The contract requires the *interface* to be Chinese. It does not require the
// user's own content to be rewritten: a memory titled "arXiv Daily Push", a
// project called "KMFA", a word cloud built from their vocabulary. Translating
// those would falsify the data the page exists to show. Elements that render
// user-authored strings verbatim mark themselves, so this stays a property of
// the markup rather than a growing allowlist of the Owner's project names.
const USER_CONTENT_CONTEXTS = ["[data-user-content]"];

// Archived records reproduced verbatim under a source contract and a digest —
// the sealed incident ledger, whose titles other checks verify by hash.
// Rewriting them would falsify the record, so the interface around them is
// Chinese and the records themselves are marked and skipped.
const VERBATIM_RECORD_CONTEXTS = ["[data-record-verbatim]"];

const browser = await chromium.launch({ headless: true });
const findings = [];
try {
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  // Two views read the live API and the ten original views read the atlas the
  // origin regenerates. Without these the audit runs against a build-time
  // snapshot and reports PASS on vocabulary the browser never renders.
  if (liveAtlas) {
    const body = await fs.readFile(liveAtlas, "utf8");
    await page.route("**/memory_atlas.json", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body }));
  }
  if (liveSnapshot) {
    const body = await fs.readFile(liveSnapshot, "utf8");
    await page.route("**/api/v31/live-snapshot", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body }));
  }
  // The failure-compound and behaviour-economy views read /api/v31/status.
  // Without it they render empty locally and the audit reported PASS while
  // production rendered dozens of raw incident and outcome keys.
  if (liveStatus) {
    const body = await fs.readFile(liveStatus, "utf8");
    await page.route("**/api/v31/status**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body }));
  }
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
      [...MACHINE_CONTEXTS, ...USER_CONTENT_CONTEXTS, ...VERBATIM_RECORD_CONTEXTS],
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
  live_data: { atlas: liveAtlas ?? null, snapshot: liveSnapshot ?? null, status: liveStatus ?? null },
  verdict: findings.length === 0 ? "PASS" : "FAIL",
  finding_count: findings.length,
  by_view: Object.fromEntries(
    VIEWS.map((view) => [view, findings.filter((row) => row.view === view).length]).filter(([, n]) => n),
  ),
  skipped_contexts: {
    machine_fields: MACHINE_CONTEXTS, user_content: USER_CONTENT_CONTEXTS,
    verbatim_records: VERBATIM_RECORD_CONTEXTS,
  },
  findings,
};
await fs.writeFile(output, JSON.stringify(report, null, 2) + "\n", { encoding: "utf8", mode: 0o600 });
console.log(`${report.verdict} — ${findings.length} findings across ${Object.keys(report.by_view).length} views`);
process.exit(report.verdict === "PASS" ? 0 : 1);
