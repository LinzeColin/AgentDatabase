/**
 * HarnessUI 菜单栏控制器
 *
 * 为什么是一个独立的小程序，而不是把菜单加进 DSH：
 * DSH 的菜单与托盘建在打包的 app.asar 主进程里，插件拿不到任何菜单 API
 * （实测：整个包里没有 setApplicationMenu，托盘菜单只有一个 Quit，也没有给插件
 * 注册菜单项的 IPC 通道）。要在 DSH 的菜单栏里加东西，只能改它的 app.asar ——
 * 而那是签名应用包，DSH 每次升级都会覆盖，改坏了它起不来。
 *
 * 所以控制器住在自己的菜单栏图标里，谁都不碰：它只写一个状态文件，
 * DSH 插件和 Kimi 外壳各自去读。两个宿主的皮肤机制天差地别，但它们需要
 * 达成一致的只有一句话——现在显示哪个角色。
 */
const { app, BrowserWindow, Menu, Tray, nativeImage, ipcMain, shell } = require("electron");
const path = require("node:path");
const fs = require("node:fs");
const store = require("./state");

let tray = null;
let gallery = null;
let timer = null;
let entries = [];

const byId = (id) => entries.find(e => e.id === id) || null;

function label(entry) {
  if (!entry) return "未选择";
  const name = entry.label || entry.character;
  return entry.variant === "default" ? name : `${name} · ${entry.variant}`;
}

/** 推进一格。force 忽略间隔，用于「换下一张」和刚切进轮播时。 */
function rotate(force) {
  const s = store.read();
  const now = Date.now();
  if (!force && now - (s.lastRotate || 0) < s.intervalMs) return;
  if (!entries.length) return;
  if (!s.cycle.length || s.cursor >= s.cycle.length) { s.cycle = store.newCycle(entries); s.cursor = 0; }
  let entry = null;
  // 跳过素材里已经不存在的 id —— 素材库增删过之后旧周期里会留下空号
  while (s.cursor < s.cycle.length && !entry) { entry = byId(s.cycle[s.cursor]); s.cursor += 1; }
  if (!entry) return;
  s.selected = entry.id;
  s.lastRotate = now;
  store.write(s);
  refresh();
}

function pick(id) {
  const s = store.read();
  // 手动挑一张就退出轮播，否则下一次 tick 会把刚选的覆盖掉
  s.mode = "gallery";
  s.selected = id;
  store.write(s);
  refresh();
}

function setMode(mode) {
  const s = store.read();
  s.mode = mode;
  store.write(s);
  schedule();
  if (mode === "rotate") rotate(true); else refresh();
}

function setInterval_(ms) {
  const s = store.read();
  s.intervalMs = ms;
  store.write(s);
  schedule();
  refresh();
}

function schedule() {
  if (timer) clearInterval(timer);
  if (store.read().mode !== "rotate") return;
  // 每分钟查一次，而不是设一个四小时的 timeout：机器睡一觉之后 timeout 未必还在，
  // 而错过的那一格下一分钟就补上了。
  timer = setInterval(() => rotate(false), 60 * 1000);
}

function openGallery() {
  if (gallery && !gallery.isDestroyed()) { gallery.show(); gallery.focus(); return; }
  gallery = new BrowserWindow({
    width: 1180, height: 800, title: "HarnessUI 角色库", show: false,
    webPreferences: { preload: path.join(__dirname, "preload.js"), contextIsolation: true },
  });
  gallery.loadFile(path.join(__dirname, "gallery.html"));
  gallery.once("ready-to-show", () => gallery.show());
  gallery.on("closed", () => { gallery = null; });
}

function buildMenu() {
  const s = store.read();
  const cur = byId(s.selected);
  const games = {};
  for (const e of entries) (games[e.gameName] ||= []).push(e);

  const template = [
    { label: `当前：${label(cur)}`, enabled: false },
    { label: `素材库 ${entries.length} 个变体`, enabled: false },
    { type: "separator" },
    { label: "角色画廊（缩略图）…", accelerator: "Cmd+Shift+K", click: openGallery },
    { label: "换下一张", accelerator: "Cmd+Shift+N", click: () => rotate(true) },
    { type: "separator" },
    { label: "单一角色", type: "radio", checked: s.mode !== "rotate", click: () => setMode("gallery") },
    { label: "全库轮播（一轮不重复）", type: "radio", checked: s.mode === "rotate", click: () => setMode("rotate") },
    { label: "轮播间隔", submenu: [1, 4, 8, 24].map(hr => ({
        label: hr === 24 ? "24 小时" : `${hr} 小时`, type: "radio",
        checked: s.intervalMs === hr * 3600000, click: () => setInterval_(hr * 3600000) })) },
    { type: "separator" },
  ];

  for (const [game, list] of Object.entries(games)) {
    const chars = {};
    // 按中文名归组。没有中文名的（中文站还没建条目的新角色）回退到英文 id。
    for (const e of list) (chars[e.label || e.character] ||= []).push(e);
    template.push({
      label: `${game}（${list.length}）`,
      // 按角色再分一级：160 个变体拉成一条直的菜单没法用
      submenu: Object.entries(chars).map(([character, vs]) => vs.length === 1
        ? { label: character, type: "radio", checked: s.selected === vs[0].id, click: () => pick(vs[0].id) }
        : { label: character, submenu: vs.map(v => ({
            label: v.variant, type: "radio", checked: s.selected === v.id, click: () => pick(v.id) })) }),
    });
  }

  template.push(
    { type: "separator" },
    { label: "打开素材目录", click: () => shell.openPath(store.ROOT) },
    { label: "重新扫描素材库", click: () => {
        entries = store.catalog().map(e => ({ ...e,
          thumbFile: "file://" + path.join(store.ROOT, "thumb", e.id, "light.webp") }));
        refresh(); } },
    { type: "separator" },
    { label: "退出 HarnessUI 控制器", role: "quit" },
  );
  return Menu.buildFromTemplate(template);
}

function refresh() {
  if (tray) tray.setContextMenu(buildMenu());
  if (gallery && !gallery.isDestroyed()) gallery.webContents.send("harness:changed", store.read());
}

/** 菜单栏图标。用模板图，跟随亮/暗菜单栏自动反色。 */
function trayIcon() {
  const file = path.join(__dirname, "iconTemplate.png");
  if (fs.existsSync(file)) {
    const img = nativeImage.createFromPath(file);
    img.setTemplateImage(true);
    return img;
  }
  return nativeImage.createEmpty();
}

app.whenReady().then(() => {
  // 菜单栏程序不该占 Dock 图标，也不该抢焦点
  if (app.dock) app.dock.hide();
  entries = store.catalog().map(e => ({ ...e,
    thumbFile: "file://" + path.join(store.ROOT, "thumb", e.id, "light.webp") }));
  tray = new Tray(trayIcon());
  tray.setToolTip("HarnessUI 皮肤");
  // 图标之外再挂一个短标题：模板图在某些菜单栏配置下不显眼，文字保证找得到。
  tray.setTitle(" HU");
  refresh();
  schedule();
  if (store.read().mode === "rotate") rotate(false);

  ipcMain.handle("harness:list", () => entries);
  ipcMain.handle("harness:state", () => store.read());
  ipcMain.handle("harness:pick", (_e, id) => { pick(id); return store.read(); });
  ipcMain.handle("harness:mode", (_e, m) => { setMode(m); return store.read(); });
});

// 关掉画廊窗口不该退掉控制器 —— 它的本体是菜单栏图标，不是窗口
app.on("window-all-closed", () => {});
