/** 共享状态：菜单栏写，DSH 插件与 Kimi 外壳读。
 *
 *  两个宿主的皮肤机制完全不同 —— DSH 只能给插件一个 client.js、素材要走 http；
 *  Kimi 有自定义协议和主进程菜单。硬把它们统一成一套 API 只会两头别扭。
 *  它们唯一需要共识的其实只有一句话：现在该显示哪个角色。所以共识就放在这一个
 *  文件里，两边各用自己顺手的方式去读（Kimi 用 fs.watch，DSH 插件用轮询 http）。
 */
const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.join(process.env.HOME, ".harness-ui");
const FILE = path.join(ROOT, "state.json");
// hidden 是「不想看到的」而不是「删掉的」：轮播跳过、画廊默认不显示，但文件还在，
// 想要回来只要从列表里去掉。真要删文件是另一个动作，不该藏在一次误点里。
const DEFAULTS = { mode: "gallery", selected: null, cycle: [], cursor: 0,
                   lastRotate: 0, intervalMs: 4 * 3600 * 1000, hidden: [], updated: 0 };

function read() {
  try { return { ...DEFAULTS, ...JSON.parse(fs.readFileSync(FILE, "utf8")) }; }
  catch { return { ...DEFAULTS }; }
}

function write(next) {
  next.updated = Date.now();
  fs.mkdirSync(ROOT, { recursive: true });
  // 先写临时文件再改名：读方随时可能在读，半个 JSON 会让它们退回默认值，
  // 表现就是背景莫名其妙跳回第一张。
  const tmp = FILE + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(next, null, 1));
  fs.renameSync(tmp, FILE);
  return next;
}

function catalog() {
  try { return JSON.parse(fs.readFileSync(path.join(ROOT, "catalog.json"), "utf8")).entries; }
  catch { return []; }
}

/** 洗一副新牌。走完整副才重洗，"一轮覆盖全库不重复"才成立。 */
function newCycle(entries) {
  const ids = entries.map(e => e.id);
  for (let i = ids.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [ids[i], ids[j]] = [ids[j], ids[i]];
  }
  return ids;
}

module.exports = { ROOT, FILE, read, write, catalog, newCycle };
