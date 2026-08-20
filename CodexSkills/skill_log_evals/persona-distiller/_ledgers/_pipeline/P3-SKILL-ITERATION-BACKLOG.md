
## 候选 1（2026-08-20，Eiffel #142 实测）
- **对象**：`persona-distiller/scripts/check_authorship.py`
- **失效**：法语 OCR 形态 5 例认不出，全部是真实署名但判据漏：
  ① `PAR /' G. EIFFEL`（OCR 在 PAR 与名字间插入 `/'`）
  ② `NOTE > s DE EIFFEL`（DE 引出词 + OCR 噪声）
  ③ `Mie CAP EL`（`M. G. EIFFEL` 被打碎成不可读形态）
  ④ 无题名页正文开头（抽到正文 §6）
  ⑤ holdout 合作件（PROJET PRESENTE PAR M. G. EIFFEL … Dressé par MM. E. NOUGUIER）
- **现状**：v0.0.0.168 已加 `Par` 前缀，但**无 OCR 噪声容错**（`PAR` 与名字间多字符）且**无「无题名页」豁免**。
- **下一步**：等有 2+ 例同类法语 OCR 形态（或 T2/T3 上报）再做检查点；改动须过 build_manifest + check_contract_drift + 全量自检，否则回滚。
- **状态**：OPEN（待触发阈值）
