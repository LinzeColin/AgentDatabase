# Raw Teleiosis 内置模块 v0.0.0.3

这是 Teleiosis v0.0.0.3 的 `T` 模块描述目录，不是 v0.0.0.2 快照，也不是独立安装包。

为避免版本漂移、重复源码、旧命令误执行和 Catalog 污染，T 的唯一实现位于父级 `teleiosis` canonical tree。本目录只保留：

- `MODULE.md`：模块职责与边界；
- `CAPABILITIES.json`：每个 T 阶段必须全量检查的能力表；
- `VERSION`：统一产品版本；
- `LICENSE` / `NOTICE.md`：来源与许可边界。

固定调用链仍为：`T1 -> C1 -> S1 -> C2 -> P1 -> C3`；三轮一组，三组一次 Run。`C` 是被迭代对象本身，不是固定 SHA。
