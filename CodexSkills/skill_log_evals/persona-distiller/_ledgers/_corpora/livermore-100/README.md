# 这个目录**不放 1940 年那本书的正文**

2026-08-17 从这里移出了 5 个文件（约 375 KB），它们是
《How to Trade in Stocks》(1940, Duell, Sloan & Pearce) 的**全文**
（`_01` / `_body_livermore` / `_TRAIN` 三份带版权页逐字：
`COPYRIGHT, 1[9]40, BY JESSE L. LIVERMORE / All rights reserved`；
另两份是第 IV 章与 Dies 写的序言）。

## 为什么不能放

`_corpora/wip-livermore-100/README.md` 自己写着：

> ## 二、★ 1940 年那本书**没有**放进来，必须自己重抓
> **原因是版权状态存疑，不宜随仓库分发**：该副本属 `opensource` 集合、
> 上传者标了 CC public-domain mark，但来源署 "Anna's Archive"，
> **1940 年注册件的美国续期状态未能独立核实**（Stanford 续期库被 Cloudflare 挡住）。

**规则早就写对了，而文件在仓里。** 它们是 2026-08-14 的 `bfe16379a`
（一个 **15,070 个文件**的批量提交）连带卷进来的，此后一直在
**PUBLIC 仓 `LinzeColin/AgentDatabase`** 的 `origin/main` 上。

## 要用它怎么办

按上面那份 README 的说明**自己重抓**，放在**仓外**（本机 `_scratch/` 或
`~/Downloads/蒸馏/`），不要 `git add`。

## ★ 还没解决的一半

移出 HEAD **只停止了往后的分发**；这 5 个文件**仍在公开的 git 历史里**
（`bfe16379a` 及其后每个提交）。要真正从公开记录里去掉，
需要改写历史或联系 GitHub 支持 —— **不可逆、且会影响所有已 clone 的人，
只能由 Owner 定**。
