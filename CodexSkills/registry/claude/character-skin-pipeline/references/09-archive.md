# 归档：NAS 与 git

## NAS 结构（成品与素材并列）

```
smb://192.168.0.1/share/03_资料库/MetaData/HarnessUI/
  <游戏中文>/<角色>/refs/          # 锚图与出处（source.json）
  <游戏中文>/<角色>/skins/<变体>/  # light.png / dark.png / meta.json
                                    # 以及 *.rejected-N.png（被替换的旧版）
```

成品放在**它所依据的素材旁边**，不另建一棵树——
一个角色目录就能回答「我们有什么、做出了什么」。

`meta.json` 记：task / game / character / variant / model / size /
pack_version / acceptance(含每张的验收指标) / generated 日期。

## SMB 的两个坑

**1. 连续写会把它打崩。** 612 个 6-8MB 文件背对背拷，实测 **240 个报
`Input/output error`**，而同一个文件一分钟后手动拷只要 0.9 秒——是被打崩不是坏了。
做法：**四次重试 + 指数退避 + 每 8 个文件歇 0.4 秒**。加了之后失败 0。

**2. 覆盖同名文件的 rename 会失败。** `mv a.png.part a.png` 在目标已存在时报 I/O 错误，
而且会**先把目标删掉**——中途失败就是两边都没有。
做法：先确认目标名空出来再 rename，失败后立刻查目录状态（数据通常还在 `.part` 里）。

**3. 别在 SMB 上跑 `du -sh` / 全量 `find`。** 会超时。要数数就按子目录分别数。

## git

**二进制不进 git。** 母版 4.8GB、显示图 100MB+ 都归档在 NAS。
仓里只放目录与治理：

```
HarnessUI/
  README.md  ROADMAP.md  DEPLOY.md
  research/     花名册、中文名、素材源调研
  delivery/     manifest-<version>.json、acceptance-<version>.json、catalog.json
  tools/        全部脚本
  dsh-plugin/  kimi-shell/  menubar-app/   宿主侧源码
  .gitignore    output/ skin-assets/ *.png *.webp *.zip .oaikey
```

`acceptance-<version>.json` 是逐张的验收记录（status/attempts/metrics/fails），
**不要把台账原样提交**——它含 key 路径和几 MB 的 prompt。

### sparse-checkout 会静默拦下新目录

`git add` 报 "paths … outside of your sparse-checkout definition" 时，
文件**没有进暂存区**，而 `git push` 仍会成功（推的是空提交）。
先 `git sparse-checkout add <目录>` 再 add。

### 推送闸门

仓库可能有 pre-push 钩子（体积闸、全仓体检）。被无关的检查拦下时，
用它文档里给的跳过方式，**并在回复里明说跳过了什么、为什么无关**——
先确认改动范围（`git diff --name-only origin/main..HEAD`）。

## 绝对不要

**把唯一副本放在会话临时目录。** 母版一度只存在 `/private/tmp/.../scratchpad`，
而运行时目录的三个软链正指着那儿。/tmp 一清，4.8GB 和验收页全部大图一起没。
运行时素材放 `~/.harness-ui/`，母版另有 NAS 备份。
