# 本轮实测的可重跑命令（证据留在仓里，不留在终端里）

本项目记档：**证据只存在会话目录 = 会消失**（Galen/Harvey 两人的语料就是这么丢的，git 里 `raw/` 各 0 份）。
所以把产 03/04/05 与自检那五个数的脚本、以及抓取当时的网络状态快照一并留在这里。

| 文件 | 作用 | 重跑 |
|---|---|---|
| `ia_meta.py` → `ia_meta.json` | 串行拉 13 个 IA 条目的 metadata（含 `date`/`description`/txt 文件清单） | `python3 ia_meta.py ia_meta.json` |
| `fetch.py` → `fetch_ledger.json` | 串行下载 12 件纯文本到 `raw/src-<12hex>/`，写 `SOURCE.json` | `python3 fetch.py` |
| `catalog.py` → `catalog.json` | K10plus SRU 逐 PPN 核出版年/版次（**与题名页年对照**用） | `python3 catalog.py catalog.json` |
| `measure2.py` → `measure2.json` | 讹形比（指令四对 + 实测形族 + 长 s + h→b + 变音符）、第一人称密度 | `python3 measure2.py` |
| `namesake.py` | 产 `kelsen_namesake_candidates.json`，含自测与**变异测试** | `python3 namesake.py` |
| `emit.py` | 由 `measure2.json` 等**现算生成** 03/04/05 三份散文产物 | `python3 emit.py` |
| `final_check.py` | 交卷前自检：**打开落盘产物本身**重算那五项 | `python3 final_check.py`（退出码 0 = 全过） |

约束：并发恒为 1、无 API 花费、不碰付费墙、不绕访问控制。
脚本里的绝对路径是本机的；换机重跑改顶部两个常量即可。

★ `emit.py` 的存在是有意的：**03/04/05 的正文数字一律由它从 `measure2.json` 现算填入，不是手写**
（记档教训：判据盯 JSON，漏了用户看的散文——交付包首屏那张表四个数字全错）。
