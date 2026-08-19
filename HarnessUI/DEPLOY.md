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
