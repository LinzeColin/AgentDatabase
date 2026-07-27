---
name: weread-portable-notes
description: 通过全局中文的“微信读书笔记迁移”应用，使用腾讯官方微信读书 Agent Gateway 或浏览器本地文件，把用户本人有权使用的阅读笔记导出为四类 Markdown、规范化 JSON、离线搜索、可校验 ZIP 和可交给 ChatGPT 的中文阅读文件。不得索取、复制、持久化或回显真实用户密钥。
version: 0.0.0.1
---

# 微信读书个人笔记可移植导出

## 首选结果

生成用户主动下载的完整/部分迁移 ZIP；正常时另生成一个中文 ChatGPT 阅读笔记文件、中文提问词和固定官方入口。用户密钥、笔记、搜索词和导出物不得进入提示词、仓库、日志、统计或服务器持久化层。

## 首选路径

1. 使用已部署的“微信读书笔记迁移”ChatGPT Site；
2. 选择演示数据、在站点密码框输入本人微信读书 Key，或上传一个历史 ZIP/JSON、最多 50 个 Markdown/TXT；
3. 选择书籍、格式和可选统计；
4. 检查完整/部分/失败状态；
5. 主动下载迁移 ZIP；需要继续询问时，再主动下载 ChatGPT Markdown、复制提问词并打开 `https://chatgpt.com/`；
6. 不得声称已替用户自动上传附件。

## 本地 CLI 备用路径

```bash
export WEREAD_API_KEY='只在本机当前终端设置'
python3 ~/.codex/skills/weread-portable-notes/scripts/export.py   --app /绝对路径/MetaDatabase/WeReadPort   --profile obsidian --output /私有输出目录
unset WEREAD_API_KEY
```

无密钥演示：

```bash
python3 ~/.codex/skills/weread-portable-notes/scripts/export.py   --app /绝对路径/MetaDatabase/WeReadPort   --demo --output /tmp/weread-demo
```

## 安全硬边界

- 只使用应用冻结的官方网关合同；禁止 Cookie、二维码、模拟登录、共享密钥、整书或刷时长；
- 密钥只能存在于当前浏览器 Worker/单次同源代理请求或本地环境变量；
- `upgrade_info`、认证失败、结构异常、全部失败、归档篡改或数据冲突必须故障关闭；
- Protected Regions 逐字节保留；不得静默删除或编造用户内容；
- ChatGPT 专用文件疑似含密钥或超过 4 MiB 时，只降级该制品并保留迁移 ZIP；
- 文件上传和 ChatGPT 附件均由用户本人明确选择。

## 验证

```bash
cd /绝对路径/MetaDatabase/WeReadPort
npm run verify:all
```

详细合同见 `references/contract.md`。
