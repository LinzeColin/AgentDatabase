# 01 · 著述路：一本 75 页的小册子，和它后来长出的名字

## ★ 计数口径先摆出来

53 条源里，**同一著作的不同版次共 11 条**（《Inquiry》4 版、《Further Observations》3 版、
《Instructions》3 版、《The Origin》3 版、《On the Varieties》2 版、Moseley《An Oliver》3 版）。

裁定写在 `meta.json:counting_convention`：**版次算源**（各有自己的扉页、印工、译者，
版次差异本身就是证据——见下一节），**但任何断言都不得建立在「本语料含 N 个版次」之上**。
那是账本事实，按 `check_fact_density` 不计入密度。**Galen #101 就是在这里翻的车。**

## ★★ 版次差异本身是证据：一个名字是什么时候出现的

1798 年初版 `src-f38076294dd1` 全文 **11,828 词**，正文出现 12 个罗马数字病例编号。
第 XVII 例——**全书最要紧的那一例**——原文只写：

> 「I selected a healthy boy, about eight years old, for the purpose of inoculation for the Cow Pox.
> The matter was taken from a sore on the hand of a dairymaid」

**这个男孩在 1798 年初版里没有名字。** 实测：`Phipps` 在 `src-f38076294dd1` 里出现 **0 次**。
而在 1800 年三版 `src-ec9e81d982c3` 与 `src-ceaa28b8107c` 里各出现 **3 次**。

**那头牛更彻底**：`Blossom` 在**三个版次里一处都没有**（`src-f38076294dd1`／
`src-ec9e81d982c3`／`src-ceaa28b8107c` 实测各 0 次）。它是后来的传说，不是他写的。

挤奶女工 Sarah Nelmes **确实在初版里**（2 处，且配有图版：
「From the fore on the hand of Sarah Nelmes — See the preceding cafe and the plate」）。

> **他给了那个女人名字，没给那个男孩名字。** 这个差别在初版里是实打实的，
> 而流行叙述把两个名字一起说。**要引这一条，必须说清是哪一版。**

## 著作序列（全部实取）

| 年 | 著作 | src |
|---|---|---|
| 1788 | *Observations on the Natural History of the Cuckoo*，**写给 John Hunter 的一封信**，Phil. Trans. 78:219–237 | `src-007c902b8121` |
| 1798 | *An Inquiry into the Causes and Effects of the Variolae Vaccinae* 初版，自费出版 | `src-f38076294dd1` |
| 1799 | *Further Observations on the Variolae Vaccinae* | `src-fd932add45c4`／`src-bfc97ebedb4d`／`src-df451f5d9d62` |
| 1799 | *Disquisitio de Caussis et Effectibus Variolarum Vaccinarum*（**拉丁译本，字句归译者**） | `src-ebe2f92f46c8`／`src-defc5c91fa33` |
| 1800 | *A Comparative Statement of Facts and Observations* | `src-6d5211d60581` |
| 1800 | *Inquiry* 三版（**名字在这一版出现**） | `src-ec9e81d982c3`／`src-ceaa28b8107c`／`src-38f9944054df` |
| 1801 | *Instructions for Vaccine Inoculation* | `src-2e162bb3987a`／`src-311bb4ef9241`／`src-d67ac65f5ed8` |
| 1801 | *The Origin of the Vaccine Inoculation* | `src-92a5ced52a9a`／`src-f0771e10b4cc`／`src-b561d1e6ceca` |
| 1803 | *Indagação sobre as Causas...*（**葡萄牙译本，字句归译者**） | `src-b85bf45c5074` |
| 1806 | *On the Varieties and Modifications of the Vaccine Pustule* | `src-1a195ca85deb` |
| 1809 | *Facts, for the Most Part Unobserved, or Not Duly Noticed* | `src-513baf9f005d` |
| 1822 | *A Letter to Charles Henry Parry, M.D.* | `src-c90a0c4ad3b1`／`src-1e87fd7e5b7f`／`src-45fd7502fdd8` |
| 1824 | *A Letter to Dr. Waterhouse* | `src-e402301b1a2b` |
| 1824 | *Some Observations on the Migration of Birds* | `src-3686fbb6347e` |

## OCR 口径

18 世纪长 s 被 OCR 成 `f`：`bufinefs`=business、`difeafe`=disease、`felefted`=selected。
**逐字引用时须还原，且必须标明是还原过的**——见 `check_quote_layer.py`。
**他写的是英文，所以不存在译文层问题**（拉丁与葡萄牙译本除外，那两份字句归译者）。
