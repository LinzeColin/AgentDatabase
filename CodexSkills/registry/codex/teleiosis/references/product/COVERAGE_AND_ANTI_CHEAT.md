# 覆盖与反作弊合同

1. Catalog 总数、Coverage 总数、Waiver 数和 Field 完成状态都由逐项账本派生，不能手填。
2. 源码清单与运行时清单必须同 ID 对账；删除难测项不能缩小分母。
3. 八维分别闭合，任何一维不能被平均分掩盖。
4. COVERED 必须有 Oracle 和 Evidence；N/A 必须有具体原因；Waiver 必须有 Owner、期限、理由、补偿控制与证据。
5. P0/P1 必须为零；FIXED/VERIFIED 缺陷必须保留最小复现、根因、修复回归、邻域回归和残余风险。
6. 关键测试至少一个有效 Negative Control；故意破坏 Subject 后仍绿色即阻断。
7. `field_validation_complete` 由完成的 FIELD_OBSERVED 实验派生；合成和受控人类证据不得升级为 Field。
8. capture-recapture 只能估计残余缺陷规模，不能证明零缺陷。
