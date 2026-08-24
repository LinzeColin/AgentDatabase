# 宿主接入：DSH 与 Kimi Code

**先查这个宿主怎么给插件送素材，别假设。**

| | 机制 | 自足? |
|---|---|---|
| **Kimi Code** | 注册 `kimiskin://` 自定义协议，直接读盘 | ✅ |
| **DSH** | 每个插件**只服务 `client.js`**，其余路径全 404；渲染进程拒绝 `file://` | ❌ 需 http |

验证：挂载中的插件，`/plugins/<pkg>/client.js` 返 200，
而 `preview/light.webp`、`package.json` 和该目录下任何其他路径**全返 404**。

## DSH

### 装：三处登记，缺一不可

1. `~/.dsh/profiles/desktop/node_modules/<包名>` → 软链到插件目录
2. 同目录 `package.json` 的 `dependencies` 加 `"<包名>": "link:<绝对路径>"`
3. **同一个 package.json 的 `dsh.profile.bundles` 数组里加 `<包名>`** ← 最容易漏

插件自己的 `package.json` 必须有：
```json
{"type":"module", "main":"lib/index.js",
 "exports":{".":"./lib/index.js","./client":"./lib/client.js"},
 "dsh":{"bundle":{"patch":"./cordis.patch.yml"},
        "client":{"inject":[],"platform":"web","immediately":true}}}
```
我一开始自己编了个 `cordis` 字段——loader 根本不看，白重启三次。

`cordis.patch.yml`：
```yaml
- insert:
    - id: ui-skin-<name>
      name: <包名>
```

**判断挂上没有**：
```bash
curl -s "http://127.0.0.1:3080/?dsh-desktop-mode=compatibility&dsh-desktop-platform=darwin" \
 | grep -o 'window.__DSH_BOOT__ = {.*}' | python3 -c "…"   # 看 entries 里包名在不在
```
**别靠界面猜。** 装完必须**完全退出 DSH 再打开**（桌面壳没有热重载）。

### 互斥的坑

皮肤中心是互斥的：`dsh-skin use X` 会把 `~/.dsh/cordis.patch.yml` 的 managed 段里
其余每一行写成 `disabled: true`。

**但通过插件目录里自己的 `insert` 挂载的皮肤绕过这个列表**——
鲸鱼娘皮肤的 managed 行是 `ui-skin-maid-atelier`，而它实际插入的 id 是
`ui-skin-deep-whale-day-night`，那行 disabled 拦不住它。要停它得按**实际插入的 id** 加一行。
不停就是两套皮肤同时挂载互相盖。

### 素材服务要住在插件里

DSH 的浏览器半边只能走 http 拿素材，所以需要一个服务。
**不要做成外部进程或 LaunchAgent**——用户一关它，皮肤就悄悄没了背景
（面板还在、缩略图还在，只是画面空白，看起来像坏了）。

把 http 服务放进插件的**宿主半边**（`lib/index.js`，跑在 Node）：
DSH 起它就起、DSH 退它就退，**装插件 = 全部安装**。
端口被占时沿用已有的，别报错退出。

服务要提供：静态文件（含路径穿越防护）、CORS 头、以及**状态写回端点**（见 08）。

## Kimi Code

外壳源码在 `~/.kimi-code/shell/`（和 app.asar 里的内容逐字节一致），
改完用 `@electron/asar pack` 重新打包进 `~/Applications/Kimi Code.app`。

皮肤放 `~/.kimi-code/shell/skins/<id>/`：`skin.css` + `skin.json` + `thumb.png` + `assets/`。
`skin.css` 里的 `__SKIN__` 会被替换成 `kimiskin://<id>`。

**CSS 特异性**：kimi 自己的规则用 `html[data-color-scheme="…"]`，
只写裸 `:root` 会被压过去。要写成
`:root, html[data-color-scheme="light"], html[data-color-scheme="system"]`，
暗色同理。

**串行化 `applySkin`**：`did-finish-load` 的自动套用和菜单点击会并发调它，
两边抢同一个 `wc.__skinKey`，结果上一套皮肤的 CSS 永久留在页面里
（表现为「亮色新配色配旧背景、暗色新背景配旧配色」）。用 promise 队列排队执行。

## macOS 打包

手工复制 `Electron.app` 再 `codesign --force --deep --sign -`，
在 Apple Silicon 上**启动即被系统杀掉**（无崩溃日志，静默退出）。
用 `@electron/packager` 正规打包。

菜单栏程序：`LSUIElement: true`（不进 Dock、不进 Cmd-Tab）+ `app.dock.hide()`。
