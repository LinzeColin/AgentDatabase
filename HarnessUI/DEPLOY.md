# HarnessUI 部署现状

## 一个控制器，两个宿主

```
        ┌─────────────────────────────┐
        │  HarnessUI 皮肤.app          │  ← 菜单栏图标（无 Dock 图标）
        │  角色画廊 / 单一 / 轮播 / 间隔  │
        └──────────────┬──────────────┘
                       │ 写
              ~/.harness-ui/state.json      ← 唯一真源
                       │ 读
        ┌──────────────┴──────────────┐
        │                             │
   Kimi Code.app                  DSH Desktop
   fs.watch 立即跟随                插件每 15s 同步
```

**为什么共用一个状态文件**：三个入口（菜单栏、Kimi 自己的菜单、DSH 插件面板）
各存各的必然分叉 —— 菜单栏切到 A，Kimi 菜单还勾着 B，用户看到的和菜单说的对不上。
一份状态、三处读写，就没有"同步"这回事可以出错。

## 已就位

| 东西 | 位置 | 状态 |
|---|---|---|
| 菜单栏控制器 | `~/Applications/HarnessUI 皮肤.app` | ✅ 已装，已跑通 |
| 共享素材库 | `~/.harness-ui/`（display 103MB + thumb 6.3MB + catalog + state） | ✅ |
| 资源服务 | `~/.harness-ui/asset_server.py` → `127.0.0.1:3099` | ✅ 已设开机自启 |
| Kimi 皮肤 | `~/.kimi-code/shell/skins/harness-ui/` | ✅ |
| Kimi 外壳 | `~/Applications/Kimi Code.app`（已重新打包） | ✅ 含 bug 修复 + HarnessUI 菜单 |
| DSH 插件 | `HarnessUI/dsh-plugin/` | ⏳ **未安装，装它要你手动重启 DSH** |
| 母版 | NAS `<游戏>/<角色>/skins/<变体>/` | ✅ 612 张 |

## Kimi 修的两个 bug（实测验证，不是看代码猜的）

**1. 关掉窗口后再也叫不回来。** 根因是 `main.js` **没有 `app.on("activate")`**。
macOS 上点 Dock 图标触发 `activate`，没有这个 handler 就永远不会重建窗口 ——
症状正是你说的「退后台」：`pgrep` 找得到进程，`open` 叫不出窗口。

```
[selftest] 关窗后 win = null（已释放）
[selftest] 进程还活着: true              ← 关窗不再退出，符合 macOS 约定
[selftest] activate 之后窗口回来了: true  ← 这是原来做不到的
```

**2. 快捷键。** 补了显式「文件」菜单（Cmd+W 关窗 / Cmd+Q 退出）和 Cmd+R 重新载入。
顺带解掉一个冲突：皮肤菜单原本占了 Cmd+Shift+R，与「强制重新载入」撞车，已挪到 Cmd+Alt+R。

```
[selftest] 快捷键: 关闭窗口=CmdOrCtrl+W | 退出 Kimi Code=CmdOrCtrl+Q | 重新载入=CmdOrCtrl+R
```

**3.（顺手修的）皮肤切换会漏样式。** 原代码里 `did-finish-load` 的自动套用和菜单点击
会并发调 `applySkin`，两边抢同一个 `wc.__skinKey`，结果上一套皮肤的 CSS 永久留在页面里
—— 实测表现为「亮色拿到新配色却还铺着旧背景，暗色拿到新背景却还用着旧配色」。已改成排队执行。

## 为什么 DSH 不能像 Kimi 那样进菜单栏

实测：DSH 的菜单与托盘建在打包的 `app.asar` 主进程里，**整个包里没有 `setApplicationMenu`，
托盘菜单只有一个 Quit，也没有任何给插件注册菜单项的 IPC 通道**。插件的 `client.js` 跑在
渲染进程，碰不到 macOS 菜单栏。要在 DSH 菜单栏里加东西只能改它的 `app.asar` —— 那是签名
应用包，DSH 每次升级都会覆盖，改坏了它起不来。所以控制器做成独立菜单栏程序，谁都不碰。

## 还差一步：装 DSH 插件

```bash
cp -R ~/Documents/Codex/GithubProject/_scratch/agentdatabase-harness-ui/HarnessUI/dsh-plugin \
      ~/.dsh/plugins/dsh-harness-ui-skins
```
然后**你手动完全退出 DSH Desktop 再打开**（桌面壳没有热重载，这是唯一办法）。
我不会自己动手重启。

---

## 装 DSH 插件踩的坑（下次直接照做）

插件光放进 `~/.dsh/plugins/` **不会被加载**。要三处齐全，缺一不可：

1. `~/.dsh/profiles/desktop/node_modules/<包名>` → 软链到插件目录
2. `~/.dsh/profiles/desktop/package.json` 的 `dependencies` 加 `"<包名>": "link:<绝对路径>"`
3. **同一个 package.json 的 `dsh.profile.bundles` 数组里加 `<包名>`** ← 最容易漏的一条

另外 `package.json` 必须有 `"type": "module"`、`exports` 里给出 `./client`，
以及 `dsh.bundle.patch` / `dsh.client` 两块 —— 我一开始自己编了个 `cordis` 字段，
loader 根本不看，插件目录放对了也是白搭。

还有一条：**鲸鱼娘皮肤是通过它自己插件目录里的 `insert` 挂载的**，
`~/.dsh/cordis.patch.yml` 那段互斥列表里写的 `ui-skin-maid-atelier` 拦不住它。
要停它得按它实际插入的 id `ui-skin-deep-whale-day-night` 加一行 disabled，
否则两套皮肤同时挂载互相盖。

