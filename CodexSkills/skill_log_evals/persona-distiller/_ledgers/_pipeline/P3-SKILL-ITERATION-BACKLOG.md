
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

## 候选 2（2026-08-21，Telford #37 实测）
- **对象**：模型文档生成惯例（gen_docs 指令 / release 门文档）
- **失效**：产物里 `"..."（src-7d31bbb6da22）` 这种「src 标注」**不被 check_quote_locator 认作坐标**
  ——判据只认同段内的年份/页码/刊名/@偏移。Telford 10 份文档一次性 65 条长引文缺坐标，
  release 被拦，逐条补年份返工。
- **现状**：check_quote_locator.py 的 LOCATOR 正则不含裸 `src-XXX`（这是设计：读者无法凭一个
  source_id 回查出版时间）。文档生成时若只写 `（src-XXX）`，release 必返工。
- **下一步**：在 gen_docs / PLAYBOOK 里把坐标惯例写成 `（src-XXX，YYYY 年）`（或同段带年份），
  从源头消除。改动先验证在下一个 persona 上不再触发 0 返工。
- **状态**：OPEN（建议 T2/T3 直接采用 `（src-XXX，YYYY 年）` 写法，不等待）

## 候选 3（2026-08-21，Telford #37 实测）
- **对象**：check_claim_coverage.py + check_unsourced_names.py 的 OCR 拼写变体处理
- **失效**：语料 OCR 把 Pontcysyllte 拼作 Pontycysyllte。claims 层 check_claim_coverage **无排除机制**，
  关键实体在引用源里搜不到即报「装饰性引用」；答案层 check_unsourced_names 靠 `raw/_EXCLUDED.txt`
  项目记录兜底（二手依据）。同一拼写问题跨两道门，修法不同。
- **现状**：claims 文本须用语料拼写（Pontycysyllte）；答案/产物可保留标准拼写 + `raw/_EXCLUDED.txt`
  说明。`_EXCLUDED.txt` 需 `.gitignore` 例外（2026-08-21 已在 persona-distiller/.gitignore 加
  `!**/raw/**/_EXCLUDED.txt`）。
- **下一步**：若 T2/T3 再遇 2+ 例同类 OCR 变体，考虑给 check_claim_coverage 加「台账著录/别名表」
  机制，否则维持现状（两条门各自的修法已通）。
- **状态**：OPEN（观察中）
