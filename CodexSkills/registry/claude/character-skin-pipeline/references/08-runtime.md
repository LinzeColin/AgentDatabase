# 运行时：共享状态、消费方案、控制器

## 两个消费方案（用户要的）

**方案 1 · 画廊挑选**：缩略图网格、按游戏筛选、搜角色（中文/英文都能搜）、
点击即时换背景、选择要记住。

**方案 2 · 全库轮播**：每 N 小时换一张（1/4/8/24 可选），
**一个周期覆盖全库且不重复**，走完才重新洗牌。

**做成一个插件的两种模式，不是两个插件**——皮肤中心是互斥的，
两个插件会互相关掉。

不重复的实现：Fisher-Yates 洗一副牌存进状态，游标推进；
走完整副才重洗。**周期要持久化**，否则重启就从头开始、前几张必然重复。

```js
function newCycle(entries, hidden) {
  const skip = new Set(hidden || []);
  const ids = entries.filter(e => !skip.has(e.id)).map(e => e.id);
  for (let i = ids.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1)); [ids[i], ids[j]] = [ids[j], ids[i]];
  }
  return ids;
}
```

**用每分钟查一次代替设一个 N 小时的 timeout**——机器睡一觉之后 timeout 未必还在，
而错过的那一格下一分钟就补上了。

## 共享状态：一份，三处读写

三个入口（菜单栏控制器、Kimi 自己的菜单、DSH 的面板）各存各的**必然分叉**——
菜单栏切到 A 而 Kimi 菜单还勾着 B，用户看到的和菜单说的对不上。

```
~/.harness-ui/state.json
{"mode":"rotate|gallery", "selected":"<id>", "cycle":[…], "cursor":N,
 "lastRotate":ms, "intervalMs":ms, "hidden":[…], "updated":ms}
```

- **Kimi**：`fs.watch` 目录，`updated` 变了就跟着换
- **DSH 插件**：每 15 秒 GET `state.json`
- 写入一律**先写 `.tmp` 再 rename**——另外两个进程随时在读，
  半个 JSON 会让它们退回默认值，表现为背景莫名跳回第一张

### 浏览器里的面板写不了文件（真实 bug）

DSH 的面板住在渲染进程，只能写 localStorage。而状态每 15 秒从共享文件读回来覆盖——
**用户选的「1 小时轮播」15 秒内就被盖掉，面板看起来是控制器，实际是只读的。**

修法：给素材服务加 `POST /__state`，**只接受白名单里的键**
（`mode / selected / intervalMs / hidden / cycle / cursor / lastRotate`）——
一个陈旧的面板不该整份覆盖，会抹掉控制器刚推进的周期游标。
写回后要把自己的 `syncSeen` 时间戳前移，别让自己刚写的又被自己读回来当外部变更。

## 菜单栏控制器（DSH 做不到菜单栏时的解法）

**DSH 的菜单和托盘建在打包的 app.asar 里**，整个包没有 `setApplicationMenu`，
托盘只有一个 Quit，也没有给插件注册菜单项的 IPC 通道。
插件的 client.js 跑在渲染进程，碰不到 macOS 菜单栏。

三条路：
| 方案 | 代价 |
|---|---|
| A. 应用内浮层 | 无风险，但不是系统菜单栏 |
| B. 改 DSH 的 app.asar | 能做，但改签名应用包，每次升级被覆盖，改坏了起不来 |
| **C. 独立菜单栏小程序** | **同时控制多个宿主，完全不碰它们** |

**选 C。** 一个 `LSUIElement: true` 的 Electron 小程序，托盘菜单里放：
当前角色、素材总数、角色画廊、换下一张、单一/轮播、轮播间隔、
按游戏→角色的多级菜单（160 个变体拉成一条直的菜单没法用，必须分二级）、
添加素材、取消隐藏全部、打开素材目录、重新扫描。

## 增删

- **删 = 隐藏**（写进 `hidden` 数组），非破坏、可撤销；轮播跳过、画廊默认不显示
- **真删文件**是另一个动作，要弹确认框，且说明母版仍在 NAS 上可重新导入
- **增**：文件选择器 → 从文件名猜归属（`<game>-<char>-<variant>-<side>`）→
  转成库里统一的格式落盘 → 重扫。
  Electron 的 `nativeImage` **不会编 WebP**，缩放交给 Python。
- 隐藏某项后要**清空周期重洗**，否则下一格会跳到一张已经不该出现的图
