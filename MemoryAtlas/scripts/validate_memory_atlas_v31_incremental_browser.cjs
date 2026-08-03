#!/usr/bin/env node
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

function rgb(value) {
  const match = String(value).match(/rgba?\((\d+)[, ]+\s*(\d+)[, ]+\s*(\d+)/i);
  return match ? match.slice(1, 4).map(Number) : null;
}
function luminance([r, g, b]) {
  const channels = [r, g, b].map(v => {
    const x = v / 255;
    return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}
function contrast(a, b) {
  const l1 = luminance(a), l2 = luminance(b);
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
}

(async () => {
  const base = process.env.MEMORY_ATLAS_BASE_URL || "http://127.0.0.1:4173";
  const out = process.env.MEMORY_ATLAS_EVIDENCE_DIR || path.resolve(process.cwd(), ".taskpack-runs/memory-atlas-v31/browser");
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const rows = [];
  const add = (id, pass, evidence) => rows.push({ id, pass: Boolean(pass), evidence });
  const original = ["home","galaxy","notion","roi","obsidian","timeline","contribution","wordcloud","search","summary"];
  const added = ["failureCompound","behaviorEconomy","runtime"];
  try {
    await page.goto(base, { waitUntil: "networkidle", timeout: 60000 });
    await page.locator(".app-shell").waitFor({ state: "visible", timeout: 30000 });
    add("BROWSER-default-home", await page.locator('[data-view="home"]').isVisible(), "home visible");
    add("BROWSER-no-parallel-root", await page.locator('.ma31-root,.ma31-legacy-boundary').count() === 0, "no wrapper");
    add("BROWSER-13-nav", await page.locator('[data-nav-view]').count() === 13, await page.locator('[data-nav-view]').count());
    for (const selector of [".controls", ".interaction-lens", ".command-palette", ".help-launch-button"]) {
      add(`BROWSER-original-surface-${selector}`, await page.locator(selector).first().isVisible(), selector);
    }

    const signatures = {};
    for (const theme of ["A", "B", "C"]) {
      await page.getByRole("button", { name: `切换到主题 ${theme}` }).click();
      add(`BROWSER-theme-${theme}`, await page.locator(`.app-shell[data-memory-atlas-theme="${theme}"]`).count() === 1, theme);
      signatures[theme] = await page.evaluate(() => {
        const shell = getComputedStyle(document.querySelector(".app-shell"));
        const sidebar = getComputedStyle(document.querySelector(".sidebar"));
        const nav = getComputedStyle(document.querySelector(".nav-list"));
        const heading = getComputedStyle(document.querySelector(".topbar h1"));
        return {
          shellColumns: shell.gridTemplateColumns,
          shellRows: shell.gridTemplateRows,
          sidebarDisplay: sidebar.display,
          sidebarPosition: sidebar.position,
          navDisplay: nav.display,
          headingFont: heading.fontFamily,
        };
      });
      for (const mode of [{ name: "白色模式", value: "light" }, { name: "黑色模式", value: "dark" }]) {
        await page.getByRole("button", { name: mode.name }).click();
        add(`BROWSER-${theme}-mode-${mode.value}`, await page.locator(`.app-shell[data-memory-atlas-mode="${mode.value}"]`).count() === 1, mode.value);
        const palette = await page.evaluate(() => {
          const sidebar = getComputedStyle(document.querySelector(".sidebar"));
          const heading = getComputedStyle(document.querySelector(".topbar h1"));
          return { background: sidebar.backgroundColor, foreground: heading.color, colorScheme: getComputedStyle(document.documentElement).colorScheme };
        });
        const bg = rgb(palette.background), fg = rgb(palette.foreground);
        add(`BROWSER-${theme}-${mode.value}-palette-resolved`, Boolean(bg && fg), palette);
        if (bg && fg) {
          add(`BROWSER-${theme}-${mode.value}-contrast`, contrast(bg, fg) >= 4.5, { ...palette, contrast: contrast(bg, fg) });
          add(`BROWSER-${theme}-${mode.value}-luminance-direction`, mode.value === "light" ? luminance(bg) > 0.65 : luminance(bg) < 0.20, { background: palette.background, luminance: luminance(bg) });
        }
        for (const key of [...original, ...added]) {
          await page.locator(`[data-nav-view="${key}"]`).click();
          await page.locator(`[data-view="${key}"]`).waitFor({ state: "visible", timeout: 20000 });
          add(`BROWSER-${theme}-${mode.value}-route-${key}`, await page.locator(`[data-view="${key}"]`).isVisible(), key);
        }
        await page.screenshot({ path: path.join(out, `memory-atlas-${theme}-${mode.value}.png`), fullPage: true });
      }
    }
    const distinct = new Set(Object.values(signatures).map(x => JSON.stringify(x))).size;
    add("BROWSER-three-distinct-layouts", distinct === 3, signatures);

    await page.setViewportSize({ width: 390, height: 844 });
    for (const theme of ["A", "B", "C"]) {
      await page.getByRole("button", { name: `切换到主题 ${theme}` }).click();
      await page.getByRole("button", { name: "白色模式" }).click();
      await page.locator('[data-nav-view="home"]').click();
      const viewport = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        scrollHeight: document.documentElement.scrollHeight,
      }));
      add(`BROWSER-mobile-${theme}-no-horizontal-overflow`, viewport.scrollWidth <= viewport.clientWidth + 1, viewport);
    }
  } catch (error) {
    add("BROWSER-execution", false, String(error?.stack || error));
  } finally {
    await browser.close();
  }
  const failed = rows.filter(x => !x.pass);
  const report = { schema_version: "memory_atlas.incremental_browser_validation.v2", base, pass: failed.length === 0, row_count: rows.length, rows, failed };
  fs.writeFileSync(path.join(out, "browser-validation.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (failed.length) process.exit(1);
})().catch(e => { console.error(e); process.exit(1); });
