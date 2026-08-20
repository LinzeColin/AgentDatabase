# Telford #37 状态（2026-08-20 17:40）

## 已完成
- namesake gate ready（单候选 Q380875）
- init_target quick 档，工作区 workspaces/thomas-telford
- 探源两轮：archive.org + Gallica，13 份已取回（9 手 + 议会系列）
- ingest 13 份：P1×5 / P2×8；train 10 / holdout 3
- dedup：10 部作品；counting_convention 声明 2 对（供水报告↔自传）
- assign_holdout --apply：密封 3 份（Bridge词条/Dunmore/1817附录）
- 移文件到 raw-holdout + references/holdout；check_material_split 通过

## 卡点（research 门 2 处硬错）
1. `research.authorship-unproven` src-01d9132416de（供水报告）：正文 `REPORT Of Thomas Telford, Civil Engineer` 被 OCR 打成 `REPORT H Of`，判据 REPORT 前缀不认
2. `research.authorship-unproven` src-0fd7902a2175（Bridge 词条 holdout）：`Telford, Thomas y Alexander Nimmo` 西语 y 合著，判据不认
- 一手占比 train = 0.4 刚好达标；**降级会毁占比，必须修判据**

## P3 判据改进点（7 例同类：Eiffel 5 + Telford 2）
check_authorship 需补：
① 单姓讨论轮次 `Mr. Telford`（议会证词，Telford 语料 22-33 次/份）
② 报告型署名 `REPORT(?: H)? Of <Name>, Civil Engineer` 前缀
③ 西语合著 `X y Y`（Eiffel/Telford 均涉）
已用 check_text 实测：全名 `Mr. Thomas Telford`✓、`THOMAS TELFORD, ESQ`✓、其余 ✗

## 待办
- [ ] P3 改 check_authorship（有实测证据，改后全量自检+回归）
- [ ] 重判 Telford 2 份 + Eiffel 5 份（若能回溯）
- [ ] 六路研究文档 → claims → docs → cases → 盲判 → 发布 → 登记
