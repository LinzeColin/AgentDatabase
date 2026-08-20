/**
 * Host half of the HarnessUI skin — and the asset server it needs.
 *
 * Why the server lives here instead of being a separate LaunchAgent:
 * this build serves exactly one file per plugin (`/plugins/<pkg>/client.js`);
 * every other path under a mounted plugin returns 404, and the renderer refuses
 * `file://`. So the browser half can only reach artwork over http. That used to
 * mean a second process the user had to remember to start — and the first time
 * it was stopped, DSH silently lost every backdrop while the picker still
 * worked, which reads as "the skin is broken".
 *
 * Kimi's shell has no such problem: it registers a `kimiskin://` protocol and
 * reads straight off disk. The equivalent here is to put the server inside the
 * plugin, so installing the plugin is the whole install. Nothing to launch,
 * nothing to remember, and it dies with DSH instead of outliving it.
 *
 * Serves ~/.harness-ui: master PNGs, thumbnails, the catalogue, and the shared
 * state file that the menu-bar controller and the Kimi shell also read.
 */

import { createServer } from "node:http";
import { createReadStream, existsSync, mkdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { extname, join, normalize, resolve, sep } from "node:path";
import { homedir } from "node:os";

const name = "dsh-harness-ui-skins";
const inject = [];

const ROOT = join(homedir(), ".harness-ui");
const PORT = Number(process.env.HARNESS_UI_PORT || 3099);
const TYPES = {
  ".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg", ".json": "application/json", ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
};

/** Keys the browser half is allowed to write. A stale panel must not be able to
 *  overwrite the whole document and wipe the cycle cursor the controller advanced. */
const WRITABLE = ["mode", "selected", "intervalMs", "hidden", "cycle", "cursor", "lastRotate"];

function safePath(urlPath) {
  const clean = normalize(decodeURIComponent(urlPath.split("?")[0])).replace(/^(\.\.[/\\])+/, "");
  const full = resolve(join(ROOT, clean));
  // Path traversal guard: the resolved path must still sit under ROOT.
  return full === ROOT || full.startsWith(ROOT + sep) ? full : null;
}

function patchState(raw, respond) {
  let patch;
  try { patch = JSON.parse(raw); } catch { respond(400); return; }
  const file = join(ROOT, "state.json");
  let current = {};
  try { current = JSON.parse(readFileSync(file, "utf8")); } catch { /* first write */ }
  for (const key of WRITABLE) if (key in patch) current[key] = patch[key];
  current.updated = Date.now();
  mkdirSync(ROOT, { recursive: true });
  // Write to a sidecar and rename: two other processes poll this file, and half
  // a JSON makes them fall back to defaults — which looks like the backdrop
  // randomly jumping back to the first character.
  writeFileSync(file + ".tmp", JSON.stringify(current, null, 1));
  renameSync(file + ".tmp", file);
  respond(204);
}

function start(ctx) {
  const server = createServer((request, response) => {
    const respond = (code, headers) => {
      response.writeHead(code, { "Access-Control-Allow-Origin": "*", ...headers });
      response.end();
    };
    if (request.method === "OPTIONS") {
      respond(204, { "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
                     "Access-Control-Allow-Headers": "*" });
      return;
    }
    if (request.method === "POST" && request.url.startsWith("/__state")) {
      let raw = "";
      request.on("data", (chunk) => { raw += chunk; if (raw.length > 1e6) request.destroy(); });
      request.on("end", () => patchState(raw, respond));
      return;
    }
    if (request.method !== "GET" && request.method !== "HEAD") { respond(405); return; }

    const file = safePath(request.url);
    if (!file || !existsSync(file) || statSync(file).isDirectory()) { respond(404); return; }
    response.writeHead(200, {
      "Content-Type": TYPES[extname(file).toLowerCase()] || "application/octet-stream",
      "Content-Length": statSync(file).size,
      "Access-Control-Allow-Origin": "*",
      // The artwork never changes under a given path; re-fetching a 7MB master
      // on every backdrop swap would make switching feel broken.
      "Cache-Control": "public, max-age=86400",
    });
    if (request.method === "HEAD") { response.end(); return; }
    createReadStream(file).pipe(response);
  });

  server.on("error", (error) => {
    // EADDRINUSE means someone already serves this — the standalone script, or a
    // second DSH. That is fine: the browser half only needs SOMETHING on the port.
    const note = error.code === "EADDRINUSE"
      ? `端口 ${PORT} 已被占用，沿用已有的素材服务`
      : `素材服务启动失败：${error.message}`;
    ctx.logger?.("harness-ui")?.info?.(note);
  });

  server.listen(PORT, "127.0.0.1", () => {
    ctx.logger?.("harness-ui")?.info?.(`素材服务 127.0.0.1:${PORT} → ${ROOT}`);
  });
  return () => { try { server.close(); } catch { /* already down */ } };
}

function apply(ctx) {
  if (!existsSync(ROOT)) {
    ctx.logger?.("harness-ui")?.info?.(`素材目录不存在：${ROOT}`);
    return;
  }
  const stop = start(ctx);
  ctx.on?.("dispose", stop);
}

export { apply, inject, name };
