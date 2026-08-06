# Walter Rosenhain (1875–1934) —— 可得性探测 #138（**本族第一个看起来做得成的**）

- 探测日期：**2026-08-06**
- 卒年出处：Wikidata **Q10393106**（P569 1875-08-24 / P570 1934-03-17），`confidence: high`
- 范围：只探测取证。**未建工作区、未组装语料。** 花费零，只用公开通道。

---

## 〇、一句话：**权利、可得性、声口三关，本轮都是绿的**

前三位各倒在不同的地方——Coffin 倒在声口、Bain 倒在声口、Mehl 卡在通道。
**Rosenhain 三关都过，而且过得不勉强。**

## 一、权利：**整段职业生涯在 PD 分界之前**

他 **1906–1931** 年任 National Physical Laboratory 冶金与冶金化学部**首任**主管
——**任期结束正好压在 1931 年这条线上**。

Wikisource 作者页的 PD 声明逐字：

> `Some or all works by this author are in the public domain in the United States
> because they were published before January 1, 1931.`
> `This author died in 1934, so works by this author are in the public domain in
> countries and areas where the copyright term is the author's life plus 91 years or less.`
> —— `en.wikisource.org/wiki/Author:Walter_Rosenhain`

★ 与前两位对比，这一点是决定性的：

| | 生涯 | pre-1931 产出 | 要不要查续期 |
|---|---|---|---|
| Bain | 1920s–1960s | 只 6 件 | 要（主体在 1931 后） |
| Mehl | 1920s–1960s | 只 3 件 | 要（主体在 1931 后） |
| **Rosenhain** | **1900s–1931** | **几乎全部** | **基本不用** |

★★ 但 `Some or all` 是 Wikisource 的标准措辞，**不是逐件断言**。
1931–1934 年间若有出版物仍要单独查——**本轮没查**。

## 二、可得性：**独著书三版、玻璃那本两版，全部开放**

archive.org 实测：

| identifier | 年 | 状态 | 书名 |
|---|---|---|---|
| `cu31924004614859` | 1914 | **开放** | Metallurgy; an introduction to the study of physical metallurgy |
| `cu31924004699082` | 1915 | 开放 | 同上 |
| `cu31924004623058` | 1922 | 开放 | 同上 |
| `glassmanufacture00roserich` | 1908 | 开放 | Glass manufacture |
| `glassmanufactur00rosegoog` | 1919 | 开放 | 同上 |

**本轮已取到 1914 那版全文（900,197 B）。**

## 三、★★★ 声口：**本族第一个四类立场句全部出现的人**

`cu31924004614859` 掐掉馆藏扉页与卷末索引后 864,673 字符：

| 人物／件 | 第一人称/万字 | 立场句/万字 | 四类分布 |
|---|---|---|---|
| Coffin 全语料 | 1.45 | **0.00** | 无 |
| Bain 1928 独著 | 0.91 | 0.23 | 单类 |
| Mehl 1936 讲演 | 2.44 | 0.43 | 三类 |
| **Rosenhain 1914** | **4.01** | **0.32** | **四类全有**：指令读者 11／下评价 2／更正取舍 7／有保留的判断 8 |
| Nasmyth 自传 | 21.22 | 0.07 | 叙事体 |

原样（逐字）：

> `Perhaps this purely scientific aspect of our subject may with advantage be
> dealt with first.`
> `Turning to the more immediately practical aspects of our subject, the importance
> of Physical Metallurgy scarcely requires either explanation or emphasis.`
> `When those experiments were made, however, the technique of radiology was yet in
> its infancy, and it seems probable that with modern appliances it might…`
> —— 均出自 `cu31924004614859`

**这是一个有主张、会引导读者、会下判断的教科书作者**，
不是 Bain/Coffin 那种「只有装置描述与套语」的形态。

## 四、已经看得见的同名（**不是随便的同姓者**）

archive.org 按 `creator:("Rosenhain")` 检索，59 个命中里混着：

- `imslp-historiettes-op97-rosenhain-jacob`（1887）
- `fantasiaappassio00rose`（1890）`Fantasia appassionata : grand duo`
- `imslp-de-concours-op39-rosenhain-jacob`（1847）

**是 Jacob Rosenhain，十九世纪作曲家。** 与 Mehl 那次的 B. Max Mehl 同形：
**同姓、同库、检索必撞。** 护栏文件要把他写进去。

## 五、下一轮（按顺序）

1. **同名护栏**：把 Jacob Rosenhain 写成候选并跑 `namesake_gate`；
2. 1931–1934 年间有无出版物，单独查（Wikisource 那句是 `Some or all`）；
3. 逐份核 1908/1915/1919/1922 各版的可得性与差异（**同一本书的多版不是多份来源**——
   与「两个 source_id 不等于两处证据」同一条）；
4. 走 `check_probe_precondition` 与 `init_target`，正式开工。

## 六、本轮的诚实边界

- **只量了 1914 那一版**，其余四份只确认了「开放」，没打开；
- 「四类立场句全有」是**一份样本**上的，不是他全部作品上的；
- 1931–1934 的出版物没查；
- ★ 这些数与前三位可比，**因为用的是同一把尺、同一版判据**（含语种守卫与套语剥离）。
