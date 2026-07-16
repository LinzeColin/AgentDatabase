#!/usr/bin/env node

"use strict";

const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const CONNECTOR_PATH = path.join(
  ROOT,
  "apps/memory-atlas/scripts/chatgpt_export_request_connector.cjs",
);

function requirePlaywright() {
  const candidates = [
    "playwright",
    path.join(ROOT, "apps/memory-atlas/node_modules/playwright"),
  ];
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
  throw new Error("Playwright is not available");
}

function fixtureHtml(options = {}) {
  const challengeHeadings = {
    login: "Log in",
    "two-factor": "Enter your verification code",
    captcha: "Verify you are human",
    "account-confirmation": "Confirm your account",
  };
  const challengeHeading = challengeHeadings[options.challenge] || "";
  const profileButtons = options.duplicateProfile
    ? '<button aria-label="Open profile menu">Profile A</button><button aria-label="Open profile menu">Profile B</button>'
    : options.missingProfile
      ? ""
      : '<button aria-label="Open profile menu" id="profile">Profile</button>';
  return `<!doctype html>
<html lang="en">
  <body>
    ${challengeHeading ? `<h1>${challengeHeading}</h1>` : ""}
    ${profileButtons}
    <div role="menu" id="profile-menu" hidden>
      <button role="menuitem" id="settings">Settings</button>
    </div>
    <div role="dialog" aria-label="General" id="settings-dialog" hidden>
      <button role="tab" id="data-controls">Data controls</button>
      <div role="tabpanel" aria-label="Data controls" id="data-panel" hidden>
        <span>Export data</span>
        <button aria-label="Export Export data" id="export-data">Export</button>
      </div>
    </div>
    <div role="dialog" aria-label="Request data export - are you sure?" id="confirm-dialog" hidden>
      <h2>Request data export - are you sure?</h2>
      <p>To proceed, click "Confirm export" below.</p>
      <button id="confirm-export">Confirm export</button>
      <button id="cancel-export">Cancel</button>
    </div>
    <div role="status" id="status"></div>
    <script>
      window.requestClicks = 0;
      const profile = document.getElementById("profile");
      if (profile) profile.addEventListener("click", () => {
        document.getElementById("profile-menu").hidden = false;
      });
      document.getElementById("settings").addEventListener("click", () => {
        document.getElementById("settings-dialog").hidden = false;
      });
      document.getElementById("data-controls").addEventListener("click", () => {
        document.getElementById("data-panel").hidden = false;
      });
      document.getElementById("export-data").addEventListener("click", () => {
        document.getElementById("confirm-dialog").hidden = false;
      });
      document.getElementById("cancel-export").addEventListener("click", () => {
        document.getElementById("confirm-dialog").hidden = true;
      });
      document.getElementById("confirm-export").addEventListener("click", () => {
        window.requestClicks += 1;
        document.getElementById("confirm-dialog").hidden = true;
        document.getElementById("status").textContent = "Export request action dispatched";
      });
    </script>
  </body>
</html>`;
}

async function listen(server) {
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  return server.address().port;
}