---

## 素材放哪（2026-08-20 修正的一个真实隐患）

母版一度只存在于会话的 scratchpad（`/private/tmp/...`）里，而 `~/.harness-ui/`
下的 `genshin` / `hsr` / `zzz` 三个软链就指向那里。**/tmp 一被清，4.8GB 母版和
验收页的全部大图链接一起没**。用户点出来之后已改：

```
~/.harness-ui/
  master/<game>/<char>/<variant>/{light,dark}.png   4.8GB  ← 皮肤实际铺的图
  thumb/ <game>/<char>/<variant>/light.webp         5MB    ← 画廊网格
  catalog.json · names_zh.json · state.json · review.html
  asset_server.py                                          ← launchd 起它，读不了 ~/Documents
```

`/tmp` 下现在一张母版都没有。NAS 上另有一份（`<游戏>/<角色>/skins/<变体>/`，612 张已核对）。

## 皮肤铺的是母版 PNG，不是 WebP

一度为了「切换快」把 3840 的母版压成 380KB 的 WebP q88。动漫线稿最吃这一刀，
用户给的评价是 70 分。实测 kimiskin:// 协议吐一张 7MB 母版只要 **33ms**，
所谓的体积优化从一开始就没必要 —— 这批图是花钱产出的，为省几百 KB 削它的画质是错的取舍。

模糊问题一共三个来源，按影响从大到小：

1. **`.app { backdrop-filter: blur(2px) }`** —— backdrop-filter 糊的是元素**背后的一切**，
   而 `.app` 铺满整窗，等于把整张立绘糊掉。用户原话「人物模型在文本的后面，不清楚很模糊」，
   单独看图 100%、DSH 95%、这里只剩 10%。DSH 插件里没有这一行，所以 DSH 一直是清楚的。
2. **`background-attachment: fixed`** —— 把背景推进独立合成层，Chromium 常按 1x 光栅化
   再放大到 DPR 2，Retina 上表现为「能看清但不够锐」。`#app` 本来就铺满整窗，fixed 毫无用处。
3. **WebP 重编码** —— 已改回母版 PNG。

---

## 背板显示不出来 / 发灰的真因（2026-08-20 定位，两个宿主同一个根因）

**不是分辨率、不是模糊滤镜，是别的层的底色压在背板上。**

判据（对 DSH 做的决定性实验）：把页面里所有元素的 `background-color` 和
`background-image` 临时清空、只留 `#root` 的背板 —— 立绘立刻完整、锐利地显示出来。
说明背板一直是好的，问题百分之百在遮挡。

- **DSH**：`DIV.pI_x6G_frame` 是一层铺满窗口的**纯白不透明**层，把背板整个盖死。
  表现是「界面一片空白 + 皮肤按钮还在」。
- **Kimi**：没有全遮，但 `--color-surface` / `--panel` 这类**半透明浅色**大面积叠在
  立绘上，表现是「能看见但发灰发糊」。

**都不能靠类名解决** —— `pI_x6G_frame` 是编译哈希，DSH 每次构建都会变。
统一做法：**清空全部后代底色，再只给真正承载文字的控件（input / textarea /
[role=dialog] / [role=menu] / [role=listbox]）加回半透明底**。一个类名都不依赖。

顺带排掉的两条（它们确实各占一部分，但都不是主因）：
`backdrop-filter: blur(2px)` 糊的是元素背后的一切（10 分那一版）；
`background-attachment: fixed` 让 Chromium 按 1x 光栅化再放大（70 分那一版）。

---

## 解剖缺陷筛查：自动判官三轮都没成，别再试第四轮

用户点出 `zzz/lucia/whispering-dreams` 有三只手（握杖那条手臂从腰侧长出来，没有肩）。
机器闸门查不了这一类——`runner.py` 只判比例、宽度、亮度、主体溢出。
于是用视觉模型做判官，三轮全失败：

| 版本 | 做法 | 对那张已知坏图 | 结果 |
|---|---|---|---|
| 1 | gpt-5-mini +「拿不准就不报」 | 漏掉 | 废 |
| 2 | gpt-5 + 强制计数 + 上半身特写 + 禁止用遮挡开脱 | 抓到，判词准确 | **100 张里报了 83 张**，没有区分力 |
| 3 | 改问「普通人第一眼会不会注意到」0-10 分 | 又漏掉（3 分放行） | 废 |

第 2 版的判词是对的——它说某张图「手臂追不到肩」，我自己核过，确实被头发挡住追不到。
但那不是用户要的：普通人看只会觉得手臂被挡住了，而 lucia 那条凭空多出的手臂一眼出戏。
**问题是问错了问题**（"能不能找出毛病"答案永远是能）；而问对之后它又复现不了用户的阈值。

**结论：这类判定只能人来。** 机器该做的是把它变便宜：
`build_qa_crops.py` 把人物从 16:9 里裁出来放大（人物只占左 35%，整图缩略里手指级别的
缺陷根本看不见，裁出来后同样尺寸给到三倍人物像素），`build_qa_page.py` 排成密网格、
点一下标记、导出 `<id>|<side>` 清单，`regen.py` 吃那份清单定点重出。
判官的分数只用来排序，不当判决。

`regen.py` 重出时会把上一版错在哪写进 prompt，并保留旧图为 `<side>.rejected-N.png`——
新的不一定更好，得留退路。
