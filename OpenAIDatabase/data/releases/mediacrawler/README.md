# MediaCrawler hardened macOS backup

这是 `NanmiCoder/MediaCrawler` 的用户级、可复现、安全收紧版安装备份。它不是源码镜像，也不含任何抓取结果、Cookie、账号、登录态、浏览器资料或本机用户名。

## 当前安装基线

- 上游仓库：<https://github.com/NanmiCoder/MediaCrawler>
- 上游提交：`0625e01a6bc717a3fc9c96d3dac7fb8957043838`
- 许可证：`NON-COMMERCIAL LEARNING LICENSE 1.1`，仅限非商业学习和研究，禁止大规模抓取或干扰平台运行。
- 入口命令：`mediacrawler`
- 默认输出：本机私有 staging 目录中的 JSONL；不会自动上传 GitHub。
- 默认上限：每次最多 5 条、并发 1、评论关闭、媒体下载关闭、代理关闭。
- 登录：只允许二维码或手机号；安全启动器禁止 Cookie 参数。

## 支持范围

MediaCrawler 上游声明支持：小红书 `xhs`、抖音 `dy`、快手 `ks`、B站 `bili`、微博 `wb`、贴吧 `tieba`、知乎 `zhihu`。

X/Twitter、Reddit、Instagram 不在 MediaCrawler 的实现范围内。本次没有为这三个平台安装来源不明的额外采集器，也没有导入浏览器登录态。完整状态见 `platform_support.json`。

## 怎么用

先看帮助，不会启动浏览器：

```bash
mediacrawler --help
```

第一次建议只抓 1 条，并在专用 Chrome 窗口里扫码登录：

```bash
mediacrawler --platform xhs --type search --keywords "你的关键词" --crawler_max_notes_count 1
```

其他示例：

```bash
mediacrawler --platform bili --type search --keywords "你的关键词" --crawler_max_notes_count 5
mediacrawler --platform wb --type detail --specified_id "帖子 URL 或 ID"
mediacrawler --platform zhihu --type creator --creator_id "创作者 URL 或 ID"
```

抖音和知乎依赖 Node.js `>=16`；验收机器已检测到 Node.js `v24.18.0`。首次真正运行前仍需由用户自己扫码或完成平台验证；本次安装没有代替用户登录，也没有进行真实抓取。

安全启动器会拒绝：

- `--lt cookie` 和 `--cookies`
- `--init_db` 和任何数据库初始化
- 自定义 `--save_data_path`
- 非 JSONL 输出
- 开启或配置代理
- 开启一级或二级评论抓取
- 并发不等于 1
- 单次条数超过 50
- 未明确提供平台、任务类型或关键词/ID

## GitHub 数据边界

本次 GitHub 备份只有安装元数据、补丁、锁文件、启动器和验证结论。以后实际使用时：

1. 原始 JSONL、浏览器目录和登录态先留在本机私有 staging 目录。
2. 逐个平台确认条款、版权、隐私和公开发布边界。
3. 只把去敏、去重、可公开且能说明来源的 processed 数据提交到 `OpenAIDatabase/data/processed/mediacrawler/`。
4. Cookie、账号标识、私信、非公开内容、浏览器状态和本机路径永不进入公开仓库。

## 恢复安装

1. 把上游仓库克隆到 macOS 用户目录下的 `~/Library/Application Support/MediaCrawler/source`。
2. 检出上面的固定提交，并保持 detached HEAD。
3. 运行 `git apply --unidiff-zero safe_defaults.patch`。
4. 用本目录的 `uv.lock` 替换上游锁文件。
5. 在源码目录运行 `uv sync --frozen --no-install-project`。
6. 把 `launcher.py.txt` 复制为 `~/.local/bin/mediacrawler` 并赋予用户执行权限。
7. 运行 `mediacrawler --help`；启动器会校验提交、补丁文件哈希、Git 工作树和离线锁定环境。

完整上游源码不在此备份中，恢复时必须从官方仓库取得。`UPSTREAM_LICENSE.txt` 必须与任何恢复副本一起保留。
恢复前可用 `SHA256SUMS` 核对本目录中的八个备份文件；该清单不包含自身。

## 卸载范围

仅需删除用户级入口 `~/.local/bin/mediacrawler` 和用户级运行目录 `~/Library/Application Support/MediaCrawler/`。不要用 `sudo`，也不要删除浏览器或其他项目目录。
