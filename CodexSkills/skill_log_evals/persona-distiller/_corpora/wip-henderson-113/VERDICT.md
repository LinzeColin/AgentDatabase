# #113 Virginia Henderson — **不按 deep 推进，记延后（第三类成因）**

**没有跑蒸馏。** 这一次派的是**可得性探测**，因为她 1996 年卒、
主要著作很可能仍在版权期内，而铁律是只取公有领域、付费墙一律不碰。

## 结论：够不着，差一个数量级

| | 实测 | 门 |
|---|---:|---:|
| 真取到全文的源 | **2 份**（按独立源计更接近 1.5） | ≥45 |
| 六条道覆盖 | **2 条** | 6 条 |
| 确认公有领域的 | **0 件** | — |

`conversations` / `decisions` / `timeline` / `external` **全 0**。

## ★ 版权状态有硬证据，不是推测

Stanford 的库返 CAPTCHA（**未绕过**），改用 **NYPL `cce-renewals`**
（美国版权局 CCE 机读转录）拿到同等证据：

| 著作 | 续展记录 | 保护至 |
|---|---|---:|
| 教科书 4 版（1939） | `© 29Aug39; A131865. Virginia Henderson (A); 14Apr67; R408306.` | 2034 |
| 教科书 5 版（1955） | `A210898 / RE180356 / 1983-11-04 / Virginia Henderson\|A` | 2050 |
| *Nursing Research*（1964）、*The Nature of Nursing*（1966） | 1992 年法案自动续展 | 2059 / 2061 |
| *Basic Principles*（ICN 日内瓦 1960） | 瑞士出版的外国作品，经 URAA/§104A 自动恢复 | 2066 |

**两部教科书都是她本人亲自续展的**——
不存在「1964 年前未续展而进入公有领域」的侥幸。

## 缺口不是某几条道空，是一手源在开放渠道近乎为零

**决定性的一条**：archive.org 的《American Journal of Nursing》
1900–1930 每年 21–26 件**全刊期**，**1931 年起每年只剩 2 件 index 卷**。
她最早的 AJN 文章是 **1935 年**——**正好卡在开放区外**，10 篇一篇取不到。

OpenAlex 全量 87 条，`is_oa=true` 仅 5 条：2 条是**同名地质学家**、
1 条非她署名、1 条 Cloudflare 拦（未绕过）、1 条 PMC。**其余 73 条全 closed。**

根因：**她的产出期 1935–1994 整段落在版权保护内**，
不像 Nightingale / Lister / Virchow 有十九世纪的公有领域主体。

## 真取到的两份，如实标注

| 文件 | 词数 | 性质 |
|---|---:|---|
| `paho-principios-basicos-1961` | 18,222 | PAHO *Publicaciones Científicas* No.57，即 ICN *Basic Principles* **西班牙文全本**，扉页载 `preparado por VIRGINIA HENDERSON, R.N., M.A.` |
| `paho-principios-fundamentales-1958` | 15,557 | *Bol Of Sanit Panam* 1958;44(3):217（PMID 13510330），她署名论文 |

**这两份不是公有领域，是 publisher-open**（PAHO IRIS 自己开放分发）。
且两文同源（1958 是 1961 的前身会议论文），**按独立源计约 1.5 份**。

## 最可惜的一项

**Safier《Contemporary American Leaders in Nursing: An Oral History》(1977)**
含 Henderson 章——**唯一已知成规模口述史，lending-only，未碰**。

archive.org 上 8 个 Henderson 相关扫描（含 1939/1966/1978 三部主著）
全部 `access-restricted-item: true` + `inlibrary`，**一律未碰**。

## 处置

- **不按 deep 推进。** 入 `_延后名单.json`，成因记为**第三类**：
  **一手源确实是他的、也确实存在，但整段产出期在版权保护内且本人亲自续展。**
- **这一类与 Grace Hopper 那类必须分开记**：那一类补足来源即可恢复，
  **这一类版权到期前不可能恢复**（最早 2034、最晚 2066）。
- **没有为交差把 S2 当 P1，也没有把 publisher-open 当成公有领域。**

## 由此得出的排期规则

> **卒于 1930 年后的人物，排期前先跑一次可得性探测。**

探测的成本远小于抓一半再废掉。三步：
**先查版权状态**（要有 CCE 续展记录这类硬证据，**不确定一律当作仍受保护**）
→ 再查开放渠道 → 最后给一个诚实的份数。

**「够不着」是有价值的结论，不是失败。**
