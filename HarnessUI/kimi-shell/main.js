// Kimi Code GUI 外壳：启动本地 kimi 服务 + 加载 web UI + 注入皮肤
// 设计约束：皮肤只用「全局 CSS 变量 + 固定定位伪元素」，绝不依赖 kimi 内部压缩类名，
// 这样 kimi 升级后皮肤最多颜色对不齐，不会整个错位。
const { app, BrowserWindow, Menu, protocol, net, shell, ipcMain } = require("electron");
const { spawn, execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const net_ = require("node:net");

const HOME = process.env.HOME;
const KIMI = path.join(HOME, ".kimi-code");
const SHELL_DIR = path.join(KIMI, "shell");
const SKINS_DIR = path.join(SHELL_DIR, "skins");
const STATE = path.join(SHELL_DIR, "state.json");
const PORT = Number(process.env.KIMI_PORT || 58627);

let serverProc = null;   // 只有我们自己拉起的服务才由我们关闭
let win = null;
let galleryWin = null;

function openGallery() {
  if (galleryWin && !galleryWin.isDestroyed()) { galleryWin.focus(); return; }
  galleryWin = new BrowserWindow({ width: 1080, height: 760, title: "皮肤中心",
    webPreferences: { preload: path.join(SHELL_DIR, "preload.js"), contextIsolation: true } });
  galleryWin.loadFile(path.join(SHELL_DIR, "gallery.html"));
  galleryWin.on("closed", () => { galleryWin = null; });
}

const HARNESS = "harness-ui";
const HARNESS_DIR = () => path.join(SKINS_DIR, HARNESS);

/** 目录一次读入内存。304 条、约 100KB，比每次切换都读盘划算。 */
let harnessCatalog = null;
function catalog() {
  if (harnessCatalog) return harnessCatalog;
  try {
    const raw = JSON.parse(fs.readFileSync(path.join(HARNESS_DIR(), "assets/catalog.json"), "utf8"));
    // 目录里的 URL 是给 DSH 的 http 服务写的；这边走自定义协议，换掉前缀即可，
    // 不必为两个宿主各生成一份目录。
    harnessCatalog = raw.entries.map(e => ({
      id: e.id, game: e.game, gameName: e.gameName, character: e.character, variant: e.variant,
      light: `kimiskin://${HARNESS}/display/${e.id}/light.webp`,
      dark:  `kimiskin://${HARNESS}/display/${e.id}/dark.webp`,
      thumb: `kimiskin://${HARNESS}/thumb/${e.id}/light.webp`,
    }));
  } catch { harnessCatalog = []; }
  return harnessCatalog;
}

// HarnessUI 的状态住在 ~/.harness-ui/state.json，不在这个外壳自己的 state.json 里。
// 因为同一套素材有三个控制入口：菜单栏控制器、这里的菜单、DSH 的插件面板。
// 各存各的必然分叉——菜单栏切到 A、Kimi 菜单还勾着 B，用户看到的和菜单说的对不上。
// 一份状态，三处读写，没有"同步"这回事可以出错。
const SHARED_DIR = path.join(HOME, ".harness-ui");
const SHARED = path.join(SHARED_DIR, "state.json");
const H_DEFAULTS = { mode: "gallery", selected: null, cycle: [], cursor: 0,
                     lastRotate: 0, intervalMs: 4*3600*1000 };
const hstate = () => { try { return { ...H_DEFAULTS, ...JSON.parse(fs.readFileSync(SHARED, "utf8")) }; }
                       catch { return { ...H_DEFAULTS }; } };
const saveH = (h) => {
  h.updated = Date.now();
  fs.mkdirSync(SHARED_DIR, { recursive: true });
  // 写临时文件再改名：另外两个进程随时可能在读，半个 JSON 会让它们退回默认值
  fs.writeFileSync(SHARED + ".tmp", JSON.stringify(h, null, 1));
  fs.renameSync(SHARED + ".tmp", SHARED);
};

/** 盯着共享状态。菜单栏控制器改了角色，这边要跟着换，而不是等下次开菜单。 */
let sharedWatcher = null;
let lastSeenUpdate = 0;
function watchShared() {
  if (sharedWatcher) return;
  try { fs.mkdirSync(SHARED_DIR, { recursive: true }); } catch {}
  try {
    sharedWatcher = fs.watch(SHARED_DIR, (_ev, file) => {
      if (file !== "state.json") return;
      const h = hstate();
      if (!h.updated || h.updated === lastSeenUpdate) return;
      lastSeenUpdate = h.updated;
      if (readState().skin !== HARNESS) return;
      applyHarness(h.selected).then(() => buildMenu());
    });
  } catch (error) { console.log(`[kimi-shell] 共享状态监听失败: ${error.message}`); }
}

/** 一个不重复的完整周期。走完才重洗，这样「一轮覆盖全库」是真的。 */
function newCycle() {
  const ids = catalog().map(e => e.id);
  for (let i = ids.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [ids[i], ids[j]] = [ids[j], ids[i]]; }
  return ids;
}

/** 只改两个 CSS 变量，不重注整段样式 —— 切换才不会闪。 */
async function applyHarness(id) {
  if (!win || win.isDestroyed()) return null;
  const entry = catalog().find(e => e.id === id) || catalog()[0];
  if (!entry) return null;
  await win.webContents.executeJavaScript(
    `document.documentElement.style.setProperty("--hu-scene", 'url("${entry.light}")');` +
    `document.documentElement.style.setProperty("--hu-scene-dark", 'url("${entry.dark}")');true`);
  console.log(`[kimi-shell] HarnessUI -> ${entry.id}`);
  return entry;
}

async function rotateHarness(force) {
  const h = hstate();
  const now = Date.now();
  if (!force && now - (h.lastRotate || 0) < (h.intervalMs || 4*3600*1000)) return;
  if (!h.cycle?.length || h.cursor >= h.cycle.length) { h.cycle = newCycle(); h.cursor = 0; }
  const id = h.cycle[h.cursor];
  h.cursor += 1;
  const entry = await applyHarness(id);
  if (entry) { h.selected = entry.id; h.lastRotate = now; saveH(h); buildMenu(); }
}

let rotateTimer = null;
function scheduleHarness() {
  if (rotateTimer) clearInterval(rotateTimer);
  if (readState().skin !== HARNESS || hstate().mode !== "rotate") return;
  // 每分钟查一次而不是设一个四小时的 timeout：睡眠唤醒后 timeout 不一定还在，
  // 而错过的那一格下一分钟就会被补上。
  rotateTimer = setInterval(() => rotateHarness(false), 60 * 1000);
}

let harnessWin = null;
function openHarnessGallery() {
  if (harnessWin && !harnessWin.isDestroyed()) { harnessWin.focus(); return; }
  harnessWin = new BrowserWindow({ width: 1180, height: 800, title: "HarnessUI 角色库",
    webPreferences: { preload: path.join(SHELL_DIR, "preload.js"), contextIsolation: true } });
  harnessWin.loadFile(path.join(SHELL_DIR, "harness-gallery.html"));
  harnessWin.on("closed", () => { harnessWin = null; });
}

const readState = () => { try { return JSON.parse(fs.readFileSync(STATE, "utf8")); } catch { return { skin: "deep-whale" }; } };
const writeState = (s) => fs.writeFileSync(STATE, JSON.stringify(s, null, 2));
const listSkins = () => { try {
  return fs.readdirSync(SKINS_DIR).filter(d => fs.existsSync(path.join(SKINS_DIR, d, "skin.css")))
    .map(id => { let meta = {}; try { meta = JSON.parse(fs.readFileSync(path.join(SKINS_DIR, id, "skin.json"), "utf8")); } catch {}
      const thumb = ["thumb.png", "preview-dark.png", "preview-light.png", "preview.png"]
        .find(f => fs.existsSync(path.join(SKINS_DIR, id, f)));
      return { id, name: meta.name || id, tagline: meta.tagline || "", tags: meta.tags || [],
               author: meta.author || "", accent: meta.accent || "",
               preview: thumb ? `kimiskin://${id}/${thumb}` : null };
    }).sort((a, b) => a.name.localeCompare(b.name, "zh"));
} catch { return []; } };

async function createWindow() {
  win = new BrowserWindow({ width: 1440, height: 920, title: "Kimi Code",
    backgroundColor: "#0d1b2a", webPreferences: { contextIsolation: true } });
  buildMenu();
  win.webContents.on("did-finish-load", () => applySkin(readState().skin));
  win.on("closed", () => { win = null; });
  await win.loadURL(`http://127.0.0.1:${PORT}/#token=${token()}`);
  return win;
}

const portOpen = (port) => new Promise(res => {
  const s = net_.connect({ port, host: "127.0.0.1" });
  s.on("connect", () => { s.destroy(); res(true); });
  s.on("error", () => res(false));
  setTimeout(() => { s.destroy(); res(false); }, 1500);
});

async function ensureServer() {
  if (await portOpen(PORT)) return "已在运行";               // 复用他自己开的服务，不重复拉起
  serverProc = spawn(path.join(KIMI, "bin/kimi"), ["web", "--no-open", "--port", String(PORT)],
    { stdio: "ignore", detached: false });
  for (let i = 0; i < 40; i++) { if (await portOpen(PORT)) return "已启动"; await new Promise(r => setTimeout(r, 500)); }
  throw new Error("kimi web 起不来（等了 20 秒）");
}

const token = () => { try { return fs.readFileSync(path.join(KIMI, "server.token"), "utf8").trim(); } catch { return ""; } };

/** 串行化 applySkin。
 *  原来两处会并发调它：did-finish-load 的自动套用，和菜单/IPC 的手动切换。
 *  两边各自读写 wc.__skinKey，谁先读到旧 key、谁后写入新 key 是不确定的 ——
 *  实测结果是上一套皮肤的 CSS 永久留在页面里：亮色拿到了新配色却还铺着旧背景，
 *  暗色拿到了新背景却还用着旧配色。排队执行就没有这个缝。 */
let skinQueue = Promise.resolve();
function applySkin(id) {
  skinQueue = skinQueue.then(() => applySkinNow(id)).catch(e => {
    console.log(`[kimi-shell] 皮肤切换失败: ${e.message}`);
  });
  return skinQueue;
}

async function applySkinNow(id) {
  if (!win || win.isDestroyed()) return;
  const wc = win.webContents;
  if (wc.__skinKey) { try { await wc.removeInsertedCSS(wc.__skinKey); } catch {} wc.__skinKey = null; }
  if (!id || id === "none") return;
  const file = path.join(SKINS_DIR, id, "skin.css");
  if (!fs.existsSync(file)) return;
  const css = fs.readFileSync(file, "utf8").replaceAll("__SKIN__", `kimiskin://${id}`);
  wc.__skinKey = await wc.insertCSS(css);
  if (id === HARNESS) {
    const h = hstate();
    if (h.mode === "rotate") await rotateHarness(true);
    else await applyHarness(h.selected);
    scheduleHarness();
  }
  // 自检：读回真实生效值，打进日志（不然没人知道皮肤到底挂上没有）
  try {
    const probe = await wc.executeJavaScript(`(() => {
      const cs = getComputedStyle(document.documentElement);
      const app = document.getElementById("app");
      return JSON.stringify({ accent: cs.getPropertyValue("--color-accent").trim(),
        bgLayers: app ? (getComputedStyle(app).backgroundImage.match(/url\\(/g) || []).length : 0 });
    })()`);
    console.log(`[kimi-shell] 皮肤 ${id} 已注入 -> ${probe}`);
  } catch (e) { console.log(`[kimi-shell] 皮肤自检失败: ${e.message}`); }
}

/** HarnessUI 的子菜单。皮肤没装时给一行说明，而不是一个空菜单。 */
function harnessMenu() {
  const list = catalog();
  if (!list.length) return [{ label: "未找到角色库（skins/harness-ui/assets/catalog.json）", enabled: false }];
  const h = hstate();
  const cur = list.find(e => e.id === h.selected);
  const byGame = {};
  for (const e of list) (byGame[e.gameName] ||= []).push(e);
  return [
    { label: `当前：${cur ? cur.character + (cur.variant === "default" ? "" : " / " + cur.variant) : "未选择"}`, enabled: false },
    { label: `共 ${list.length} 个变体`, enabled: false },
    { type: "separator" },
    { label: "角色画廊（缩略图）…", accelerator: "CmdOrCtrl+Shift+K", click: () => openHarnessGallery() },
    { label: "换下一张", accelerator: "CmdOrCtrl+Shift+N", click: () => rotateHarness(true) },
    { type: "separator" },
    { label: "单一角色（手动）", type: "radio", checked: h.mode === "gallery",
      click: () => { const x = hstate(); x.mode = "gallery"; saveH(x); scheduleHarness(); buildMenu(); } },
    { label: "全库轮播（不重复）", type: "radio", checked: h.mode === "rotate",
      click: () => { const x = hstate(); x.mode = "rotate"; saveH(x); rotateHarness(true); scheduleHarness(); } },
    { label: "轮播间隔", submenu: [1, 4, 8].map(hr => ({
        label: `${hr} 小时`, type: "radio", checked: (h.intervalMs || 14400000) === hr * 3600000,
        click: () => { const x = hstate(); x.intervalMs = hr * 3600000; saveH(x); scheduleHarness(); buildMenu(); } })) },
    { type: "separator" },
    ...Object.entries(byGame).map(([game, entries]) => ({
      label: `${game}（${entries.length}）`,
      // 按角色分二级，否则 160 个变体拉成一条直的菜单没法用
      submenu: Object.entries(entries.reduce((acc, e) => ((acc[e.character] ||= []).push(e), acc), {}))
        .map(([character, vs]) => vs.length === 1
          ? { label: character, type: "radio", checked: h.selected === vs[0].id,
              click: () => pickHarness(vs[0].id) }
          : { label: character, submenu: vs.map(v => ({
              label: v.variant, type: "radio", checked: h.selected === v.id,
              click: () => pickHarness(v.id) })) }),
    })),
  ];
}

async function pickHarness(id) {
  const h = hstate();
  // 手动挑一张就意味着退出轮播，否则下一分钟的 tick 会把刚选的覆盖掉。
  h.mode = "gallery"; h.selected = id; saveH(h);
  const st = readState();
  if (st.skin !== HARNESS) { st.skin = HARNESS; writeState(st); await applySkin(HARNESS); }
  else await applyHarness(id);
  scheduleHarness(); buildMenu();
}

function buildMenu() {
  const cur = readState().skin;
  const skins = listSkins();
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    { role: "appMenu" },
    { label: "皮肤", submenu: [
      ...skins.map(s => ({ label: s.name, type: "radio", checked: cur === s.id,
        click: () => { const st = readState(); st.skin = s.id; writeState(st); applySkin(s.id); } })),
      { type: "separator" },
      { label: "官方原样（关闭皮肤）", type: "radio", checked: cur === "none",
        click: () => { const st = readState(); st.skin = "none"; writeState(st); applySkin("none"); } },
      { type: "separator" },
      { label: "皮肤中心（缩略图挑选）…", accelerator: "CmdOrCtrl+K", click: () => openGallery() },
      { type: "separator" },
      { label: "HarnessUI 角色库", submenu: harnessMenu() },
      { label: "打开皮肤目录", click: () => shell.openPath(SKINS_DIR) },
      { label: "重新载入当前皮肤", accelerator: "CmdOrCtrl+Alt+R", click: () => applySkin(readState().skin) },
    ]},
    { label: "文件", submenu: [
      { label: "关闭窗口", accelerator: "CmdOrCtrl+W", role: "close" },
      { type: "separator" },
      { label: "退出 Kimi Code", accelerator: "CmdOrCtrl+Q", role: "quit" },
    ]},
    { role: "editMenu" },
    { label: "视图", submenu: [
      { label: "重新载入", accelerator: "CmdOrCtrl+R", role: "reload" },
      { label: "强制重新载入", accelerator: "CmdOrCtrl+Shift+R", role: "forceReload" },
      { role: "toggleDevTools" }, { type: "separator" },
      { role: "resetZoom" }, { role: "zoomIn" }, { role: "zoomOut" }, { type: "separator" },
      { role: "togglefullscreen" }] },
    { role: "windowMenu" },
  ]));
}

