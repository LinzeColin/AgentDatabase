# 抓源派发指令 —— #115 Nikolai Slavyanov（写好待发）

> 待 Peplau 的可得性探测回来后发出（**抓源并发保持 1**，两边都要打外部服务器）。

---

你负责 **#115 Nikolai Gavrilovich Slavyanov（Николай Гаврилович Славянов，
1854-05-05 – 1897-10-17，俄国工程师，电弧焊「金属电极」法）** 的语料抓取。

## 工作目录

`CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-slavyanov-115/`
语料放 `raw/<短名>/<短名>.txt`，台账写 `raw/_ids.txt`。

## 铁律（违反其一，整批作废）

1. **零编造。** URL 必须是你真的取到过内容的。取不到就写进 `raw/_fetch.log`。
   **绝不允许凭印象填写篇名、年份、卷期页码。**
2. **只取公有领域**。他 1897 年卒，其著作与专利在公有领域。
   **付费墙一律不碰，不绕过任何访问控制。**
3. **分档**：`P1` = 他亲笔／署名的专利、论文、报告；`P2` = 同一材料的降质版本
   （重复扫描、OCR 更差、**译本**）；`S1` = 同时代第三方；`S2` = 后世研究。

## ★★ 头号风险：与 Nikolai Benardos 的发明长期被互相混记

| | 生卒 | 电极 |
|---|---|---|
| **Benardos** | 1842–1905 | **碳** |
| **Slavyanov**（本人物） | 1854–1897 | **金属**（可熔） |

**Benardos 也在本项目的队列里，将来会做成另一份产物。**
若这一份把功劳写宽了，两份产物会自相矛盾且同时在册。

**所以台账第 9 列必须带 `ELECTRODE=carbon|metal|both`**，
并且：**讲的是 Benardos 发明的材料，第 8 列要标 `OTHER-INVENTOR`**。
那类材料**仍要抓**（边界题需要它），但下游不得作本人物的声音。

另外单独产出 `raw/_EXCLUDED.txt`，记录你**真的检索到**的：
- Benardos 的哪些专利／论文被你排除，依据是什么（**要引著录原文**）；
- 有没有同名者（`Славянов` 是常见姓）——查得到就记，查不到就写查不到。

## 目标（deep 档）

- **可用源 ≥ 50 份**（门槛 45）；**一手占比 ≥ 70%**（门槛 65%）
- **六条道各 ≥ 4 份**：`writings`（论文与专著）／`expression`（演说、公开陈述）／
  `conversations`（书信）／`decisions`（**专利与工厂技术决定**）／
  `timeline`（生平、讣告）／`external`（同时代与后世评价）

## ★ 语种：他用俄文写作

- **英译本一律 P2**，并在 note 里写明译者与译本年份。
- **逐字引文必须能回俄文原件**——译本里的话不是他的话。
- 俄文扫本要标 `CYRILLIC-OCR-SUSPECT` 若可读性差：
  本流水线在西里尔同形字上栽过一次（Livermore #100 的 OCR 里
  1405 个西里尔字符、314 个「全同形字词」）。**入库后会跑 `check_ocr_homoglyphs`。**

## 台账格式 `raw/_ids.txt`

首行 `# ── #115 Nikolai Slavyanov (1854-05-05 – 1897-10-17, Russian engineer,
metal-electrode arc welding; wrote in RUSSIAN) corpus ledger ──`，
随后每份一行，**制表符分隔 9 列**：

```
短名<TAB>URL<TAB>篇名<TAB>年份<TAB>出处定位<TAB>语种<TAB>分档<TAB>标记<TAB>说明
```

- 第 8 列标记：**归属标记必须有一个**
  （`HIS-OWN` / `CO-AUTHORED` / `THIRD-PARTY` / `ATTRIBUTION-UNCLEAR` / `OTHER-INVENTOR`），
  另可加 `POSTHUMOUS` / `TRANSLATION` / `DUPLICATE-SCAN` / `OCR-POOR` /
  `CYRILLIC-OCR-SUSPECT` / `FULL-PAGE-SCAN`
- 第 9 列说明：**必须以 `lane=<六条道之一>. ` 开头**，
  **且必须含 `ELECTRODE=carbon|metal|both`**，其后写你看过文档后的判断依据

## 另外产出

- `raw/_fetch.log`：每次抓取尝试的结果，成功与失败都记
- `raw/_BOUNDARIES.json`：仅针对整版扫图，给出他那一段的起止行号 + 据以判断的原文行

## 返回值

简短中文报告：① 落盘份数、分档分布、六条道分布；
② **`ELECTRODE=` 三类各几份，`OTHER-INVENTOR` 几份**；
③ 同名与 Benardos 排除查证到了什么（查不到就说查不到）；
④ 探过取不到的重要材料及原因。

**取不到 50 份就如实说取到了几份**，不要把 S2 当 P1，不要编造 URL。
