# #106 Louis Pasteur —— 同名风险（**本族第一个有实质风险的人物**）

`namesake_gate.py` 返回 `resolution: none / candidate_count: 0`——**那只说明平级注册表里没有**，
公开源要人自己搜。实搜结论如下，**与 Jenner、Semmelweis 那两次「无消歧义页」完全不同**。

## ★ 一号风险：Louis Pasteur Vallery-Radot（1886–1970）

**他的外孙，本身是医生，而且是《Œuvres de Pasteur》全集（7 卷）的编者。**

- 名字里**字面包含「Louis Pasteur」**
- 同为医生 → 医学文本里出现他的名字完全自然
- **全集每一卷的扉页与编者按上都印着他的名字**

→ `check_authorship.py` 的 `A-editorial` 证据**极易挂到他身上**，
把外孙 1930 年代写的编者按当成 Pasteur 本人 1880 年代的话。

**这与 Jenner #104 的 `b22006345`（扉页 PUBLISHED By Doctors JENNER and WOODVILLE，
实为匿名第三方册子）是同一形态**——扉页上有目标人物的名字，而文本不是他写的。

### 抓源与 ingest 阶段的硬约束

1. **凡取自《Œuvres de Pasteur》或《Correspondance》的文本，必须分清正文与编者按。**
   编者按、序、脚注一律记 `S1 / external`，`--author` **不得**填 Louis Pasteur。
2. **凡 P1 源，逐份到扉页确认署名是 `Louis Pasteur` 而非 `Louis Pasteur Vallery-Radot`。**
   `check_source_attribution.py`（v0.0.0.34）会逐份要求点名，别指望它替你读扉页。
3. 时间判据最硬：**Pasteur 卒于 1895-09-28。1895 年之后署名的文字一律不是他的。**
   外孙 1886 年才出生。

## 二号风险：William Pasteur（1855–1943）

瑞士裔英籍医生。**同姓、同职业**，活跃期与 Pasteur 晚年重叠。
19 世纪末的英文医学期刊里出现 "Dr. Pasteur" 时，须看上下文是巴黎还是伦敦。

## 三号：机构名淹没

Institut Pasteur、Pasteur Institute、巴黎地铁 Pasteur 站、南极 Pasteur Island／Peninsula、
以及大量以他命名的街道与学校。**全文搜 "Pasteur" 会被机构名淹没**，
关键词须用 `Pasteur, Louis` 或配合年份／地点。

## 其余（低风险，年代或领域可分）

Marie Pasteur（妻，1826–1910）、Cheryl Pasteur（美国政治人物）、
Simon Pasteur（喀麦隆足球运动员，1985–）、Pasteur Bizimungu（卢旺达总统，Pasteur 作**名**）。
