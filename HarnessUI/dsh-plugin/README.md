# HarnessUI 皮肤 — DSH 插件

一个插件，两种模式。**不是两个插件** —— 皮肤中心是互斥的（`dsh-skin use X` 会把注册表里
其余每一行写成 `disabled: true`），做成两个会互相关掉。

| 模式 | 行为 |
|---|---|
| **画廊**（方案 1） | 缩略图网格，按游戏筛选 / 搜角色，点一下即时换背景，选择会记住 |
| **轮播**（方案 2） | 每 4 小时换一张（可调 1/4/8 小时），**一个周期覆盖全库且不重复**，走完才重新洗牌 |

昼夜跟随宿主主题：`data-ds-dark-theme` 在就用 `dark.webp`，不在就用 `light.webp`。

## 素材为什么走本地服务，而不是像别的皮肤那样内嵌

这一版 DSH 对每个插件**只服务 `client.js` 一个文件**。实测：挂载中的皮肤，
`client.js` 返 200，而 `preview/light.webp`、`package.json` 和该目录下任何其他路径全返 404。
渲染进程还会拒绝 `file://`（`<img>` 指过去直接 `error`），但 `http://127.0.0.1` 正常。

参照皮肤（鲸鱼娘昼夜工坊）的做法是把素材全部内嵌成 data URI —— 它 2 张图就占 1.7MB，
这套 612 张会变成好几个 GB 的 bundle，装不了也跑不动。

所以：素材由 `tools/asset_server.py` 在 `127.0.0.1:3099` 提供，皮肤 fetch 目录、按 URL 挂背景。
**该服务必须带 CORS 头** —— 页面在 `:3080`，跨端口 `fetch` 会被拦；图片能显示而目录拉不到，
就是这个原因（已在 `asset_server.py` 里解决，别用 `python3 -m http.server` 顶替）。

## 性能约束（来自 `~/.dsh/AGENTS.md` 的事故记录）

**这个皮肤里没有任何 `infinite` CSS 动画，也不要加。** 一个常驻关键帧动画铺满整窗，
曾让 DSH 空闲时占 111% CPU，去掉后 2.5%。只用一次性 transition —— 它会结束。

## 安装

**素材服务住在插件里**，不再需要单独起进程或配开机自启。DSH 一启动，
插件的宿主半边就在 `127.0.0.1:3099` 上把 `~/.harness-ui` 服务起来，
DSH 退出它就跟着退。装插件就是全部安装。

（为什么需要这个服务：这一版 DSH 每个插件只服务 `client.js` 一个文件，
其余路径全 404，渲染进程又拒绝 `file://`。Kimi 那边有 `kimiskin://` 协议
可以直接读盘，DSH 没有对应机制，所以由插件自己起一个。端口被占时会沿用已有的，
不会报错。）

三处登记缺一不可，见下面「装 DSH 插件踩的坑」。装完**完全退出 DSH 再打开**
（桌面壳没有热重载）。

装完在右下角会出现「皮肤」按钮，点开就是画廊。

## 素材服务开机自启（可选）

```bash
cat > ~/Library/LaunchAgents/com.harnessui.assets.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.harnessui.assets</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string>
    <string>__TOOLS__/asset_server.py</string>
    <string>--root</string><string>__ROOT__</string>
    <string>--port</string><string>3099</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
PLIST
launchctl load ~/Library/LaunchAgents/com.harnessui.assets.plist
```

## 实测数据（2026-08-20，对着真实 DSH 界面在浏览器里跑的）

| 项 | 结果 |
|---|---|
| 挂载 / 作用域 | ✅ `body[data-dsh-harness-ui]` |
| 画廊渲染 | ✅ 253 张卡片（当时的目录规模），缩略图 lazy 加载，0 失败 |
| 轮播不重复 | ✅ 周期内全唯一，连抽 6 次零重复 |
| 昼夜跟随 | ✅ 暗→`dark.webp`，亮→`light.webp` |
| 切换耗时 | 681ms（图片本身冷加载仅 8ms，其余是 2560×1440 解码；420ms 淡入覆盖掉） |
| 单张显示图 | 149–162KB WebP（母版 6.6MB PNG，小 45 倍） |
| 缩略图 | 6.5KB |
