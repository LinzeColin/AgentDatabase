# Build Agent 最后一公里

Build Agent 不重新研究、重新设计或扩大 Acceptance。固定顺序：

1. 读取目标仓 AGENTS、CONTRIBUTING、部署和安全规则。
2. fetch 最新 integration base；检查 clean state。
3. 运行本包 `verify-self --strict`。
4. 对每项文件执行 `satisfied / apply / adapt / equivalent / conflict / blocked / obsolete` 分类。
5. 在仓外备份，在 staging 树应用，不用旧整树覆盖最新 main。
6. 运行包内测试与目标仓原生测试；更新 Catalog 时保持唯一 slug。
7. 任一后置门失败即精确回滚。
8. 获得明确授权后才 commit/push；推送前重新读取远端，远端前进则停止并重建 integration base。

未知可执行文件冲突、Genesis 不匹配、目标版本高于 v4、未授权生产副作用或 Scope 实质变化时立即停止。