async function closeServer(server) {
  await new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

async function main() {
  const {
    ConnectorError,
    detectHumanAuthChallenge,
    normalizeLoopbackCdpEndpoint,
    runVisibleUiWorkflow,
  } = require(CONNECTOR_PATH);
  const { chromium } = requirePlaywright();
  const server = http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    const mode = url.searchParams.get("fixture") || "normal";
    response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    response.end(
      fixtureHtml({
        duplicateProfile: mode === "duplicate-profile",
        missingProfile: mode === "missing-profile",
        challenge: mode,
      }),
    );
  });
  const port = await listen(server);
  const origin = `http://127.0.0.1:${port}`;
  const launchOptions = { headless: true };
  const chromePath = process.env.PLAYWRIGHT_CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  if (fs.existsSync(chromePath)) launchOptions.executablePath = chromePath;
  const browser = await chromium.launch(launchOptions);

  try {
    const inspectPage = await browser.newPage();
    await inspectPage.goto(`${origin}/?fixture=normal`);
    const inspect = await runVisibleUiWorkflow(inspectPage, {
      mode: "inspect",
      expectedOrigin: origin,
    });
    const inspectClicks = await inspectPage.evaluate(() => window.requestClicks);

    const requestPage = await browser.newPage();
    await requestPage.goto(`${origin}/?fixture=normal`);
    const request = await runVisibleUiWorkflow(requestPage, {
      mode: "request",
      expectedOrigin: origin,
    });
    const requestClicks = await requestPage.evaluate(() => window.requestClicks);

    const missingPage = await browser.newPage();
    await missingPage.goto(`${origin}/?fixture=missing-profile`);
    let missingError = null;
    try {
      await runVisibleUiWorkflow(missingPage, { mode: "inspect", expectedOrigin: origin });
    } catch (error) {
      if (!(error instanceof ConnectorError)) throw error;
      missingError = error.code;
    }

    const duplicatePage = await browser.newPage();
    await duplicatePage.goto(`${origin}/?fixture=duplicate-profile`);
    let duplicateError = null;
    try {
      await runVisibleUiWorkflow(duplicatePage, { mode: "inspect", expectedOrigin: origin });
    } catch (error) {
      if (!(error instanceof ConnectorError)) throw error;
      duplicateError = error.code;
    }

    const wrongOriginPage = await browser.newPage();
    await wrongOriginPage.goto(`${origin}/?fixture=normal`);
    let originError = null;
    try {
      await runVisibleUiWorkflow(wrongOriginPage, {
        mode: "inspect",
        expectedOrigin: "https://chatgpt.com",
      });
    } catch (error) {
      if (!(error instanceof ConnectorError)) throw error;
      originError = error.code;
    }

    const humanAuthScenarios = [
      ["login", "login_required"],
      ["two-factor", "two_factor_required"],
      ["captcha", "captcha_required"],
      ["account-confirmation", "account_confirmation_required"],
    ];
    const humanAuthResults = {};
    for (const [fixture, expectedCode] of humanAuthScenarios) {
      const page = await browser.newPage();
      await page.goto(`${origin}/?fixture=${fixture}`);
      humanAuthResults[fixture] = await detectHumanAuthChallenge(page);
      let workflowError = null;
      try {
        await runVisibleUiWorkflow(page, { mode: "inspect", expectedOrigin: origin });
      } catch (error) {
        if (!(error instanceof ConnectorError)) throw error;
        workflowError = error.code;
      }
      if (workflowError !== expectedCode) {
        throw new Error(JSON.stringify({ fixture, expectedCode, workflowError }));
      }
      await page.close();
    }
    const officialAuthUrlScenarios = [
      ["https://auth.openai.com/u/login", "login_required"],
      ["https://auth.openai.com/u/login/mfa", "two_factor_required"],
      ["https://auth.openai.com/captcha", "captcha_required"],
      ["https://auth.openai.com/u/verify", "account_confirmation_required"],
    ];
    const officialAuthUrlResults = {};
    for (const [url, expectedCode] of officialAuthUrlScenarios) {
      const urlOnlyPage = {
        url: () => url,
        getByRole: () => {
          throw new Error("visible marker lookup must not be needed for official auth URLs");
        },
      };
      officialAuthUrlResults[url] = await detectHumanAuthChallenge(urlOnlyPage);
      if (officialAuthUrlResults[url] !== expectedCode) {
        throw new Error(JSON.stringify({ url, expectedCode, officialAuthUrlResults }));
      }
    }

    const source = fs.readFileSync(CONNECTOR_PATH, "utf8");
    const forbiddenSourcePatterns = [
      ".cookies(",
      ".storageState(",
      "localStorage",
      "sessionStorage",
      "XMLHttpRequest",
      "/backend-api",
      "launchPersistentContext",
      ".fill(",
      ".type(",
      "inputValue(",
    ];
    const forbiddenMatches = forbiddenSourcePatterns.filter((value) => source.includes(value));

    const endpointChecks = [
      normalizeLoopbackCdpEndpoint("http://127.0.0.1:9222") === "http://127.0.0.1:9222",
      normalizeLoopbackCdpEndpoint("http://[::1]:9333/") === "http://[::1]:9333",
    ];
    let remoteEndpointRejected = false;
    try {
      normalizeLoopbackCdpEndpoint("http://192.168.1.2:9222");
    } catch (error) {
      remoteEndpointRejected = error instanceof ConnectorError;
    }

    const assertions = [
      inspect.status === "READY_TO_REQUEST",
      inspect.action === "CANCELLED_BEFORE_REQUEST",
      inspect.request_click_count === 0,
      inspectClicks === 0,
      request.status === "REQUEST_ACTION_DISPATCHED",
      request.request_click_count === 1,
      requestClicks === 1,
      missingError === "profile_menu_unavailable",
      duplicateError === "profile_menu_ambiguous",
      originError === "unexpected_page_origin",
      humanAuthScenarios.every(
        ([fixture, expectedCode]) => humanAuthResults[fixture] === expectedCode,
      ),
      officialAuthUrlScenarios.every(
        ([url, expectedCode]) => officialAuthUrlResults[url] === expectedCode,
      ),
      forbiddenMatches.length === 0,
      endpointChecks.every(Boolean),
      remoteEndpointRejected,
    ];
    if (!assertions.every(Boolean)) {
      throw new Error(JSON.stringify({ assertions, forbiddenMatches }));
    }

    process.stdout.write(
      `${JSON.stringify({
        schema_version: "memory_atlas.chatgpt_export_request_browser_fixture.v1_2_1_s08_p1_t1",
        status: "PASS",
        scenario_count: 10,
        human_auth_challenges: humanAuthResults,
        official_auth_url_checks: officialAuthUrlResults,
        request_clicks: { inspect: inspectClicks, request: requestClicks },
        credential_store_access: false,
        private_api_calls: false,
      })}\n`,
    );
  } finally {
    await browser.close();
    await closeServer(server);
  }
}

main().catch((error) => {
  process.stderr.write(`${error && error.stack ? error.stack : String(error)}\n`);
  process.exitCode = 1;
});
