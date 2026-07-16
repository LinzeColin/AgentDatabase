#!/usr/bin/env node

"use strict";

const path = require("path");
const fs = require("fs");
const os = require("os");

const ROOT = path.resolve(__dirname, "../../..");
const RESULT_SCHEMA_VERSION =
  "memory_atlas.chatgpt_export_request_connector_result.v1_2_1_s08_p1_t1";
const CHATGPT_ORIGIN = "https://chatgpt.com";

class ConnectorError extends Error {
  constructor(code, options = {}) {
    super(code);
    this.name = "ConnectorError";
    this.code = code;
    this.requestClickCount = options.requestClickCount || 0;
    this.ownedTabClosed = Boolean(options.ownedTabClosed);
  }
}

function requirePlaywright() {
  const candidates = ["playwright", path.join(ROOT, "apps/memory-atlas/node_modules/playwright")];
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (error) {
      if (error && error.code !== "MODULE_NOT_FOUND") throw error;
    }
  }
  const pnpmRoot = path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm",
  );
  try {
    const candidate = fs
      .readdirSync(pnpmRoot)
      .filter((entry) => entry.startsWith("playwright@"))
      .sort()
      .at(-1);
    if (candidate) return require(path.join(pnpmRoot, candidate, "node_modules/playwright"));
  } catch {}
  throw new ConnectorError("playwright_unavailable");
}

function normalizeLoopbackCdpEndpoint(value) {
  if (typeof value !== "string" || value.length === 0 || value.length > 256) {
    throw new ConnectorError("cdp_endpoint_invalid");
  }
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new ConnectorError("cdp_endpoint_invalid");
  }
  if (
    parsed.protocol !== "http:" ||
    !["127.0.0.1", "[::1]"].includes(parsed.hostname) ||
    parsed.username ||
    parsed.password ||
    parsed.search ||
    parsed.hash ||
    !["", "/"].includes(parsed.pathname) ||
    !parsed.port
  ) {
    throw new ConnectorError("cdp_endpoint_invalid");
  }
  return `http://${parsed.hostname}:${parsed.port}`;
}

async function requireUniqueVisible(locator, unavailableCode, ambiguousCode) {
  const count = await locator.count();
  if (count === 0) throw new ConnectorError(unavailableCode);
  if (count !== 1) throw new ConnectorError(ambiguousCode);
  if (!(await locator.isVisible())) throw new ConnectorError(unavailableCode);
  return locator;
}

async function findExportButton(panel) {
  const labels = ["Export Export data", "Export data", "Export"];
  for (const label of labels) {
    const candidate = panel.getByRole("button", { name: label, exact: true });
    const count = await candidate.count();
    if (count === 1 && (await candidate.isVisible())) return candidate;
    if (count > 1) throw new ConnectorError("export_button_ambiguous");
  }
  throw new ConnectorError("export_button_unavailable");
}

async function hasExactVisibleHeading(page, names) {
  for (const name of names) {
    const candidate = page.getByRole("heading", { name, exact: true });
    const count = await candidate.count();
    if (count > 0 && (await candidate.first().isVisible())) return true;
  }
  return false;
}

async function detectHumanAuthChallenge(page) {
  let parsed;
  try {
    parsed = new URL(page.url());
  } catch {
    parsed = null;
  }
  if (parsed) {
    const host = parsed.hostname.toLowerCase();
    const pathname = parsed.pathname.toLowerCase();
    const officialAuthHost = new Set(["auth.openai.com", "auth0.openai.com"]).has(host);
    if (officialAuthHost && /(^|\/)(captcha|verify-human)(\/|$)/.test(pathname)) {
      return "captcha_required";
    }
    if (officialAuthHost && /(^|\/)(mfa|otp|two-factor|2fa)(\/|$)/.test(pathname)) {
      return "two_factor_required";
    }
    if (officialAuthHost && /(^|\/)(verify|challenge|confirm)(\/|$)/.test(pathname)) {
      return "account_confirmation_required";
    }
    if (officialAuthHost || (host === "chatgpt.com" && pathname === "/auth/login")) {
      return "login_required";
    }
  }
  if (
    await hasExactVisibleHeading(page, ["Verify you are human", "Security verification"])
  ) {
    return "captcha_required";
  }
  if (
    await hasExactVisibleHeading(page, [
      "Enter your verification code",
      "Verify with your authenticator app",
    ])
  ) {
    return "two_factor_required";
  }
  if (
    await hasExactVisibleHeading(page, [
      "Verify your identity",
      "Confirm your identity",
      "Confirm your account",
    ])
  ) {
    return "account_confirmation_required";
  }
  if (await hasExactVisibleHeading(page, ["Log in", "Welcome back", "Sign in"])) {
    return "login_required";
  }
  return null;
}

