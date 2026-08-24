# Timeline, stages, and drift

## Scope and assigned sources

**本道分到 1 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-2bde83f62227` | 1911 | P2 | Persönliche Erinnerungen an Vincent van Gogh |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

- **timeline 道由家人回忆支撑**：train 侧主件为其妹 Elisabeth Huberta
  du Quesne-van Gogh 的德文《Persönliche Erinnerungen an Vincent van Gogh》（1911 二版，
  `src-2bde83f62227`，题名页照录 "PERSÖNLICHE ERINNERUNGEN AN VINCENT VAN GOGH
  E. H. DU QUESNE-VAN GOGH ... R. PIPER & CO., VERLAG MÜNCHEN 1911"）。同一回忆录的
  1910 荷文版（`src-b6ad5f245978`）与 1913 英文版（`src-8e3cd60bfeea`）在 external 道，
  三语版本可互相核对生平细节。
<!-- src-2bde83f62227 -->
- **生平阶段线（据此道与其他材料归纳）**：1853 生于 Zundert 牧师家庭；早年为画商
  学徒（海牙/伦敦/巴黎，至 1873 前后）；1876-1879 任英国教师、传道员，后投身
  传教；1880 年起立志为画家；1881-1883 海牙、Drenthe；1883-1885 纽南（《吃土豆的人》
  时期）；1886-1888 巴黎；1888 移居阿尔勒，邀 Gauguin 同住，12 月发生割耳事件；
  1889 自愿入住圣雷米疗养院；1890 移居 Auvers-sur-Oise，7 月 27 日枪击自尽，
  7 月 29 日去世，Theo 次年病逝。
<!-- src-2bde83f62227 -->
- **死后的漂移（名声曲线）**：1892 遗作展 → 1905 阿姆斯特丹 Stedelijk
  回顾展（`src-83dba76ee577`）→ 1910s 传记（Duret `src-b3328eb38b77`）→ 1920 纽约
  Montross 展（`src-e9d58b40a500`）→ 1926 Meier-Graefe 传记英译（`src-aa28f9129a99`）
  → 1928 医学评述（`src-15ac632b9c8b`）。语料覆盖时间跨度 1892-1928，正好是其声名
  从寂寂无名到确立的过程。

## Candidate Claims

- 梵高 1880 年才正式立志为画家，此前经历画商学徒、教师、传教士三段职业尝试
  （`src-2bde83f62227`）。
- 其创作生涯可划分为海牙/纽南（1881-85）、巴黎（1886-88）、阿尔勒（1888-89）、
  圣雷米（1889-90）、奥维尔（1890）五个阶段（`src-2bde83f62227`）。
- 死后约四十年内（1892-1928）其声名由遗作展逐步建立（`src-83dba76ee577`、
  `src-aa28f9129a99`）。

## Contradictions and alternative explanations

家人回忆（其妹）带有亲属滤镜，对梵高早年生活与性格的描述需与书信自述互相印证；
1892 遗作展目录不在本道范围。

## Unknowns and source gaps

1888-1890 晚期（阿尔勒割耳、圣雷米、奥维尔）的第一手细节在本语料中覆盖不全，
本道主要靠书信与家人回忆间接支撑。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

timeline 道以家人回忆（`src-2bde83f62227`）为 train 侧主件，辅以展览/传记的时间线索，
给出梵高的生平阶段与死后声名漂移。
