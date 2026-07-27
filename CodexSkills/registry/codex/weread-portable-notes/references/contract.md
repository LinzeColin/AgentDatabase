# 微信读书个人笔记可移植合同

- 官方数据源固定为腾讯微信读书 Agent Gateway；每次请求携带 `skill_version=1.0.4`；收到 `upgrade_info` 停止受影响操作。
- 本地输入只接受一个经校验历史 ZIP、一个规范化 JSON，或最多 50 个 Markdown/TXT；在浏览器 Worker 内处理，不上传服务器。
- 输出包括四类 Markdown、Canonical JSON、离线搜索、中文报告、Manifest、SHA-256、迁移 ZIP；正常时附 ChatGPT 中文阅读文件。
- 相同输入与配置产生相同 ZIP；完整、部分、失败不得混淆；用户保护区逐字节保留。
- ChatGPT 只打开 `https://chatgpt.com/`；不携带 query/hash/密钥/笔记/提问词，不自动添加附件。
- P0 不启用登录、D1、服务器笔记库、凭证库、个人定时同步或模型推理。
