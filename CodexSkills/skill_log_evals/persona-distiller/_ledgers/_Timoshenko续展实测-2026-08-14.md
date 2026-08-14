# Timoshenko #14x 的 CCE 续展查完了：**三部全部续展过 ⇒ 不是 PD，这条路封死**

## 这是延后条目自己点名要做的动作

他的 `unblock_todo` ① 写着：
「**查 CCE Part 1 的 1963–1968 年卷：1936/1937/1940 三部若未续展即为 PD**（照搬 Mehl #137）」。
今天做完了 —— **结论是反的：续展过，所以不是 PD。**

## 做法（可逐步复现，全部只读公开资料）

1. 在 archive.org 找 CCE Third Series **Part 1（Books and Pamphlets）1963–1968**，共 **12 卷**；
2. 逐卷取 `*_djvu.txt`（合计约 **128 MB**）；
3. **先跑正对照再搜目标**：每卷用 `Hemingway|Faulkner|Steinbeck` 当已知正例
   （各卷命中 60–134 次，证明这卷的 OCR 文本可搜）；
   同时数 `RENEWAL REGISTRATIONS` 段（各卷 38–54 处，证明这卷确实含续展区）；
4. 目标用**容错正则** `T[il1|][mn][o0e]sh?[e3][nm]k[o0e]`（OCR 讹形），
   十二卷合计命中 **37 处**，**逐处打开读**。

## 读出来的三条续展记录（逐字照录）

| 作品 | 原始版权 | **续展** |
|---|---|---|
| **Theory of elastic stability** | © 19Jun36; A95809 | **S. Timoshenko (A); 23Oct63; R324163** |
| **Engineering mechanics; statics**（与 D. H. Young 合著） | © 30Jun37; A107555 | **S. Timoshenko & D. H. Young (A); 5Aug64; R342895** |
| **Engineering mechanics, dynamics**（与 D. H. Young 合著） | © 12Aug37 | **S. Timoshenko & D. H. Young (A); 29Jan65; R355155** |

⇒ **1936 与 1937 的三部全部按时续展**，续展号可查。**它们不是公有领域。**

★ 另有两条不是他的著作权：
`Contributions to the mechanics of solids`（Lessells 编，献给他六十寿辰，© 6Dec38，
Gladys Lessells 1966 年续展 R395976）—— **编者的书，不是他写的**；
1968 卷里的 `As I remember`（自传英译，D. Van Nostrand 1968 年**新登记** A975398）
与 `Elements of strength of materials 5th ed.`（1968 新登记 A967683）
—— **都是 1968 年的新登记，不是续展，且远晚于 PD 分界**。

## 处置（我定的）

- **`unblock_todo` ① 就此关闭**，理由不是「没查到」而是「查到了，且方向相反」；
- 他的 `unblock_todo` ② 仍开着：「换通道找 1911–1920 年的俄文教材（基辅／彼得堡），
  archive.org 没有；可试 РГБ／HathiTrust」—— **本轮未试**（HathiTrust 今天实测仍 403）；
- **一手规模仍是 3 部**（1925／1929／1930，合计 2.44 MB），维持延后。

## 这一轮真正的产出

**把一个「也许能解封」的待办，变成了一个带续展号的确定结论。**
下一个人不必再下 128 MB、不必再读 37 处命中 —— 三个号码就够了：
`R324163`／`R342895`／`R355155`。

★ 方法本身对**另外 10 个同样写着「查 CCE」的人**成立，但**卷不同**：
他们要查的是 **Part 2（Periodicals）**（Duwez 的 J. Appl. Phys.／Phys. Rev.、
Cohen 的 Trans. AIME／Acta Metallurgica 等）。本轮**只做了 Part 1**，
**Part 2 未做 —— 不是「查过没有」，是没查**。
