# Timeline, stages, and drift

**本路 51 份，是六路里最厚的一路，几乎全部是她的日记（LOC mss11973 全宗）。
但「厚」在这里有个陷阱：日记不是叙事，是台账。**

## Scope and assigned sources

train 分割 51 份，主体为逐年日记卷，跨度 1849–1910。核心几份：
src-18d580f61c05（1862 Jan–Dec／1865）、src-3ad3fc0fc419（1849 Jan 23–Nov 5，含诗）、
src-e62c4b1ab9b6（1863 Jan–Feb）、src-7b627b4eec99（1865 Jan–Dec）。
另有 4 册作 **holdout**（1864／1867／1871／1897），**本路不得读其正文**。

## ★★ Source-linked observations 一：日记的载体本身就是证据

src-18d580f61c05（`diary-1862-jan-dec-1865`）开卷即印着（逐字照录）：

```
Pocket Diary
for
1862.
CONTAINING
An Almanac,
A BLANK SPACE FOR EVERY DAY,
CASH ACCOUNT, &c
SALEM, MASS.
D. B. Brooks & Bro.,
Blank Book Manufacturers and Publishers.
```

**这是一本商用袖珍日记本**——带历书、每日空格、**现金账**、邮资表。
**不是日志本，是随身事务本。**

## ★★ Source-linked observations 二：她把空白页当成了人名册

同一卷（src-18d580f61c05）正文之前，是一串人名加编号（照录）：

```
Wm A Daniels 2-
Sec W Jenner 2 crop
Ezra S Whittameer 20
E F Field sargt 21 E
W Nait 13
James Ryan 28
David Welch 12
Louis Askil 21 - H
Edward Fletcher 13
J L Thompson 19 Sargt 10
```

两处 `sargt`／`Sargt`（军衔 sergeant）与「数字＋字母」（团／连编号形态）
表明**这是一份军人名录**。

**这一条与 05 决策路直接接得上**：1865–66 年她在安德森维尔做的是
`identifying and marking the graves of the dead`；
**而 1862 年她已经在袖珍日记本的空白页上一个一个记名字了。**
**「把人从无名里捞出来」不是战后才有的任务，是她战时就在做的事。**

## Contradictions and alternative explanations

- 名录也可能是**代人转记**或**收发物资的领取名单**，不必然是她自己的辨认工作。
  **本条因此列为观察，不列为断言**——要坐实，须在同卷正文里找到她说明用途的句子，
  **下一轮逐段核**。
- 日记是**事务本**，因此**大量条目是账目与行程，不是心迹**。
  **不许把「日记里没写感想」读成「她不表达情感」**——载体本来就不为此设计。

## Unknowns and source gaps

- **1849–1861 与 1866–1910 的年份覆盖不均**，尚未逐卷统计有日记的年份与缺口年份。
  **在统计完成之前，不许说「某年她在做什么」这类需要连续时间轴的话。**
- 多份 `Speeches and Writings` 标 `undated`（见 03 表达路），**不许给它们编年份**。
- **holdout 四册（1864／1867／1871／1897）本路不得读**，
  因此这四年的时间线以其他源为准；若其他源无覆盖，**照实写「本轮不判」**。
- 她 1912-04-12 卒；`The Red Cross in Peace and War` 1912 印次已标 `POSTHUMOUS` 降 P2，
  **不作时间锚点**。

## Proposed Holdout cases

已留出：四册单副本日记（1864／1867／1871／1897），按**短名逐条列出**而非按篇名分组。
**第一次按篇名分组时栽过**——`A Story of the Red Cross: Glimpses of Field Work`
与 `A Story of the Red Cross` 是同一本书的两种著录题名，
`check_holdout_overlap` 报硬失败 6 条、覆盖 89.4%。改法后硬失败 0。

## Handoff to adjudication

1. **先做年份覆盖统计**，再写任何依赖连续时间轴的断言。
2. **「1862 年就在记名字」这一条是本人物最有价值的时间线观察**，
   但须先排除「代人转记／领取名单」两种解释才能升为断言。
3. 日记是事务本这一条**必须写进边界文档**——
   防止把「日记里没有的东西」误读成「她生活里没有的东西」。
