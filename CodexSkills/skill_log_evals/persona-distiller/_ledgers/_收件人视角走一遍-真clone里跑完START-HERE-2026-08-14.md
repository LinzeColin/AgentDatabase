# 从交付包真 clone 一份，把 START-HERE 教的命令全跑一遍

**2026-08-14**｜做这件事的理由：本项目此前栽过两次 ——
[[green-in-the-repo-dead-in-the-package]]（仓里 1402 条判据全绿，装进包里 import 就死）与
[[verifying-single-commands-is-not-verifying-the-chain]]（三条命令各自都绿，
整条「从零复现」走完 89/91 红）。**验单步 ≠ 验链条**，所以这次验的是**收件人手上那个东西**。

## 怎么做的

```bash
git clone <_protected/agentdb-handover-20260814/agentdb-persona-distiller-full.bundle> <临时目录>
cd <临时目录>          # ★ 之后所有命令都在 clone 里跑，不在工作树里
```

clone rc=0，`git rev-parse HEAD` = **`e71c695a`**，与工作树 tip 逐字一致。

## 结果：**收件人会跑的每一条都跑得通，且输出与文里写的对得上**

| 命令（照 START-HERE 抄） | rc | 关键输出 |
|---|---:|---|
| `python3 --version && git --version` | 0 | Python **3.9.6**／git **2.39.5** —— 第三节说「只需要 python3(3.9+) 和 git」 |
| `check_start_here_numbers.py` | **0** | 六格表与实测一致 |
| `check_lessons_library.py` | **0** | **✓ 三者一致** |
| `check_scoring_ready.py` | **1** | 「分母：扫到工作区 **54**」——★ **这个红就是停点本身**，文里写明了 |
| `emit_ids_rebuild.py --scan … --check` | **0** | 「一致 **18** 个｜有问题 0 个｜没有 manifest **36** 个」 |
| `check_measurements_fresh.py` | **0** | 分道/分档产物与重跑逐字一致 |
| `fetch_kramerius.py --self-test` | **0** | 15/15 |
| `slice_letter_volume.py --self-test` | **0** | 35/35 |
| `assign_lanes.py --selftest` | **0** | 60/60 |
| 第三节那段「数非标准库 import」 | 0 | **682 个 `.py`｜非标准库 3 个**（msvcrt 50／registry_core 3／pypdf 1） |
| `head -1 文档/踩坑库/README.md` | 0 | `# 踩坑库 —— 193 条实测教训` |

★★ **两个当天刚写进文档的数，在 clone 里逐字复现**：
`emit_ids_rebuild` 的 **18／36**（我当天把文里的 19／26 改成了这个）、
`.py` 的 **682**（改自 669）。⇒ 不是「我在工作树里量的那一次碰巧对」。

## 这一趟**没有**验到的（说清楚，别读成「全验过了」）

- **只跑了 START-HERE 点名的那些命令**，没有跑 HANDOFF §3 那张表
  （那张表有 `check_handoff_commands.py` 单独管着，接在打包自验证里）；
- **没有跑阶段 5 判分**——那要两个互相独立的空白会话，本会话做不了；
- **没有验语料**：新工作区的 `raw/*.txt` 按设计不在包里（靠 `_ids-rebuild.txt` ＋ sha256 重建），
  这一趟没有真去抓一遍源来复原；
- 跑的机器就是打包的这台。**换一台机器仍然是没验过的**
  ——[[all-my-acceptance-ran-on-the-machine-being-tested]] 那次就是这么栽的。

## 复现

```bash
git clone /Users/linzezhang/Documents/Codex/GithubProject/_protected/agentdb-handover-20260814/agentdb-persona-distiller-full.bundle /tmp/recipient
cd /tmp/recipient && head -8 START-HERE.md          # 一句话 prompt 在第 3 行
```
