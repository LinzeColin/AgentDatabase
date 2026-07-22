# dws_probe.md

每次运行和每次升级后都重新探测 version、auth、help、目标 leaf schema；私有群 ID、profile、corpId、凭据和原始响应不入 Git。

## 只读探测顺序

1. `command -v dws`、`dws version` 和 `dws upgrade --check --format json`；
2. 先读取产品/分组 Schema，再读取拟调用 leaf 的 Help 和 Schema；
3. 记录版本、canonical path、effect、risk、confirmation 和 Schema SHA-256；
4. `dws auth status --format json` 必须为已登录，且另有企业管理员授权与精确 profile/enterprise/conversation 绑定；
5. 只有 `effect=read`、身份绑定唯一、输出脱敏和本地落点通过时才允许真实读取。

`DWS_CONFIRMATION_METADATA_NOT_AUTHORIZATION`：`confirmation=not_required` 不代表用户或企业授权。任何 `effect=write|destructive` 都在本 Skill 中 fail closed，不调用、不 dry-run 真实对象、不用 `--yes` 探测。
