# External 2×6+1 Review Adapter

## 信任边界

正式 adapter 必须位于 workspace、target、optimizer 与安装包之外，以绝对路径和 SHA-256 在首个 Candidate patch 前冻结。Receipt root 由远端 provider、独立 OS principal 或 hardware-attested runtime 控制；Candidate 不得写入，也不得访问签名私钥。

正式合同必须冻结：

```text
attestation_mode = FORMAL_EXTERNAL
trust_mode = ED25519_SIGNED_RECEIPTS
signature_algorithm = ed25519
trust_anchor_provisioning = PRE_EXISTING_EXTERNAL
isolation_mode = REMOTE_PROVIDER | SEPARATE_OS_PRINCIPAL | HARDWARE_ATTESTED
```

每个 12 个 reviewer seat 和第 13 个 verifier 均需：

- 唯一 actor/context/provider-run/provider-request ID；
- round 1-2、seat 1-6 的精确覆盖；
- 外部 provider 原始 receipt 文件、SHA-256、detached Ed25519 signature；
- packet/adapter/trust-anchor hash；
- provider、runtime、model/config、开始/结束；
- verifier `read_only=true` 且不复用 reviewer 身份；
- verdict、dissent、成本和 residual trust。

聚合 attestation 本身也必须由同一冻结 trust anchor 对 canonical payload 签名。任一 receipt、签名、身份或路径复用立即失败。

## 参考命令

```text
teleiosis-review-attestor verify-batch \
  --contract /trusted/benchmark-and-review-contract.json \
  --packet-index /frozen/packet-index.json \
  --receipt-root /external/protected/receipts \
  --output /external/protected/receipts/attestation.json
```

仓库内只提供协议、Schema、测试和诊断示例；包内示例、临时本地密钥或 `candidate_authored=false` 的自我声明都不能单独证明组织独立。`DIAGNOSTIC_FIXTURE` 只能返回 `DIAGNOSTIC_ONLY`。

Ed25519 验证使用可选 `cryptography` runtime 能力；缺失时返回 `UNAVAILABLE`，不影响普通 engineering 使用，但阻断 formal promotion。只有独立操作者/可信 runtime 部署、外部签名原始 provider receipts 和独立只读 verifier 能通过正式 Gate。

当前环境若不具备该能力，准确状态为 `INDEPENDENT_REVIEW_UNAVAILABLE / FORMAL_PROMOTION_BLOCKED`。
