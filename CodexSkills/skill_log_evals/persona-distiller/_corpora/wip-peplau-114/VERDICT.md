# #114 Hildegard E. Peplau — **不按 deep 推进，记延后（第三类成因）**

**没有跑蒸馏。** 这一次派的是**可得性探测**，因为她 1999 年卒、
主要著作很可能仍在版权期内，而铁律是只取公有领域、付费墙一律不碰。

**没有假定她与 #113 Henderson 相同**——版权、开放渠道、档案三层各自重查了一遍。
结论同向，成因略有不同（见下）。

## 结论：够不着，差一个数量级

| | 实测 | 门 |
|---|---:|---:|
| 真取到全文的源 | **3 份** | ≥45 |
| 六条道覆盖 | **4 条**（writings / expression / conversations / timeline） | 6 条 |
| 确认公有领域的 | **0 件** | — |

`decisions` 只有 0.5（散在问答里，无独立文本）、`external` **0**。
三份合计 **30,347 词**，且集中在「患者会谈技术」一个题域。

## ★ 版权状态有硬证据，不是推测

用 **NYPL `cce-renewals`**（美国版权局记录的机读转录）**47 个年度文件全下、全 grep**，
`peplau` 全库**仅 1 条**命中：

```
Hildegard E. Peplau, foreword by R. Louise McManus.
Interpersonal relations in nursing.
A62979  1952-01-14   RE66969  1980-09-29   Productions Corporation|PWH
```

| 著作 | 状态 | 保护至 |
|---|---|---:|
| *Interpersonal Relations in Nursing*（1952） | **RE66969 / 1980-09-29 按时续展**（依 §305，1952 年作品的续展年即 1980 年，窗口内） | **2047 年底** |
| *Basic Principles of Patient Counseling*（1964, Smith Kline & French） | 1964 年出版，吃 1992 年法案**自动续展**；全库 grep `patient counseling` = 0 命中，与「无需申报」一致 | **2059 年底** |

**旗舰著作被人按时续展、第二本直接吃到自动续展——两条路都堵死。**
不存在「漏续展而落入公有领域」的侥幸。

## 缺口不是某几条道空，是一手源在开放渠道近乎为零

**决定性的一条**（与 #113 完全一致）：archive.org 的《American Journal of Nursing》
1900–1930 每年 5–26 件**全刊期**，**1931 年起每年只剩 1–3 件 index 卷**。
她最早的 AJN 文章是 **1947 年**——**整段产出全在开放区外**。

**全量核验，不是抽样**：Crossref 取回她署名 **113 个 DOI**，逐条查 Unpaywall
→ `is_oa=true` **仅 2 条**，其中 1 条（AJN 1970，bronze）实测 Cloudflare 403，**未绕过**。
113 条里带 license 的 30 条**全是 Wiley/Sage/Elsevier/Springer 的 TDM 许可，无一条 CC**。

Europe PMC 63 条 OA **0**；DOAJ 4 条**无一条是她**；ERIC **0**；
OpenAIRE 12 条全 closed/unspecified；WHO IRIS 17 条**无一条她署名**。

## 真取到的三份，如实标注

| 文件 | 词数 | 性质 |
|---|---:|---|
| `paho-orientacion-paciente-1968` | 21,176 | PAHO *Publicación Científica* No.167（1968-11），即《Basic Principles of Patient Counseling》**西班牙文全译本**。扉页原文载 `Reprinted with permission of Smith Kline & French Laboratories / Copyright © 1964` |
| `paho-vinadelmar-salud-mental-1970` | 8,032 | PAHO 智利 Viña del Mar 工作组文集（1970）中**她署名的一章**；脚注注明译自 *Community Mental Health Journal* |
| `iee-premio-reimann-1998` | 1,139 | 1997-06-15 温哥华 ICN 大会 **Christiane Reimann 奖领奖致辞**，载 *Investigación y Educación en Enfermería* 16(1)。DOI `10.17533/udea.iee.16928`，gold OA / CC-BY-NC-SA。纯图像 PDF，**OCR 取得**；其中末 339 词是译者写的介绍，**不是她本人** |

**三份都不是公有领域**：前两份是 **publisher-open**（PAHO IRIS 获授权分发），
第三份是**开放许可**（期刊自陈版权归期刊）。**没有把 publisher-open 冒充成 PD。**

## 与 #113 的差别：只在运气，不在量级

`paho-orientacion-paciente-1968` 是本批到目前**质地最高的一份 20 世纪语料**——
正文是**工作坊逐字问答**，`Enfermera:` 提问 **69 次**、`Profesora:`（= Peplau）作答 **72 次**，
里面有她第一人称的分歧自述（「我得承认，很多护士在这些做法有没有用上跟我意见不同」）。

**但这改变不了量级。** 3 份对 45 份。
而且她的理论主干（interpersonal relations 六阶段、四个护士角色）**一手文本一个字也取不到**。

## 最可惜的一项

**Penn / Barbara Bates Center 的 *Hildegard E. Peplau papers* (MC 59)，
Box 1 Folder 2：「Oral history, psychiatric nursing career, conducted by Patricia D'Antonio, PhD., 1985」**
——已知唯一成规模的 Peplau 访谈转录。
finding aid 原文写明材料「**physically available in their reading room,
and not digitally available through the web**」。**实体闭架，未碰。**

Schlesinger Library（Radcliffe/Harvard）另有她 1984 年亲捐的三个全宗与录音带
T-165 / Vt-41，HOLLIS finding aid 本机 404，**无任何公开转录的证据**。

archive.org 上她的三个书扫描（1952 初版、1988 重印、1989 选集）
全部 `access-restricted-item: true`，**一律未碰**。

## 处置

- **不按 deep 推进。** 入 `_延后名单`，成因记为**第三类**（与 #113 同类）：
  **一手源确实是她的、也确实存在，但整段产出期在版权保护内且被按时／自动续展。**
- 这一类**版权到期前不可能恢复**（最早 2048、最晚 2060）。
- **没有为交差把 S2 当 P1，没有把 publisher-open 当成公有领域，没有绕过任何访问控制。**

## 由此加固的排期规则

> **卒于 1930 年后的人物，排期前先跑一次可得性探测。**

#113 与 #114 连着两个坐实了同一个系统性障碍。建议把这条**固化成排期表的硬前置**，
而不是每次排到了才发现。

**一条可复用的正面经验**：`iris.paho.org` 的 DSpace REST API
是 1950–70 年代美国护理学家的稳定开放渠道（Henderson 2 份、Peplau 2 份都出自这里），
**但它同时也是上限**——PAHO 只译了各人一两本，挖到底就是个位数。

**「够不着」是有价值的结论，不是失败。**
