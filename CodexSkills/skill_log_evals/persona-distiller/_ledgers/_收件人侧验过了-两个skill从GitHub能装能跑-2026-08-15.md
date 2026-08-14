# 收件人侧验过了：两个 skill 从 GitHub **能下载、能校验、能跑**

**2026-08-15**｜用户的原话是「确保这两个 skill 是最新能用的状态，别人只用下载安装使用
github 上的 skill」。**推上去 ≠ 别人能用。** 这次真走了一遍收件人的路。

## ① 真 clone

```bash
git clone --depth 1 git@github.com:LinzeColin/AgentDatabase.git
```

    38 秒｜工作树 1.0 GB（.git 228 MB）｜tip 与 origin/main 一致
    persona-distiller        v0.0.0.154｜492 文件
    persona-distiller-group  v0.0.0.13 ｜352 文件

## ② 在 clone 出来的那份里跑它们自带的校验

| 跑什么 | 结果 |
|---|---|
| `persona-distiller-group/scripts/validate_group.py` | `passed=True`｜**products 102**｜categories 12｜**errors 0** |
| `persona-distiller/checksums.sha256` | rc=0｜**490 OK / 0 FAILED** |
| registry 四件判据 `--self-test` | `check_authorship` / `check_translation_witness` / `check_claim_source_independence` / `quality_check` **全 rc=0** |

## ★★ 只有走这一步才暴露的一个错

`_pipeline/` 四件判据里，**我在同一场会话写了两种自测拼法**：

    check_corpus_not_in_git.py          --selftest    ← 我
    check_private_assets_not_public.py  --selftest    ← 我
    check_deferred_list.py              --self-test   ✓
    emit_parallel_witnesses.py          --self-test   ✓

仓里多数决实测：**`"--self-test"` 138 处 / `"--selftest"` 3 处**（那 3 处全是我写的）。
⇒ 按仓里的约定调前两件，**rc=2 unrecognized arguments**。

已加 `--self-test` 别名（`--selftest` 保留，不断已有调用），
正对照：两种拼法输出**完全一致**（23/23、10/10）。
**在我自己的工作树里永远发现不了 —— 我一直按自己写的拼法调。**
[[green-in-the-repo-dead-in-the-package]]

修完推上去，**回到那份 clone 拉最新再验一遍**：四件全 rc=0
（23/23、10/10、5/5、4/4），`validate_group` 与 `checksums` 仍全绿。

## ③ 顺带把本机装的那份也修了（任务 #36，一直卡在「等推送」）

同步前实测**比记录的还差**：

| 位置 | version | 文件 | 产物 |
|---|---|---:|---:|
| `~/.codex/skills/persona-distiller` | v0.0.0.13 | 273 | — |
| `~/.codex/skills/persona-distiller-group` | **根本没有 manifest** | 327 | **97** |
| `~/.claude/skills/persona-distiller-group` | **根本没有 manifest** | 328 | **97** |

**没有 manifest ＝ 版本绑定那道硬门无从生效**，而且少 5 个人。
已全部同步到 GitHub main 那版并**从装好的位置**复验：
三处 `validate_group` 全 `passed=True / 102 产物 / errors 0`、
`checksums` 490 OK / 0 FAILED、四件 registry 判据 `--self-test` 全 rc=0、
`SKILL.md` 与 `manifest.json` 与仓里 **sha256 逐字节一致**。

## ★ 我在这一步造了一个问题，当场修了

备份照本机既有的 `.backup-<时间戳>` 约定建**在 `~/.claude/skills/` 里面** ——
下一条系统提示就把 `persona-distiller-group.backup-…` 列成了一个**可调用的 skill**，
名字与描述和真的那个几乎一样。

skills 目录是**按目录枚举**的，它不认「这是备份」。已全部挪到 `~/.codex/backups/`。
★ 顺带查出同型的历史遗留：`~/.codex/skills/persona-distiller.backup-20260728T215747Z`
（**v0.0.0.6**）也一直躺在那里 —— 一个差 148 个版本的 skill 一直可被按名字调起来。已一并挪走。

复核：`~/.codex/skills/` 与 `~/.claude/skills/` 下只剩真 skill；
备份区 2.2 MB + 31 MB，可取回。

## 一个没修的（记下来）

`persona-distiller/checksums.sha256` **490 行，实际 492 个文件**，未覆盖两个：
`checksums.sha256` 自己（正常）与 **`registry.yaml`**（真缺口）。
本轮没改 —— 改它要动生成校验和的那件工具，且要先确认它不是有意排除。

★ 顺带：我第一版统计说「漏 3 个、还有 1 个清单有而文件不在」是**错的**，
真因是我用 `lstrip("./")` —— 那是**按字符集**剥，把 `./.gitignore` 剥成了 `gitignore`。
改成只剥一次前缀之后，漏 2、多 0。
