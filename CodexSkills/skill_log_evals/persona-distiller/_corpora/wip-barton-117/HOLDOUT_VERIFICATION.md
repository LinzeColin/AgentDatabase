# #117 Clara Barton —— holdout 的两次选法与那一条 ⚠ 的逐条核对

日期：2026-08-04

---

## 一、第一次选法是错的，而且是明知故犯的那种错

我知道 Nightingale #112 栽过什么：**同一本书的不同版次被拆到 train/holdout 两侧**，
`check_holdout_overlap` 实测覆盖 53.1%。所以我特意**按篇名整组留出**。

**然后踩了同一个坑。**

| | 篇名 | 去处 |
|---|---|---|
| 留出 | `A Story of the Red Cross: Glimpses of Field Work` | holdout |
| 留在 train | `A Story of the Red Cross`（**8 份扫描**） | train |

**是同一本书的两种著录题名。** 实跑当场报：

```
✗ src-eb048aa49caa  story-rc-1904.txt
      与 src-de97638e2474 覆盖 89.4%
硬失败 6 / 待人工核 0
```

**「按篇名分组」不等于「按著作分组」——著录题名会变，书不会变。**

## 二、改成逐条列短名，并且**选没有近似兄弟的单副本**

```python
HOLDOUT_IDS = {
    "diary-1864-jan-dec",
    "diary-1867-jan-dec",
    "diary-1871-feb-dec",
    "diary-1897-may-17-sept-5",
}
```

四册横跨 1864–1897，语料里没有它们的第二份扫描，也没有同书异名的兄弟。

复跑：**硬失败 0 / 待人工核 1**。

## ★ 三、那一条 ⚠ 逐条核过了，可接受

```
⚠ src-a4588f50bb49  diary-1897-may-17-sept-5.txt
      与 src-2ed812ef911a 覆盖 17.1%
```

两者是：

| | 内容 | 分档 |
|---|---|---|
| `src-a4588f50bb49` | **她本人**的日记，1897 May 17 – Sept 5 | P1 / holdout |
| `src-2ed812ef911a` | **随行人员**的日记（Diarists other than Barton; Staff diaries），1896 Jul 17 – 1897 Jun 23 | S1 / train |

**日期区间确实相交**（1897 May 17 – Jun 23），两人在同一次亚美尼亚救援行程中。

判据自己的口径是「**同场活动的不同报道可接受，转载不可**」。逐字核：

```
两文各自 ≥40 字的句段：933 / 2303
**逐字相同的句段：8**
   · It is decided that we dine at the hospital
   · had been waiting since 6 1/2 for our belated train
   · the privilege of purchasing more if desired at
```

**8 / 933 ＝ 0.9%。** 而那 17.1% 的真正来源是**普通日记词汇**：

    with, that, will, have, from, came, they, house, this,
    would, home, them, very, little, well, went, work, been

**结论：不是转载，是两个人在同一趟行程里各记各的。可接受。**

## ★★ 四、这条 ⚠ 顺带暴露判据的一个性质

**重合率会被虚词抬高。** 同体裁、同年代、同一批人的文本
（两本日记、两份战地报告），光靠常用词就能到 17%。

所以在**日记型语料**上，⚠ 这一档会经常响。
**它仍然该响**——但读它的人必须做本文这一步（数逐字相同的句段），
**不能看见百分比就下结论**。

## 五、留下的口径

1. **holdout 逐条列短名，不按篇名分组。** 著录题名会变。
2. **选没有任何近似兄弟的单副本。**
3. **选完必须实跑 `check_holdout_overlap` 验一遍，不许凭设计自信**——
   本次第一版就是"设计得很仔细"然后硬失败 6 条。
4. **⚠ 一律逐条核**：数「逐字相同的句段」，不看百分比。
