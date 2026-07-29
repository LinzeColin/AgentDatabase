# Risk Controls

## 环境等级

- `R0`: 只读源码、离线 Schema/fixture。
- `R1`: 本地或一次性 sandbox，可销毁数据。
- `R2`: staging/测试租户，有限共享依赖。
- `R3`: canary，小流量真实用户，强制 Flag/rollback。
- `R4`: production，默认观察；主动风险动作需 owner 明示授权。

## 高风险动作 Gate

以下动作必须记录 target、authorization、blast radius、abort、rollback 和 owner：

- 主动漏洞扫描、注入和权限攻击。
- Stress/spike/breakpoint/soak。
- Chaos、kill、network partition、disk/CPU pressure。
- 删除、付款、发布、批量写、真实通知。
- 真实用户回放和敏感数据处理。
- 对竞品的自动化访问或高频请求。

## Kill switches

- Token/模型成本上限。
- 并发、QPS、时长和错误率阈值。
- 数据差异、权限、隐私和 P0 告警。
- 目标 digest 变化。
- 无法确认 rollback。

## 证据保全

Abort 后保留时间、subject、工具配置、动作序列、trace/log、world-state snapshot 和未完成副作用；不要为了“清理”删除事故证据。
