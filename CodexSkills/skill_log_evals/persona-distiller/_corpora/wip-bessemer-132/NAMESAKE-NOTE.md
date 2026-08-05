# Bessemer #132 同名处置——目标 1 人，显式排除 3 人

`namesake_gate.py` 的口径是**纯机械的**：候选 >1 就 `blocked`，它不判断谁是目标。
所以按 Coffin #130 的先例：**只把已解析的目标喂给门，被排除的另存并提交**
（`evidence/namesake-excluded.json`）。

门的结果：`status=ready`、`resolution=single`、
`selected_subject_uid=bessemer-henry-1813-1898-steelmaker`。

## ★★★ 本人物的同名风险是「书内同名」，不是「同代人重名」

| | |
|---|---|
| **目标** | Henry Bessemer **1813–1898**，转炉炼钢法 |
| **必须排除** | Henry Bessemer **1838–1907**，**长子，同名同业**（分析化学家，Bessemer Brothers, East Greenwich） |

**自传《Sir Henry Bessemer, F.R.S.: An Autobiography》(1905) 是两个人写的：**

| 页码 | 作者 | 能不能当一手 |
|---|---|---|
| pp. 1–326（Ch. I–XX） | **本人** | ✅ 第一人称自述 |
| **pp. 327–约380（Ch. XXI，含那份 129 件专利清单）** | **儿子** | ❌ **不是他写的，约占全书 14%** |
| Ch. XXI 内转载的他本人书信 | 本人 | ✅ 载体是儿子的章，文本是他的 |

依据是 1905 原书 Ch. XXI 开头的编者方括号（探测报告里有逐字原文与字节坐标）：
`...to complete it with the assistance of his eldest son, Mr. Henry Bessemer.`
archive.org 的 `creator` 字段也列了两位作者。

### ★★ 标签陷阱：同一个字符串在同一本书里指两个人

- 在 Ch. XXI 里，`Mr. Henry Bessemer` / `Mr. Bessemer` = **儿子**，`Sir Henry` = 父亲
- 在 1856 年那些章节里，`Mr. Henry Bessemer` = **父亲**（当时尚未受封）

**所以抓源时不能按「Mr. Bessemer」这个标签切分，必须按页码/章节边界切。**

### 他本人在印刷品上的署名（探测实测原样，非推想）

`Henry Bessemer`（如 `Denmark Hill, January 3, 1878. Henry Bessemer.`）——
**不是** `Sir Henry Bessemer`（那是别人称呼他，且限 1879 受封后），**不是** `H. Bessemer`。

★ **探测在 5 个学会卷册里搜 `"Mr. Bessemer"` 全部零命中**——
学会发言标签这一类**本次为空**，后续不要假设 `Mr. BESSEMER said` 存在。
