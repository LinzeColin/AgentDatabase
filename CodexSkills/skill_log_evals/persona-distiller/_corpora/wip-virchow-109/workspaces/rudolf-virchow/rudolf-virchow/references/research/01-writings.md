# 01 著作

> 语种：德文。**逐字引文只能取德文 P1**；本工作区 30 份英译／法译一律记 P2，
> 是译者的字，不是他的字。

## 核心著作：《Die Cellularpathologie》(Berlin: Hirschwald, 1858)

- src-3bf8c9c3b522 —— **Deutsches Textarchiv 双录入转写本，非 OCR，1858 初版**。
  扉页可核：「Zwanzig Vorlesungen, gehalten während der Monate Februar, März und April
  1858… BERLIN, 1858. Verlag von August Hirschwald」，全书 91.4 万字符至
  「Druck von Trowitzsch und Sohn in Berlin」。**逐字引文以这一份为准。**
- src-63ac5a56f924 —— **不是 1858，是 1871 年第四版**（Project Gutenberg #44921）。
  扉页作「Vierte Auflage. Berlin, 1871」。抓源时的文件名年份有误，已按扉页更正。
- src-f98483048f3c —— 1871 年第四版（Bayerische Staatsbibliothek 扫本）。

**★ 一处必须写明的实测：那句拉丁公式根本不在 1858 初版里。**

| 出处 | 拉丁公式 | 实测 |
|---|---|---|
| src-0f84fd47f3c0〈Cellular-Pathologie〉1855 | `Omnis cellula **a** cellula` | ✅ |
| src-911fadcbcd25《Gesammelte Abhandlungen》1856 | `Omnis cellula a cellu**ll**a` | ✅（且 cellula 拼成 cellulla） |
| **src-3bf8c9c3b522《Cellularpathologie》1858 初版** | — | **全书 0 处** |
| src-63ac5a56f924 / src-f98483048f3c 同书 1871 第四版 | `Omnis cellula **e** cellula` | ✅ |

**1858 初版是用德文说这件事的，没有那句拉丁话。** 原样（含换行连字符）：

> «so wenig lassen wir in
> der physiologischen oder pathologischen Gewebelehre es zu, dass
> sich aus irgend einer unzelligen Substanz eine neue Zelle auf-
> bauen könne. Wo eine Zelle entsteht, da muss eine Zelle
> vorausgegangen sein»
> ——src-3bf8c9c3b522，《Die Cellularpathologie》Berlin 1858

而 1871 第四版把它提升成了一条**有名字的定律**，写进目录：

> «Das Gesetz von der continuirlichen Entwickelung (Omnis cellula e cellula)»
> ——src-f98483048f3c，1871 年第四版目录

**所以这句话的三层要分开说：**
1. **1855 年在《Archiv》里首次用拉丁文，作 `a cellula`**；
2. **1858 年成书时只有德文表述，没有拉丁公式**；
3. **1871 年第四版改作 `e cellula`，并被列为一条定律的名称。**

**把「Omnis cellula e cellula」记在 1858 年名下，是一处普遍的、可核的错**——
我自己在本文件的第一版里就是这么写的，根因是照着文件名里的年份写，没看扉页。

## 期刊：《Archiv für pathologische Anatomie und Physiologie》(1847 起)

他创办并长期主编。**卷次本身不算他的著作**（多人合著），故 44 个卷次一律记 U；
他本人的文章按正文署名「Von R. Virchow」切出，成 22 个 `art-*` 单元记 P1：

- src-0f84fd47f3c0 〈Cellular-Pathologie〉(1855) —— 公式最早出现处之一
- src-51df3ba90ac1 〈Die naturwissenschaftliche Methode und die Standpunkte in der Therapie〉
- src-05057e87c590 〈Descendenz und Pathologie〉(1886)

每份文件头记着母卷与字符偏移，**切得对不对可以回卷复核**。

## 其余主要著作

- src-d82862576099《Die krankhaften Geschwülste》(1863–67)
- src-911fadcbcd25 / src-f746c5e8237d《Gesammelte Abhandlungen zur wissenschaftlichen Medicin》
- src-f746c5e8237d《Gesammelte Abhandlungen zur wissenschaftlichen Medicin》1862 卷

> **1877 年的《Sectionstechnik》故意留作 holdout，本路不引它。**
> 留出集一旦被研究笔记引用，它就不再是留出集——`known` 套组也就测不出
> 「不在训练集里的事他知不知道」。研究门实测拦住了这一处（`research.invalid-source`）。