async function runVisibleUiWorkflow(page, options) {
  const mode = options && options.mode;
  const expectedOrigin = (options && options.expectedOrigin) || CHATGPT_ORIGIN;
  if (!new Set(["inspect", "request"]).has(mode)) {
    throw new ConnectorError("request_mode_invalid");
  }
  const humanAuthChallenge = await detectHumanAuthChallenge(page);
  if (humanAuthChallenge) throw new ConnectorError(humanAuthChallenge);
  let pageOrigin;
  try {
    pageOrigin = new URL(page.url()).origin;
  } catch {
    throw new ConnectorError("unexpected_page_origin");
  }
  if (pageOrigin !== expectedOrigin) throw new ConnectorError("unexpected_page_origin");

  const profile = await requireUniqueVisible(
    page.getByRole("button", { name: "Open profile menu", exact: true }),
    "profile_menu_unavailable",
    "profile_menu_ambiguous",
  );
  await profile.click();

  const settings = await requireUniqueVisible(
    page.getByRole("menuitem", { name: "Settings", exact: true }),
    "settings_menu_unavailable",
    "settings_menu_ambiguous",
  );
  await settings.click();

  const dataControls = await requireUniqueVisible(
    page.getByRole("tab", { name: "Data controls", exact: true }),
    "data_controls_unavailable",
    "data_controls_ambiguous",
  );
  await dataControls.click();

  const panel = await requireUniqueVisible(
    page.getByRole("tabpanel", { name: "Data controls", exact: true }),
    "data_controls_panel_unavailable",
    "data_controls_panel_ambiguous",
  );
  const exportButton = await findExportButton(panel);
  await exportButton.click();

  const dialog = await requireUniqueVisible(
    page.getByRole("dialog", {
      name: "Request data export - are you sure?",
      exact: true,
    }),
    "export_confirmation_unavailable",
    "export_confirmation_ambiguous",
  );
  if (mode === "inspect") {
    const cancel = await requireUniqueVisible(
      dialog.getByRole("button", { name: "Cancel", exact: true }),
      "cancel_button_unavailable",
      "cancel_button_ambiguous",
    );
    await cancel.click();
    return {
      schema_version: RESULT_SCHEMA_VERSION,
      status: "READY_TO_REQUEST",
      mode,
      action: "CANCELLED_BEFORE_REQUEST",
      visible_ui_only: true,
      existing_session_reused: true,
      request_click_count: 0,
      credential_store_access: false,
      private_api_calls: false,
    };
  }

  const confirm = await requireUniqueVisible(
    dialog.getByRole("button", { name: "Confirm export", exact: true }),
    "confirm_button_unavailable",
    "confirm_button_ambiguous",
  );
  try {
    await confirm.click();
  } catch {
    throw new ConnectorError("confirm_click_outcome_uncertain", { requestClickCount: 1 });
  }
  return {
    schema_version: RESULT_SCHEMA_VERSION,
    status: "REQUEST_ACTION_DISPATCHED",
    mode,
    action: "CONFIRM_EXPORT_CLICKED_ONCE",
    visible_ui_only: true,
    existing_session_reused: true,
    request_click_count: 1,
    credential_store_access: false,
    private_api_calls: false,
  };
}

function parseArgs(argv) {
  const parsed = { cdpEndpoint: null, mode: null, confirmRequest: false };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--cdp-endpoint" && index + 1 < argv.length) {
      parsed.cdpEndpoint = argv[++index];
    } else if (value === "--mode" && index + 1 < argv.length) {
      parsed.mode = argv[++index];
    } else if (value === "--confirm-request") {
      parsed.confirmRequest = true;
    } else {
      throw new ConnectorError("argument_invalid");
    }
  }
  if (!parsed.cdpEndpoint || !new Set(["inspect", "request"]).has(parsed.mode)) {
    throw new ConnectorError("argument_invalid");
  }
  if ((parsed.mode === "request") !== parsed.confirmRequest) {
    throw new ConnectorError("explicit_request_confirmation_required");
  }
  return parsed;
}

async function runConnector(args) {
  const endpoint = normalizeLoopbackCdpEndpoint(args.cdpEndpoint);
  const { chromium } = requirePlaywright();
  let browser;
  try {
    browser = await chromium.connectOverCDP(endpoint, { timeout: 15000 });
  } catch {
    throw new ConnectorError("browser_connection_failed");
  }
  const contexts = browser.contexts();
  if (contexts.length !== 1) throw new ConnectorError("browser_context_ambiguous");
  let page;
  let result;
  let workflowError;
  let ownedTabClosed = false;
  try {
    page = await contexts[0].newPage();
    await page.goto(`${CHATGPT_ORIGIN}/`, {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    result = await runVisibleUiWorkflow(page, {
      mode: args.mode,
      expectedOrigin: CHATGPT_ORIGIN,
    });
  } catch (error) {
    workflowError = error;
  }
  if (page) {
    try {
      await page.close({ runBeforeUnload: false });
      ownedTabClosed = true;
    } catch {
      const requestClickCount = result
        ? result.request_click_count
        : workflowError instanceof ConnectorError
          ? workflowError.requestClickCount
          : 0;
      throw new ConnectorError("owned_tab_cleanup_failed", { requestClickCount });
    }
  }
  if (workflowError) {
    if (workflowError instanceof ConnectorError) {
      workflowError.ownedTabClosed = ownedTabClosed;
      throw workflowError;
    }
    throw workflowError;
  }
  return { ...result, owned_tab_closed: ownedTabClosed };
}

async function cli(argv) {
  try {
    const args = parseArgs(argv);
    const result = await runConnector(args);
    process.stdout.write(`${JSON.stringify(result)}\n`, () => process.exit(0));
  } catch (error) {
    const code = error instanceof ConnectorError ? error.code : "connector_unhandled_error";
    const payload = {
      schema_version: RESULT_SCHEMA_VERSION,
      status: "FAIL",
      error_code: code,
      request_click_count: error instanceof ConnectorError ? error.requestClickCount : 0,
      credential_store_access: false,
      private_api_calls: false,
      owned_tab_closed: error instanceof ConnectorError ? error.ownedTabClosed : false,
    };
    process.stdout.write(`${JSON.stringify(payload)}\n`, () => process.exit(2));
  }
}

module.exports = {
  ConnectorError,
  detectHumanAuthChallenge,
  normalizeLoopbackCdpEndpoint,
  runConnector,
  runVisibleUiWorkflow,
};

if (require.main === module) {
  void cli(process.argv.slice(2));
}