protocol.registerSchemesAsPrivileged([
  { scheme: "kimiskin", privileges: { standard: true, secure: true, supportFetchAPI: true, bypassCSP: true } },
]);

app.whenReady().then(async () => {
  protocol.handle("kimiskin", (req) => {                     // 皮肤图片走自定义协议，避免 file:// 被拦
    const u = new URL(req.url);
    const rel = decodeURIComponent(u.pathname).replace(/^\/+/, "");
    const cands = [path.join(SKINS_DIR, u.hostname, "assets", rel), path.join(SKINS_DIR, u.hostname, rel)];
    const p = cands.find(c => c.startsWith(SKINS_DIR) && fs.existsSync(c));
    if (!p) return new Response("not found", { status: 404 });
    return net.fetch("file://" + p);
  });

  ipcMain.handle("harness:list", () => catalog());
  ipcMain.handle("harness:state", () => hstate());
  ipcMain.handle("harness:pick", async (_e, id) => { await pickHarness(id); return true; });
  ipcMain.handle("harness:mode", async (_e, mode) => {
    const h = hstate(); h.mode = mode; saveH(h);
    if (mode === "rotate") await rotateHarness(true);
    scheduleHarness(); buildMenu(); return true;
  });
  ipcMain.handle("skins:list", () => listSkins());
  ipcMain.handle("skins:current", () => readState().skin);
  ipcMain.handle("skins:apply", async (_e, id) => {
    const st = readState(); st.skin = id; writeState(st); await applySkin(id); buildMenu(); return true;
  });

  watchShared();
  const how = await ensureServer();
  await createWindow();
  console.log(`[kimi-shell] 服务 ${how}，端口 ${PORT}`);
});

// macOS 约定：关窗 ≠ 退出。少了 activate 这一半，关掉窗口后进程还在但永远回不来 ——
// 实测就是这个症状：pgrep 找得到进程，open 叫不出窗口，dock 点了也没反应。
// 所以两件事要一起给：关窗时别退，activate 时把窗口找回来。
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", async () => {
  if (win && !win.isDestroyed()) { win.show(); win.focus(); return; }
  await createWindow();
});
app.on("before-quit", () => { if (serverProc) { try { serverProc.kill(); } catch {} } });
